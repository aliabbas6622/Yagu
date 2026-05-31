import requests
import json
import time
import urllib.parse
from typing import List
from product_idea_miner.config.models import RawPost, Source
from product_idea_miner.config.settings import TINYFISH_API_KEY

def scrape_quora(search_queries: List[str]) -> List[RawPost]:
    """
    Scrapes Quora using TinyFish Agent API.
    """
    if not TINYFISH_API_KEY:
        print("TINYFISH_API_KEY not set, skipping Quora scrape.")
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
            response = requests.post("https://api.tinyfish.ai/v1/agent/run", headers=headers, json=payload)
            response.raise_for_status()
            run_data = response.json()
            run_id = run_data.get("run_id")

            if not run_id:
                print(f"Failed to get run_id for query: {query}")
                continue

            # Polling for completion
            result_json = None
            for _ in range(30): # Poll for up to 5 minutes
                poll_resp = requests.get(f"https://api.tinyfish.ai/v1/agent/run/{run_id}", headers=headers)
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()

                if poll_data.get("status") == "completed":
                    result_json = poll_data.get("output")
                    break
                elif poll_data.get("status") == "failed":
                    print(f"TinyFish run failed for query: {query}")
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
                            print(f"Could not parse JSON from TinyFish output for query: {query}")
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

        except Exception as e:
            print(f"Error scraping Quora for query '{query}': {e}")

    return raw_posts
