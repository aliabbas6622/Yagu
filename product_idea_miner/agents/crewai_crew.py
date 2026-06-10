import json
import logging
import os
import toons
from typing import Optional
from crewai import Agent, Task, Crew, Process
from tenacity import retry, stop_after_attempt, wait_exponential
from product_idea_miner.config.models import RawPost, AnalysisResult, ProductIdea
from product_idea_miner.config.settings import (
    AI_MODEL,
    AI_PROVIDER_DEFAULT_MODELS,
    ANTHROPIC_API_KEY,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    LLM_ANALYSIS_RETRIES,
    OPENAI_API_KEY,
    OPENROUTER_API_KEY,
    RETRY_WAIT_SECONDS,
    XAI_API_KEY,
)

logger = logging.getLogger(__name__)

for key, value in {
    "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "GROQ_API_KEY": GROQ_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
    "XAI_API_KEY": XAI_API_KEY,
}.items():
    if value:
        os.environ.setdefault(key, value)

def build_crew() -> Crew:
    if not AI_MODEL:
        supported = ", ".join(sorted(AI_PROVIDER_DEFAULT_MODELS))
        raise ValueError(
            "No AI model configured. Set AI_MODEL to any LiteLLM model string, "
            f"or set AI_PROVIDER to one of: {supported}."
        )

    llm = AI_MODEL

    # AGENT 1 — Pain Point Researcher
    researcher = Agent(
        role="Pain Point Researcher",
        goal="Determine if a forum post describes a genuine, monetizable problem",
        backstory="Expert at reading between the lines of user complaints online",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # AGENT 2 — Opportunity Scorer
    scorer = Agent(
        role="Market Opportunity Scorer",
        goal="Score the business opportunity behind this pain point",
        backstory="Startup advisor who evaluates ideas for urgency, market size, and revenue potential",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # AGENT 3 — Product Ideator
    ideator = Agent(
        role="Digital Product Ideator",
        goal="Generate 2-3 concrete digital product ideas that solve this problem",
        backstory="Serial indie hacker who has shipped 20+ profitable digital products",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Task 1: Research
    research_task = Task(
        description=(
            "Analyze the following forum post.\n"
            "Title: {title}\n"
            "Body: {body}\n\n"
            "Determine if this is a genuine pain point. "
            "Return TOON format (Token Oriented Object Notation) with keys: is_pain_point (bool), problem_summary (str), reasoning (str)."
        ),
        expected_output="TOON data with pain point analysis.",
        agent=researcher
    )

    # Task 2: Scoring
    scoring_task = Task(
        description=(
            "Based on the problem summary, score the business opportunity.\n"
            "Return TOON format with keys: urgency_score (int), frequency_score (int), monetization_score (int), "
            "total_score (int), category (str), target_audience (str)."
        ),
        expected_output="TOON data with scores and category.",
        agent=scorer,
        context=[research_task]
    )

    # Task 3: Ideation
    ideation_task = Task(
        description=(
            "Generate 2-3 concrete digital product ideas for this problem.\n"
            "Return TOON format with: product_ideas (list of objects with: idea, type, description)."
        ),
        expected_output="TOON data with a list of product ideas.",
        agent=ideator,
        context=[research_task, scoring_task]
    )

    return Crew(
        agents=[researcher, scorer, ideator],
        tasks=[research_task, scoring_task, ideation_task],
        process=Process.sequential,
        verbose=True
    )

def clean_format_string(s: str) -> str:
    """
    Cleans a string that might contain data wrapped in markdown code blocks.
    """
    s = s.strip()
    if "```" in s:
        # Split by ``` and take the second part if it exists
        parts = s.split("```")
        if len(parts) >= 2:
            content = parts[1]
            # If the block has a language identifier (like json or toon), skip first line
            if "\n" in content:
                first_line = content.split("\n")[0]
                if not first_line.strip() or not any(c in first_line for c in "{[:"):
                    content = "\n".join(content.split("\n")[1:])
            s = content
    return s.strip()

def parse_llm_output(s: str) -> dict:
    """
    Tries to parse output as TOON, then falls back to JSON.
    """
    cleaned = clean_format_string(s)
    try:
        return toons.loads(cleaned)
    except Exception:
        try:
            return json.loads(cleaned)
        except Exception:
            logger.warning("Failed to parse LLM output as TOON or JSON: %s", cleaned[:100])
            raise

@retry(reraise=True, stop=stop_after_attempt(LLM_ANALYSIS_RETRIES), wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, min=1, max=30))
def analyze_post(post: RawPost) -> AnalysisResult:
    """
    Runs the CrewAI analysis on a single post.
    """
    crew = build_crew()
    result = crew.kickoff(inputs={"title": post.title, "body": post.body})

    try:
        research_out = parse_llm_output(result.tasks_output[0].raw)
        scoring_out = parse_llm_output(result.tasks_output[1].raw)
        ideation_out = parse_llm_output(result.tasks_output[2].raw)

        is_pain = research_out.get("is_pain_point")
        # Handle TOON potentially returning string "true"/"false" if not careful,
        # though toons.loads handles basic types.
        if not is_pain or str(is_pain).lower() == "false":
            return AnalysisResult(is_pain_point=False)

        product_ideas = [ProductIdea(**p) for p in ideation_out.get("product_ideas", [])]

        return AnalysisResult(
            is_pain_point=True,
            problem_summary=research_out.get("problem_summary"),
            urgency_score=scoring_out.get("urgency_score"),
            frequency_score=scoring_out.get("frequency_score"),
            monetization_score=scoring_out.get("monetization_score"),
            total_score=scoring_out.get("total_score"),
            product_ideas=product_ideas,
            category=scoring_out.get("category"),
            target_audience=scoring_out.get("target_audience")
        )
    except Exception:
        logger.exception("Error parsing CrewAI output for post %s", post.url)
        # Log the raw outputs for debugging
        logger.debug("Research raw: %s", result.tasks_output[0].raw)
        logger.debug("Scoring raw: %s", result.tasks_output[1].raw)
        logger.debug("Ideation raw: %s", result.tasks_output[2].raw)
        return AnalysisResult(is_pain_point=False)
