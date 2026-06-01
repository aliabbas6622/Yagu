import logging
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from product_idea_miner.tools import supabase_tool
from product_idea_miner.agents.adk_orchestrator import pipeline_task
from product_idea_miner.config.models import IdeaRecord

logger = logging.getLogger(__name__)

app = FastAPI(title="Product Idea Miner API")

# Configure allowed origins from environment variable or default to a sensible list
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/ideas", response_model=List[IdeaRecord])
async def get_ideas(limit: int = 50):
    """
    Fetch the latest product ideas.
    """
    try:
        supabase = supabase_tool.get_supabase_client()
        response = (
            supabase.table("ideas")
            .select("*")
            .order("total_score", desc=True)
            .limit(limit)
            .execute()
        )

        ideas = []
        for item in response.data:
            from product_idea_miner.config.models import ProductIdea
            product_ideas = [ProductIdea(**p) for p in item["product_ideas"]]
            item["product_ideas"] = product_ideas
            if isinstance(item.get("source"), str):
                item["source"] = item["source"].lower()
            ideas.append(IdeaRecord(**item))

        return ideas
    except Exception as e:
        logger.error(f"Error fetching ideas: {e}")
        return []

@app.post("/api/trigger")
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    Trigger the scraping pipeline in the background.
    """
    background_tasks.add_task(pipeline_task)
    return {"status": "Pipeline triggered in background"}

@app.get("/api/stats")
async def get_stats():
    """
    Fetch some basic stats for the dashboard.
    """
    try:
        supabase = supabase_tool.get_supabase_client()
        # Count total
        total_res = supabase.table("ideas").select("id", count="exact").execute()
        total_count = total_res.count if total_res.count is not None else 0

        # Average score
        avg_res = supabase.table("ideas").select("total_score").execute()
        scores = [item["total_score"] for item in avg_res.data if item["total_score"] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "total_ideas": total_count,
            "average_score": round(avg_score, 2),
            "top_category": "TBD"
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {"total_ideas": 0, "average_score": 0, "top_category": "N/A"}
