import asyncio
import logging
from typing import List, Callable, Any

logger = logging.getLogger(__name__)

def run_crawlee_async(async_func, *args, **kwargs):
    """
    Helper to run an async Crawlee crawler inside a synchronous context.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # If there is already a running loop (e.g. in FastAPI or Uvicorn),
        # we run it as a task or schedule it.
        # But for pipeline CLI it's usually synchronous.
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(async_func(*args, **kwargs))
    else:
        return loop.run_until_complete(async_func(*args, **kwargs))

async def scrape_with_playwright(urls: List[str], handler: Callable[[Any], None]) -> None:
    """
    Scrapes URLs using Crawlee's PlaywrightCrawler.
    """
    try:
        from crawlee.crawlers import PlaywrightCrawler
    except ImportError:
        logger.error("Crawlee is not installed. Run 'pip install crawlee[playwright]' first.")
        return

    crawler = PlaywrightCrawler(
        max_requests_per_crawl=20,
        headless=True,
    )

    @crawler.router.default_handler
    async def default_handler(context: Any) -> None:
        try:
            await handler(context)
        except Exception:
            logger.exception("Error in Playwright request handler for %s", context.request.url)

    await crawler.run(urls)

async def scrape_with_cheerio(urls: List[str], handler: Callable[[Any], None]) -> None:
    """
    Scrapes URLs using Crawlee's BeautifulSoupCrawler (similar to cheerio).
    """
    try:
        from crawlee.crawlers import BeautifulSoupCrawler
    except ImportError:
        logger.error("Crawlee is not installed. Run 'pip install crawlee' first.")
        return

    crawler = BeautifulSoupCrawler(
        max_requests_per_crawl=50,
    )

    @crawler.router.default_handler
    async def default_handler(context: Any) -> None:
        try:
            await handler(context)
        except Exception:
            logger.exception("Error in BeautifulSoup request handler for %s", context.request.url)

    await crawler.run(urls)
