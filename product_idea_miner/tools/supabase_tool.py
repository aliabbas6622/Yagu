import logging
from typing import List
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from product_idea_miner.config.models import RawPost, IdeaRecord, ProductIdea, StartupRaw, StartupRecord
from product_idea_miner.config.settings import (
    RETRY_ATTEMPTS,
    RETRY_WAIT_SECONDS,
    SUPABASE_URL,
    SUPABASE_KEY,
)

logger = logging.getLogger(__name__)

def _retry_db():
    return retry(
        reraise=True,
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, min=1, max=30),
        retry=retry_if_exception_type(Exception),
    )

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY "
            "in your environment before running the miner."
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@_retry_db()
def check_duplicates(posts: List[RawPost]) -> List[RawPost]:
    """
    Returns only posts NOT already in the database.
    """
    if not posts:
        return []

    supabase = get_supabase_client()
    urls = [post.url for post in posts]

    # Supabase query to find existing URLs
    response = supabase.table("ideas").select("original_url").in_("original_url", urls).execute()
    existing_urls = {item["original_url"] for item in response.data}
    logger.info("Found %s duplicate Reddit/source URLs", len(existing_urls))

    return [post for post in posts if post.url not in existing_urls]

@_retry_db()
def check_startup_duplicates(startups: List[StartupRaw]) -> List[StartupRaw]:
    """
    Returns only startups NOT already in the database.
    """
    if not startups:
        return []

    supabase = get_supabase_client()
    urls = [s.url for s in startups]

    # Supabase query to find existing URLs
    response = supabase.table("startups").select("url").in_("url", urls).execute()
    existing_urls = {item["url"] for item in response.data}
    logger.info("Found %s duplicate startup URLs", len(existing_urls))

    return [s for s in startups if s.url not in existing_urls]

@_retry_db()
def save_startups(startups: List[StartupRecord]) -> int:
    """
    Saves a list of StartupRecords to Supabase.
    """
    if not startups:
        return 0

    supabase = get_supabase_client()
    data_to_insert = []

    for startup in startups:
        startup_dict = startup.model_dump(exclude={"id"})
        # date_found to ISO string
        startup_dict["date_found"] = startup.date_found.isoformat()
        data_to_insert.append(startup_dict)

    response = supabase.table("startups").upsert(data_to_insert, on_conflict="url").execute()
    logger.info("Saved %s startups to Supabase", len(response.data))
    return len(response.data)

@_retry_db()
def save_ideas(ideas: List[IdeaRecord]) -> int:
    """
    Saves a list of IdeaRecords to Supabase.
    """
    if not ideas:
        return 0

    supabase = get_supabase_client()
    data_to_insert = []

    for idea in ideas:
        idea_dict = idea.model_dump(exclude={"id"})
        # Convert product_ideas list of models to list of dicts for JSONB
        idea_dict["product_ideas"] = [p.model_dump() for p in idea.product_ideas]
        # Source is Enum, convert to string
        idea_dict["source"] = idea.source.value
        # date_found to ISO string
        idea_dict["date_found"] = idea.date_found.isoformat()
        data_to_insert.append(idea_dict)

    response = supabase.table("ideas").upsert(data_to_insert, on_conflict="original_url").execute()
    logger.info("Saved %s ideas to Supabase", len(response.data))
    return len(response.data)

@_retry_db()
def get_unsent_ideas(limit: int = 10) -> List[IdeaRecord]:
    """
    Retrieves ideas that haven't been sent in a digest yet.
    """
    supabase = get_supabase_client()
    response = (
        supabase.table("ideas")
        .select("*")
        .eq("sent_in_digest", False)
        .order("total_score", desc=True)
        .limit(limit)
        .execute()
    )

    ideas = []
    for item in response.data:
        # Convert product_ideas from JSON to list of ProductIdea models
        product_ideas = [ProductIdea(**p) for p in item["product_ideas"]]
        item["product_ideas"] = product_ideas
        if isinstance(item.get("source"), str):
            item["source"] = item["source"].lower()
        ideas.append(IdeaRecord(**item))

    return ideas

@_retry_db()
def mark_as_sent(idea_ids: List[str]):
    """
    Marks ideas as sent in digest.
    """
    if not idea_ids:
        return

    supabase = get_supabase_client()
    supabase.table("ideas").update({"sent_in_digest": True}).in_("id", idea_ids).execute()
    logger.info("Marked %s ideas as sent", len(idea_ids))
