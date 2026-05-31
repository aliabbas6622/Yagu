import json
from typing import List
from supabase import create_client, Client
from product_idea_miner.config.models import RawPost, IdeaRecord, ProductIdea
from product_idea_miner.config.settings import SUPABASE_URL, SUPABASE_ANON_KEY

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

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

    return [post for post in posts if post.url not in existing_urls]

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
    return len(response.data)

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
        ideas.append(IdeaRecord(**item))

    return ideas

def mark_as_sent(idea_ids: List[str]):
    """
    Marks ideas as sent in digest.
    """
    if not idea_ids:
        return

    supabase = get_supabase_client()
    supabase.table("ideas").update({"sent_in_digest": True}).in_("id", idea_ids).execute()
