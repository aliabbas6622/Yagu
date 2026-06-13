import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import os
from pydantic import BaseModel
import litellm

from product_idea_miner.tools import supabase_tool, status_tool
from product_idea_miner.agents.adk_orchestrator import pipeline_task
from product_idea_miner.config.models import IdeaRecord
from product_idea_miner.config.settings import (
    AI_MODEL,
    ANTHROPIC_API_KEY,
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    OPENAI_API_KEY,
    GROQ_API_KEY
)

# Setup keys for LiteLLM
for k, v in {
    "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "GROQ_API_KEY": GROQ_API_KEY,
}.items():
    if v:
        os.environ[k] = v

LLM_MODEL = AI_MODEL or "gemini/gemini-2.0-flash"

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

        # Average score and source breakdown
        res = supabase.table("ideas").select("source, total_score").execute()
        scores = [item["total_score"] for item in res.data if item["total_score"] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        source_breakdown = {}
        for item in res.data:
            source = item.get("source")
            if source:
                source = source.lower()
                source_breakdown[source] = source_breakdown.get(source, 0) + 1

        return {
            "total_ideas": total_count,
            "average_score": round(avg_score, 2),
            "top_category": "TBD",
            "source_breakdown": source_breakdown
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {"total_ideas": 0, "average_score": 0, "top_category": "N/A"}

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@app.get("/api/scraper/status")
async def get_scraper_status():
    """
    Get current progress and logs of the scraper pipeline.
    """
    return status_tool.tracker.get_state()

@app.post("/api/ideas/{id}/chat")
async def chat_with_idea(id: str, payload: ChatRequest):
    """
    Chat with an AI co-founder about this specific idea.
    """
    try:
        supabase = supabase_tool.get_supabase_client()
        res = supabase.table("ideas").select("*").eq("id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Idea not found")
        idea = res.data[0]

        # Structure history for LiteLLM
        messages = []
        
        # System prompt setting the Persona
        system_prompt = (
            "You are a seasoned startup co-founder, incubator director, and venture builder AI.\n"
            "You are helping the user validate and develop a product idea based on this identified pain point:\n\n"
            f"Category: {idea.get('category')}\n"
            f"Target Audience: {idea.get('target_audience')}\n"
            f"Original Post Title: {idea.get('post_title')}\n"
            f"Original Post Body: {idea.get('post_body')[:1000]}\n"
            f"Identified Problem: {idea.get('problem_summary')}\n"
            f"Suggested Product Idea(s): {idea.get('product_ideas')}\n\n"
            "Provide highly critical, realistic, and tactical feedback. "
            "Suggest business models, simple tech stacks, feature scopes, and clear 48-hour customer validation steps. "
            "Keep answers concise, realistic (favoring MVP/indie-hacker approaches), and formatted in clean markdown."
        )
        messages.append({"role": "system", "content": system_prompt})

        # Append history
        for h in payload.history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        # Append latest message
        messages.append({"role": "user", "content": payload.message})

        # Call LLM
        response = litellm.completion(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        logger.exception("Error in co-founder chat")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ideas/{id}/landing-page")
async def generate_landing_page(id: str):
    """
    Generate landing page copy for this idea.
    """
    try:
        supabase = supabase_tool.get_supabase_client()
        res = supabase.table("ideas").select("*").eq("id", id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Idea not found")
        idea = res.data[0]

        system_prompt = (
            "You are a conversion copywriting and SaaS positioning expert.\n"
            "Generate detailed, high-converting Landing Page Copy for a digital product that solves this pain point:\n\n"
            f"Problem: {idea.get('problem_summary')}\n"
            f"Target Audience: {idea.get('target_audience')}\n"
            f"Suggested Ideas: {idea.get('product_ideas')}\n"
            f"Category: {idea.get('category')}\n\n"
            "Generate output in structured JSON format. Avoid markdown formatting blocks. Format exactly as this JSON:\n"
            "{\n"
            "  \"headline\": \"Catchy, value-driven main headline\",\n"
            "  \"subheadline\": \"Clear explanation of how it works and what the user gets\",\n"
            "  \"hero_cta\": \"Text for the main sign up button\",\n"
            "  \"features\": [\n"
            "    {\"title\": \"Feature 1 Name\", \"description\": \"Benefit-driven feature description\"},\n"
            "    {\"title\": \"Feature 2 Name\", \"description\": \"Benefit-driven feature description\"},\n"
            "    {\"title\": \"Feature 3 Name\", \"description\": \"Benefit-driven feature description\"}\n"
            "  ],\n"
            "  \"faq\": [\n"
            "    {\"question\": \"Frequently Asked Question 1?\", \"answer\": \"Clear, encouraging answer\"},\n"
            "    {\"question\": \"Frequently Asked Question 2?\", \"answer\": \"Clear, encouraging answer\"}\n"
            "  ],\n"
            "  \"launch_plan\": \"Quick MVP/Validation plan in 2 sentences.\"\n"
            "}"
        )

        response = litellm.completion(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        import json
        raw_content = response.choices[0].message.content
        logger.info(f"Generated landing page content: {raw_content}")
        return json.loads(raw_content)
    except Exception as e:
        logger.exception("Error generating landing page")
        raise HTTPException(status_code=500, detail=str(e))
