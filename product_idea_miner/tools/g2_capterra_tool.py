import logging
import urllib.parse
from datetime import datetime
from typing import List, Any

from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.tools.crawlee_engine import run_crawlee_async, scrape_with_playwright

logger = logging.getLogger(__name__)

# Map of common product names to Capterra IDs to construct correct URLs
CAPTERRA_PRODUCT_MAP = {
    "notion": "https://www.capterra.com/p/162817/Notion/reviews/",
    "slack": "https://www.capterra.com/p/132924/Slack/reviews/",
    "hubspot": "https://www.capterra.com/p/124794/HubSpot-Sales/reviews/"
}

def scrape_g2_capterra(products: List[str], limit_per_product: int = 5) -> List[RawPost]:
    """
    Scrapes software review platforms (mainly Capterra and G2) for common products.
    Focuses on extracting 'Cons' or complaints.
    """
    if not products:
        return []

    raw_posts: List[RawPost] = []
    start_urls = []

    for prod in products:
        prod_lower = prod.lower().strip()
        # Use mapped URL if available, otherwise guess Capterra URL format
        if prod_lower in CAPTERRA_PRODUCT_MAP:
            start_urls.append(CAPTERRA_PRODUCT_MAP[prod_lower])
        else:
            start_urls.append(f"https://www.capterra.com/p/{prod_lower}/reviews/")

    async def request_handler(context: Any) -> None:
        url = context.request.url
        logger.info("Processing Review page: %s", url)
        page = context.page

        # Wait for the review cards to render
        try:
            # Common selectors for Capterra review blocks
            await page.wait_for_selector('.review-card, [data-testid="review-card"], .Card__CardContainer-sc-1nldt6d-0', timeout=8000)
        except Exception:
            logger.warning("Timeout waiting for reviews on %s. Page format may have changed or is blocked.", url)
            return

        review_cards = await page.query_selector_all('.review-card, [data-testid="review-card"], .Card__CardContainer-sc-1nldt6d-0')
        count = 0
        for card in review_cards:
            if count >= limit_per_product:
                break

            # Try to find overall title
            title_el = await card.query_selector('h3, [data-testid="review-title"], .review-card-title')
            title = await title_el.inner_text() if title_el else "Review of product"

            # Check rating if possible
            rating_text = ""
            rating_el = await card.query_selector('[data-testid="review-rating"], .rating-stars')
            if rating_el:
                rating_text = await rating_el.inner_text()

            # Cons section (most important for pain points)
            cons_el = await card.query_selector('.review-cons, [data-testid="cons-text"], .cons')
            cons_text = await cons_el.inner_text() if cons_el else ""

            # Pros section
            pros_el = await card.query_selector('.review-pros, [data-testid="pros-text"], .pros')
            pros_text = await pros_el.inner_text() if pros_el else ""

            # Main comment body
            body_el = await card.query_selector('.review-body, [data-testid="review-comments"], .comment')
            body_text = await body_el.inner_text() if body_el else ""

            # We combine pros/cons/body, placing emphasis on Cons as the "complaints"
            full_body = ""
            if cons_text:
                full_body += f"CONS/PAIN POINTS:\n{cons_text}\n\n"
            if pros_text:
                full_body += f"PROS:\n{pros_text}\n\n"
            if body_text:
                full_body += f"GENERAL FEEDBACK:\n{body_text}"

            full_body = full_body.strip()

            # We save as CAPTERRA or G2 depending on URL
            source = Source.G2 if "g2.com" in url else Source.CAPTERRA

            if full_body:
                raw_posts.append(
                    RawPost(
                        source=source,
                        url=url,
                        title=f"{prod.capitalize()}: {title.strip()}",
                        body=full_body,
                        upvotes=0,
                        num_comments=0,
                        created_at=datetime.now()
                    )
                )
                count += 1

    logger.info("Starting Crawlee PlaywrightCrawler for G2/Capterra reviews...")
    run_crawlee_async(scrape_with_playwright, start_urls, request_handler)
    logger.info("Review platform scraping complete. Found %s reviews.", len(raw_posts))
    return raw_posts

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    posts = scrape_g2_capterra(["notion"])
    for post in posts:
        print(f"URL: {post.url}\nTitle: {post.title}\nBody Snippet: {post.body[:200]}\n")
