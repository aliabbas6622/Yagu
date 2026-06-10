from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# Source enum
class Source(str, Enum):
    REDDIT = "reddit"
    QUORA = "quora"
    HN = "hn"
    STARTUP_LAUNCH = "startup_launch"

# One product idea suggested by CrewAI
class ProductIdea(BaseModel):
    idea: str           # e.g. "Notion template for freelance invoicing"
    type: str           # SaaS | Chrome Extension | Template | Course | Newsletter
    description: str    # 2 sentences max

# Raw scraped post (before AI analysis)
class RawPost(BaseModel):
    source: Source
    url: str            # unique identifier, used for dedup
    title: str
    body: str
    upvotes: int = 0
    num_comments: int = 0
    subreddit: Optional[str] = None
    created_at: Optional[datetime] = None

# Full AI analysis output for one post
class AnalysisResult(BaseModel):
    is_pain_point: bool
    problem_summary: Optional[str] = None      # 1 clear sentence
    urgency_score: Optional[int] = None        # 1–10
    frequency_score: Optional[int] = None      # 1–10
    monetization_score: Optional[int] = None   # 1–10
    total_score: Optional[int] = None          # sum of above 3 (max 30)
    product_ideas: Optional[List[ProductIdea]] = None
    category: Optional[str] = None             # productivity / finance / dev-tools / etc.
    target_audience: Optional[str] = None

# Full record saved to Supabase
class IdeaRecord(BaseModel):
    id: Optional[str] = None # UUID from Supabase
    source: Source
    original_url: str
    post_title: str
    post_body: str
    problem_summary: str
    urgency_score: int
    frequency_score: int
    monetization_score: int
    total_score: int
    product_ideas: List[ProductIdea]   # stored as JSONB in Supabase
    category: str
    target_audience: str
    date_found: datetime
    sent_in_digest: bool = False

# Startup analysis result
class StartupAnalysis(BaseModel):
    innovation_score: int        # 1–10
    market_potential_score: int # 1–10
    execution_score: int        # 1–10
    total_rating: int           # sum or weighted average (max 30)
    summary: str                # 2-3 sentences analysis
    country: str
    category: str

# Raw startup data from scraper
class StartupRaw(BaseModel):
    name: str
    url: str
    description: str
    launch_date: Optional[datetime] = None
    country: Optional[str] = "Unknown"

# Full record for a startup
class StartupRecord(BaseModel):
    id: Optional[str] = None
    name: str
    url: str
    description: str
    country: str
    category: str
    innovation_score: int
    market_potential_score: int
    execution_score: int
    total_rating: int
    summary: str
    date_found: datetime

# LangGraph pipeline state — flows through every node
class PipelineState(BaseModel):
    raw_posts: List[RawPost] = []
    deduplicated_posts: List[RawPost] = []
    analyzed_ideas: List[IdeaRecord] = []

    raw_startups: List[StartupRaw] = []
    deduplicated_startups: List[StartupRaw] = []
    analyzed_startups: List[StartupRecord] = []

    saved_count: int = 0
    errors: List[str] = []
