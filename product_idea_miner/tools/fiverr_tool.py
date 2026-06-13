import logging
import urllib.parse
from datetime import datetime
from typing import List, Any

from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.tools.crawlee_engine import run_crawlee_async, scrape_with_playwright

logger = logging.getLogger(__name__)

def scrape_fiverr(queries: List[str], limit_per_query: int = 5) -> List[RawPost]:
    """
    Scrapes Fiverr gig offerings for the given queries using Crawlee's PlaywrightCrawler.
    """
    if not queries:
        return []

    raw_posts: List[RawPost] = []
    start_urls = []
    for query in queries:
        encoded_query = urllib.parse.quote(query)
        start_urls.append(f"https://www.fiverr.com/search/gigs?query={encoded_query}")

    async def request_handler(context: Any) -> None:
        url = context.request.url
        logger.info("Processing Fiverr URL: %s", url)
        page = context.page

        # Wait for the gig cards to load
        try:
            await page.wait_for_selector('[data-testid="gig-card"], .gig-card-layout, .gig-wrapper', timeout=8000)
        except Exception:
            logger.warning("Timeout waiting for gig cards on %s. Fiverr may be blocking or has no results.", url)
            return

        # Query all gig cards
        cards = await page.query_selector_all('[data-testid="gig-card"], .gig-card-layout, .gig-wrapper')
        count = 0
        for card in cards:
            if count >= limit_per_query:
                break

            # Extract Title and URL
            title_el = await card.query_selector('h3 a, .title a, [data-testid="gig-card-title"] a')
            title = await title_el.inner_text() if title_el else ""
            href = await title_el.get_attribute("href") if title_el else ""

            if href and not href.startswith("http"):
                href = urllib.parse.urljoin("https://www.fiverr.com", href)

            # Extract pricing
            price_el = await card.query_selector('.price, [data-testid="price"], .price-wrapper')
            price = await price_el.inner_text() if price_el else ""

            # Extract rating / seller details
            rating_el = await card.query_selector('.rating-wrapper, [data-testid="rating-score"], .rating')
            rating = await rating_el.inner_text() if rating_el else ""

            body = f"Fiverr Gig details:\nPrice: {price.strip()}\nRating/Reviews: {rating.strip()}\nDescription of service offered."

            if title and href:
                raw_posts.append(
                    RawPost(
                        source=Source.FIVERR,
                        url=href,
                        title=title.strip(),
                        body=body,
                        upvotes=0,
                        num_comments=0,
                        created_at=datetime.now()
                    )
                )
                count += 1

    logger.info("Starting Crawlee PlaywrightCrawler for Fiverr gigs...")
    run_crawlee_async(scrape_with_playwright, start_urls, request_handler)
    logger.info("Fiverr scraping complete. Found %s gigs.", len(raw_posts))
    return raw_posts

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    posts = scrape_fiverr(["web scraping"])
    for post in posts:
        print(f"URL: {post.url}\nTitle: {post.title}\nBody: {post.body}\n")
