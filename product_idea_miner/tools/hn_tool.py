import requests
from typing import List
from datetime import datetime
from product_idea_miner.config.models import RawPost, Source

def scrape_hn(limit: int = 50) -> List[RawPost]:
    """
    Scrapes Hacker News for top stories that might contain pain points.
    Focuses on 'Ask HN' and 'Show HN'.
    """
    raw_posts = []
    try:
        # Get top story IDs
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        response.raise_for_status()
        story_ids = response.json()[:limit]

        for story_id in story_ids:
            story_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
            story_resp.raise_for_status()
            story = story_resp.json()

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
    except Exception as e:
        print(f"Error scraping Hacker News: {e}")

    return raw_posts
