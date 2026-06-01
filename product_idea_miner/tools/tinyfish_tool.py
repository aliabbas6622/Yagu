import requests
import json
import time
import urllib.parse
import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.config.settings import (
    REQUEST_TIMEOUT_SECONDS,
    RETRY_ATTEMPTS,
    RETRY_WAIT_SECONDS,
    TINYFISH_API_KEY,
)

logger = logging.getLogger(__name__)

@retry(reraise=True, stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, min=1, max=30))
def _request_json(method: str, url: str, **kwargs):
    response = requests.request(method, url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
    response.raise_for_status()
    return response.json()

def scrape_quora(search_queries: List[str]) -> List[RawPost]:
    """
    Scrapes Quora using TinyFish Agent API.
    """
    if not TINYFISH_API_KEY:
        logger.info("TINYFISH_API_KEY not set, skipping Quora scrape.")
        return []

    headers = {
        "Authorization": f"Bearer {TINYFISH_API_KEY}",
        "Content-Type": "application/json"
    }

    raw_posts = []
    seen_urls = set()

    for query in search_queries:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.quora.com/search?q={encoded_query}"

        payload = {
            "url": url,
            "goal": "Extract the top 10 questions from this Quora search page. For each question return: question_text, url, number_of_answers. Return as JSON array only."
        }

        try:
            run_data = _request_json("POST", "https://api.tinyfish.ai/v1/agent/run", headers=headers, json=payload)
            run_id = run_data.get("run_id")

            if not run_id:
                logger.warning("Failed to get run_id for query: %s", query)
                continue

            # Polling for completion
            result_json = None
            for _ in range(30): # Poll for up to 5 minutes
                poll_data = _request_json("GET", f"https://api.tinyfish.ai/v1/agent/run/{run_id}", headers=headers)

                if poll_data.get("status") == "completed":
                    result_json = poll_data.get("output")
                    break
                elif poll_data.get("status") == "failed":
                    logger.warning("TinyFish run failed for query: %s", query)
                    break

                time.sleep(10)

            if result_json:
                # result_json might be a string containing JSON or actual JSON
                if isinstance(result_json, str):
                    try:
                        questions = json.loads(result_json)
                    except json.JSONDecodeError:
                        # Sometimes LLMs wrap JSON in code blocks
                        if "```json" in result_json:
                            questions = json.loads(result_json.split("```json")[1].split("```")[0])
                        elif "```" in result_json:
                            questions = json.loads(result_json.split("```")[1].split("```")[0])
                        else:
                            logger.warning("Could not parse JSON from TinyFish output for query: %s", query)
                            continue
                else:
                    questions = result_json

                for q in questions:
                    q_url = q.get("url")
                    if q_url and q_url not in seen_urls:
                        raw_post = RawPost(
                            source=Source.QUORA,
                            url=q_url,
                            title=q.get("question_text", ""),
                            body=f"Number of answers: {q.get('number_of_answers', 'unknown')}",
                            upvotes=0 # Quora doesn't have a direct equivalent easily scrapable here
                        )
                        raw_posts.append(raw_post)
                        seen_urls.add(q_url)

        except Exception:
            logger.exception("Error scraping Quora for query %r", query)

    return raw_posts
