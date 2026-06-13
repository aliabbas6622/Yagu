import logging
import urllib.parse
from datetime import datetime
from typing import List, Any

from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.tools.crawlee_engine import run_crawlee_async, scrape_with_playwright

logger = logging.getLogger(__name__)

def scrape_upwork(queries: List[str], limit_per_query: int = 5) -> List[RawPost]:
    """
    Scrapes Upwork job postings for the given queries using Crawlee's PlaywrightCrawler.
    """
    if not queries:
        return []

    raw_posts: List[RawPost] = []
    # Build search URLs
    start_urls = []
    for query in queries:
        encoded_query = urllib.parse.quote(query)
        start_urls.append(f"https://www.upwork.com/nx/search/jobs/?q={encoded_query}")

    async def request_handler(context: Any) -> None:
        url = context.request.url
        logger.info("Processing Upwork URL: %s", url)
        page = context.page

        # Wait for the job tiles to render (Upwork uses a dynamic SPA)
        try:
            await page.wait_for_selector('[data-test="JobTile"], article.job-tile, section.air3-card, .job-tile', timeout=8000)
        except Exception:
            logger.warning("Timeout waiting for job tiles on %s. Upwork may be blocking or has no results.", url)
            return

        # Query all job tile elements
        tiles = await page.query_selector_all('[data-test="JobTile"], article.job-tile, section.air3-card, .job-tile')
        count = 0
        for tile in tiles:
            if count >= limit_per_query:
                break

            # Extract title
            title_el = await tile.query_selector('h2.job-tile-title a, h3 a, [data-test="job-tile-title"] a')
            title = await title_el.inner_text() if title_el else ""
            href = await title_el.get_attribute("href") if title_el else ""

            if href and not href.startswith("http"):
                href = urllib.parse.urljoin("https://www.upwork.com", href)

            # Extract body/description
            body_el = await tile.query_selector('[data-test="job-description"], .job-description, .description')
            body = await body_el.inner_text() if body_el else ""

            # Extract budget/info if available
            info_el = await tile.query_selector('.job-tile-info, .job-info, [data-test="job-info-paragraph"]')
            info_text = await info_el.inner_text() if info_el else ""

            full_body = f"{body}\n\nJob details: {info_text}".strip()

            if title and href:
                raw_posts.append(
                    RawPost(
                        source=Source.UPWORK,
                        url=href,
                        title=title.strip(),
                        body=full_body.strip(),
                        upvotes=0,
                        num_comments=0,
                        created_at=datetime.now()
                    )
                )
                count += 1

    logger.info("Starting Crawlee PlaywrightCrawler for Upwork jobs...")
    run_crawlee_async(scrape_with_playwright, start_urls, request_handler)
    logger.info("Upwork scraping complete. Found %s jobs.", len(raw_posts))
    return raw_posts

# Simple test function
def test_scrape():
    logging.basicConfig(level=logging.INFO)
    posts = scrape_upwork(["python developer"])
    for post in posts:
        print(f"URL: {post.url}\nTitle: {post.title}\nBody Snippet: {post.body[:150]}\n")

if __name__ == "__main__":
    test_scrape()
