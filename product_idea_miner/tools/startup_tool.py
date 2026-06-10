import json
import time
import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from product_idea_miner.config.models import StartupRaw
from product_idea_miner.config.settings import (
    REQUEST_TIMEOUT_SECONDS,
    RETRY_ATTEMPTS,
    RETRY_WAIT_SECONDS,
    TINYFISH_API_KEY,
    STARTUP_SOURCES,
)

logger = logging.getLogger(__name__)

@retry(reraise=True, stop=stop_after_attempt(RETRY_ATTEMPTS), wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, min=1, max=30))
def _request_json(method: str, url: str, **kwargs):
    import requests
    response = requests.request(method, url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
    response.raise_for_status()
    return response.json()

def scrape_recent_startups(limit_per_source: int = 3) -> List[StartupRaw]:
    """
    Scrapes recently launched startups from multiple regional sources using TinyFish Agent API.
    """
    if not TINYFISH_API_KEY:
        logger.info("TINYFISH_API_KEY not set, skipping startup scrape.")
        return []

    headers = {
        "Authorization": f"Bearer {TINYFISH_API_KEY}",
        "Content-Type": "application/json"
    }

    all_startups = []

    for source in STARTUP_SOURCES:
        country = source["country"]
        url = source["url"]

        logger.info("Scraping startups for %s from %s", country, url)

        payload = {
            "url": url,
            "goal": f"Extract {limit_per_source} recently launched or featured startups from this page. For each startup return: name, url, description. Return as JSON array only."
        }

        try:
            run_data = _request_json("POST", "https://api.tinyfish.ai/v1/agent/run", headers=headers, json=payload)
            run_id = run_data.get("run_id")

            if not run_id:
                logger.warning("Failed to get run_id for startup scrape at %s", url)
                continue

            # Polling for completion
            result_json = None
            for _ in range(30): # Poll for up to 5 minutes
                poll_data = _request_json("GET", f"https://api.tinyfish.ai/v1/agent/run/{run_id}", headers=headers)

                if poll_data.get("status") == "completed":
                    result_json = poll_data.get("output")
                    break
                elif poll_data.get("status") == "failed":
                    logger.warning("TinyFish run failed for startup scrape at %s", url)
                    break

                time.sleep(10)

            if result_json:
                if isinstance(result_json, str):
                    try:
                        raw_data = json.loads(result_json)
                    except json.JSONDecodeError:
                        if "```json" in result_json:
                            raw_data = json.loads(result_json.split("```json")[1].split("```")[0])
                        elif "```" in result_json:
                            raw_data = json.loads(result_json.split("```")[1].split("```")[0])
                        else:
                            logger.warning("Could not parse JSON from TinyFish output for %s", url)
                            continue
                else:
                    raw_data = result_json

                for s in raw_data:
                    all_startups.append(StartupRaw(
                        name=s.get("name", "Unknown"),
                        url=s.get("url", url), # fallback to source url if not found
                        description=s.get("description", ""),
                        country=country
                    ))

        except Exception:
            logger.exception("Error scraping startups from %s", url)

    return all_startups
