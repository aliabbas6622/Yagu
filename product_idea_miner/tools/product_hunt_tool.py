import logging
import urllib.parse
import urllib.request
from datetime import datetime
from typing import List, Any

from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.tools.crawlee_engine import run_crawlee_async, scrape_with_playwright

logger = logging.getLogger(__name__)

def scrape_product_hunt(limit: int = 10) -> List[RawPost]:
    """
    Scrapes the front page of Product Hunt for today's launches using Crawlee's PlaywrightCrawler.
    Falls back to the Product Hunt Atom RSS feed if Playwright is blocked or times out.
    """
    raw_posts: List[RawPost] = []
    start_urls = ["https://www.producthunt.com/"]

    async def request_handler(context: Any) -> None:
        url = context.request.url
        logger.info("Processing Product Hunt frontpage: %s", url)
        page = context.page

        # Wait for the post items to render on Product Hunt
        try:
            await page.wait_for_selector('[data-test^="post-item-"], [data-testid="post-item"], .styles_item__', timeout=8000)
        except Exception:
            logger.warning("Timeout waiting for post items on Product Hunt. The page format may have changed or is blocked.")
            return

        # Query all product launch elements
        items = await page.query_selector_all('[data-test^="post-item-"], [data-testid="post-item"], .styles_item__')
        count = 0
        for item in items:
            if count >= limit:
                break

            # Extract Name
            name_el = await item.query_selector('[data-test="post-name"], h3, .post-name')
            name = await name_el.inner_text() if name_el else ""

            # Extract Tagline
            tagline_el = await item.query_selector('[data-test="post-tagline"], .post-tagline, p')
            tagline = await tagline_el.inner_text() if tagline_el else ""

            # Extract link
            link_el = await item.query_selector('a[href^="/posts/"]')
            href = await link_el.get_attribute("href") if link_el else ""
            if href and not href.startswith("http"):
                href = urllib.parse.urljoin("https://www.producthunt.com", href)

            # Extract Upvotes
            votes = 0
            vote_el = await item.query_selector('[data-test="vote-button"] [data-test="vote-count"], .vote-count')
            if vote_el:
                try:
                    votes = int((await vote_el.inner_text()).strip().replace(",", ""))
                except Exception:
                    pass

            body = f"Product Hunt Launch:\nTagline: {tagline}\nUpvotes: {votes}\nThis is a recently launched product. Good source to evaluate competitive solutions."

            if name and href:
                raw_posts.append(
                    RawPost(
                        source=Source.PRODUCT_HUNT,
                        url=href,
                        title=name.strip(),
                        body=body,
                        upvotes=votes,
                        num_comments=0,
                        created_at=datetime.now()
                    )
                )
                count += 1

    try:
        logger.info("Starting Crawlee PlaywrightCrawler for Product Hunt launches...")
        run_crawlee_async(scrape_with_playwright, start_urls, request_handler)
    except Exception as e:
        logger.warning("Playwright crawler failed: %s. Will fallback to RSS feed...", e)

    # Fallback if Playwright was blocked or found 0 products
    if not raw_posts:
        logger.info("No products found via Playwright. Falling back to Product Hunt Atom RSS feed...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            req = urllib.request.Request("https://www.producthunt.com/feed", headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.read(), "xml")
                entries = soup.find_all("entry")
                count = 0
                for entry in entries:
                    if count >= limit:
                        break
                    
                    name = entry.title.text if entry.title else ""
                    href = entry.link.get("href") if entry.link else ""
                    
                    # Extract description from content html
                    content_text = ""
                    if entry.content:
                        content_soup = BeautifulSoup(entry.content.text, "html.parser")
                        content_text = content_soup.get_text(strip=True)
                    
                    body = f"Product Hunt Launch:\nTagline: {content_text}\nThis is a recently launched product. Good source to evaluate competitive solutions."
                    
                    if name and href:
                        raw_posts.append(
                            RawPost(
                                source=Source.PRODUCT_HUNT,
                                url=href,
                                title=name.strip(),
                                body=body,
                                upvotes=0,
                                num_comments=0,
                                created_at=datetime.now()
                            )
                        )
                        count += 1
            logger.info("Successfully fetched %s products from RSS feed.", len(raw_posts))
        except Exception as rss_err:
            logger.error("Failed to parse Product Hunt RSS feed: %s", rss_err)

    logger.info("Product Hunt scraping complete. Found %s products.", len(raw_posts))
    return raw_posts

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    posts = scrape_product_hunt(5)
    for post in posts:
        title_safe = post.title.encode('ascii', 'ignore').decode('ascii')
        body_safe = post.body.encode('ascii', 'ignore').decode('ascii')
        print(f"URL: {post.url}\nTitle: {title_safe}\nBody: {body_safe}\n")
