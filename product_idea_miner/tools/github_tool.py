import logging
import urllib.parse
import urllib.request
import json
from datetime import datetime
from typing import List, Any

from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.tools.crawlee_engine import run_crawlee_async, scrape_with_cheerio

logger = logging.getLogger(__name__)

def scrape_github(repos: List[str]) -> List[RawPost]:
    """
    Scrapes GitHub issues for the given list of repositories.
    First tries the official GitHub REST API (direct API routes),
    and falls back to Crawlee's BeautifulSoupCrawler if it fails.
    """
    if not repos:
        return []

    raw_posts: List[RawPost] = []
    failed_repos: List[str] = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 1. Try official API routes
    logger.info("Attempting to fetch GitHub issues via API...")
    for repo in repos:
        try:
            # Search for open issues (excluding PRs) in the repo, limit to 5
            q = urllib.parse.quote(f"repo:{repo} is:issue state:open")
            api_url = f"https://api.github.com/search/issues?q={q}&per_page=5"
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                search_data = json.loads(response.read().decode('utf-8'))
                issues = search_data.get("items", [])
                repo_posts_count = 0
                for issue in issues:
                    created_at_dt = datetime.now()
                    if issue.get("created_at"):
                        try:
                            # Format: "2026-06-04T02:00:00Z"
                            created_at_dt = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                        except Exception:
                            pass

                    raw_posts.append(
                        RawPost(
                            source=Source.GITHUB,
                            url=issue.get("html_url", ""),
                            title=issue.get("title", ""),
                            body=issue.get("body") or "",
                            upvotes=issue.get("reactions", {}).get("total_count", 0),
                            num_comments=issue.get("comments", 0),
                            created_at=created_at_dt,
                        )
                    )
                    repo_posts_count += 1
                logger.info("Fetched %s issues from repo %s via Search API", repo_posts_count, repo)
        except Exception as e:
            logger.warning("Failed to fetch GitHub issues via Search API for %s: %s. Will fallback to BeautifulSoupCrawler.", repo, e)
            failed_repos.append(repo)

    # 2. Fallback to Crawlee BeautifulSoupCrawler for failed repos
    if failed_repos:
        logger.info("Starting Crawlee BeautifulSoupCrawler fallback for repos: %s", failed_repos)
        start_urls = [f"https://github.com/{repo}/issues" for repo in failed_repos]

        async def request_handler(context: Any) -> None:
            url = context.request.url
            logger.info("Processing GitHub fallback page: %s", url)
            soup = context.soup

            # Detail Page Check
            if "/issues/" in url:
                title_el = soup.select_one(".gh-header-title")
                body_el = soup.select_one(".comment-body")

                title = title_el.get_text(strip=True) if title_el else ""
                if title and " #" in title:
                    title = title.split(" #")[0]

                body = body_el.get_text(strip=True) if body_el else ""

                if title:
                    raw_posts.append(
                        RawPost(
                            source=Source.GITHUB,
                            url=url,
                            title=title,
                            body=body[:2000],
                            upvotes=0,
                            num_comments=0,
                            created_at=datetime.now(),
                        )
                    )
            # Index Page Check
            else:
                issue_links = soup.select(".js-navigation-container .js-issue-row a.Link--primary")
                urls_to_enqueue = []
                for link in issue_links:
                    href = link.get("href")
                    if href:
                        detail_url = urllib.parse.urljoin("https://github.com", href)
                        urls_to_enqueue.append(detail_url)

                await context.add_requests(urls_to_enqueue[:3])

        try:
            run_crawlee_async(scrape_with_cheerio, start_urls, request_handler)
        except Exception as crawler_err:
            logger.error("Crawlee fallback failed: %s", crawler_err)

    logger.info("GitHub scraping complete. Found %s potential issues.", len(raw_posts))
    return raw_posts

# For simple testing
def test_scrape():
    logging.basicConfig(level=logging.INFO)
    posts = scrape_github(["fastapi/fastapi", "langchain-ai/langchain"])
    for post in posts:
        title_safe = post.title.encode('ascii', 'ignore').decode('ascii')
        body_safe = post.body.encode('ascii', 'ignore').decode('ascii')
        print(f"URL: {post.url}\nTitle: {title_safe}\nBody Snippet: {body_safe[:150]}\n")

if __name__ == "__main__":
    test_scrape()
