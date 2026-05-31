import praw
from typing import List
from datetime import datetime
from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.config.settings import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USERNAME,
    REDDIT_PASSWORD,
    REDDIT_USER_AGENT,
    MIN_UPVOTES
)

def scrape_reddit(subreddits: List[str], keywords: List[str], limit_per_search: int = 25) -> List[RawPost]:
    """
    Scrapes Reddit for posts matching keywords in specific subreddits.
    """
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent=REDDIT_USER_AGENT
    )

    raw_posts = []
    seen_urls = set()

    for sub_name in subreddits:
        subreddit = reddit.subreddit(sub_name)
        for keyword in keywords:
            search_results = subreddit.search(keyword, sort="new", time_filter="week", limit=limit_per_search)
            for post in search_results:
                if post.score >= MIN_UPVOTES and post.url not in seen_urls:
                    raw_post = RawPost(
                        source=Source.REDDIT,
                        url=post.url,
                        title=post.title,
                        body=post.selftext,
                        upvotes=post.score,
                        num_comments=post.num_comments,
                        subreddit=sub_name,
                        created_at=datetime.fromtimestamp(post.created_utc)
                    )
                    raw_posts.append(raw_post)
                    seen_urls.add(post.url)

    return raw_posts
