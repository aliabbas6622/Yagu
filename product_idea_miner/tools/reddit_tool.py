import praw
import re
import logging
from typing import List
from datetime import datetime
from urllib.parse import quote_plus
from tenacity import retry, stop_after_attempt, wait_exponential
from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.config.settings import (
    REQUEST_TIMEOUT_SECONDS,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USERNAME,
    REDDIT_PASSWORD,
    REDDIT_USER_AGENT,
    REDDIT_USE_SCRAPLING_FALLBACK,
    RETRY_ATTEMPTS,
    RETRY_WAIT_SECONDS,
    MIN_UPVOTES
)

REDDIT_BASE_URL = "https://old.reddit.com"
logger = logging.getLogger(__name__)

def _has_reddit_api_config() -> bool:
    return all([
        REDDIT_CLIENT_ID,
        REDDIT_CLIENT_SECRET,
        REDDIT_USERNAME,
        REDDIT_PASSWORD,
    ])

def _parse_first_int(value: str | None) -> int:
    if not value:
        return 0
    match = re.search(r"-?\d+", value.replace(",", ""))
    return int(match.group(0)) if match else 0

def _text_or_empty(selector) -> str:
    text = selector.get()
    return text.strip() if text else ""

@retry(reraise=True, stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, min=1, max=30))
def _fetch_reddit_search(fetcher, url: str, headers: dict):
    return fetcher.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)

def scrape_reddit(subreddits: List[str], keywords: List[str], limit_per_search: int = 25) -> List[RawPost]:
    """
    Scrapes Reddit for posts matching keywords in specific subreddits.
    Uses the Reddit API first, then falls back to Scrapling when the API is
    unavailable or credentials are missing.
    """
    if _has_reddit_api_config():
        try:
            return _scrape_reddit_api(subreddits, keywords, limit_per_search)
        except Exception:
            logger.exception("Reddit API scrape failed")
    else:
        logger.info("Reddit API credentials are missing; using Scrapling fallback.")

    if REDDIT_USE_SCRAPLING_FALLBACK:
        return _scrape_reddit_with_scrapling(subreddits, keywords, limit_per_search)

    return []

def _scrape_reddit_api(subreddits: List[str], keywords: List[str], limit_per_search: int) -> List[RawPost]:
    """
    Scrapes Reddit through PRAW.
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

def _scrape_reddit_with_scrapling(subreddits: List[str], keywords: List[str], limit_per_search: int) -> List[RawPost]:
    """
    Scrapes Reddit search pages with Scrapling when the API cannot be used.
    """
    try:
        from scrapling.fetchers import Fetcher
    except ImportError as exc:
        raise RuntimeError(
            "Scrapling fallback is enabled but dependencies are missing. "
            "Install them with: pip install scrapling curl-cffi browserforge playwright"
        ) from exc

    raw_posts = []
    seen_urls = set()
    headers = {"User-Agent": REDDIT_USER_AGENT}

    for sub_name in subreddits:
        for keyword in keywords:
            search_url = (
                f"{REDDIT_BASE_URL}/r/{sub_name}/search"
                f"?q={quote_plus(keyword)}&restrict_sr=on&sort=new&t=week"
            )
            try:
                page = _fetch_reddit_search(Fetcher, search_url, headers)
            except Exception:
                logger.exception("Scrapling Reddit scrape failed for r/%s / %s", sub_name, keyword)
                continue

            if getattr(page, "status", None) and page.status >= 400:
                logger.warning("Scrapling Reddit scrape returned HTTP %s for %s", page.status, search_url)
                continue

            for result in page.css("div.search-result")[:limit_per_search]:
                title = _text_or_empty(result.css("a.search-title::text"))
                url = _text_or_empty(result.css("a.search-title::attr(href)"))
                body_parts = []
                for part in result.css("div.search-expando div.md p::text"):
                    text = part.get()
                    if text and text.strip():
                        body_parts.append(text.strip())
                body = "\n\n".join(body_parts)
                upvotes = _parse_first_int(result.css("span.search-score::text").get())
                num_comments = _parse_first_int(result.css("a.search-comments::text").get())
                created_at_raw = _text_or_empty(result.css("span.search-time time::attr(datetime)"))

                if not title or not url or upvotes < MIN_UPVOTES or url in seen_urls:
                    continue

                if url.startswith("/"):
                    url = f"{REDDIT_BASE_URL}{url}"

                created_at = None
                if created_at_raw:
                    try:
                        created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                    except ValueError:
                        created_at = None

                raw_posts.append(
                    RawPost(
                        source=Source.REDDIT,
                        url=url,
                        title=title,
                        body=body,
                        upvotes=upvotes,
                        num_comments=num_comments,
                        subreddit=sub_name,
                        created_at=created_at,
                    )
                )
                seen_urls.add(url)

    return raw_posts
