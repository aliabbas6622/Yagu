import requests
import logging
from typing import List
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.config.settings import REQUEST_TIMEOUT_SECONDS, RETRY_ATTEMPTS, RETRY_WAIT_SECONDS

logger = logging.getLogger(__name__)

@retry(reraise=True, stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, min=1, max=30))
def _get_json(url: str):
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()

def scrape_hn(limit: int = 50) -> List[RawPost]:
    """
    Scrapes Hacker News for top stories that might contain pain points.
    Focuses on 'Ask HN' and 'Show HN'.
    """
    raw_posts = []
    try:
        # Get top story IDs
        story_ids = _get_json("https://hacker-news.firebaseio.com/v0/topstories.json")[:limit]

        for story_id in story_ids:
            story = _get_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")

            if not story:
                continue

            title = story.get("title", "")
            # Look for Ask HN or Show HN
            if title.startswith("Ask HN:") or title.startswith("Show HN:"):
                raw_post = RawPost(
                    source=Source.HN,
                    url=f"https://news.ycombinator.com/item?id={story_id}",
                    title=title,
                    body=story.get("text", ""),
                    upvotes=story.get("score", 0),
                    num_comments=len(story.get("kids", [])),
                    created_at=datetime.fromtimestamp(story.get("time", 0))
                )
                raw_posts.append(raw_post)
    except Exception:
        logger.exception("Error scraping Hacker News")

    return raw_posts
