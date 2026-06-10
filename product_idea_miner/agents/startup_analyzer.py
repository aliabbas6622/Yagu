import json
import logging
import os
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from tenacity import retry, stop_after_attempt, wait_exponential
from product_idea_miner.config.models import StartupRaw, StartupRecord
from product_idea_miner.config.settings import (
    AI_MODEL,
    AI_PROVIDER_DEFAULT_MODELS,
    LLM_ANALYSIS_RETRIES,
    RETRY_WAIT_SECONDS,
)
from product_idea_miner.agents.crewai_crew import parse_llm_output

logger = logging.getLogger(__name__)

def build_startup_crew() -> Crew:
    llm = AI_MODEL

    # AGENT — Startup Analyst
    analyst = Agent(
        role="Startup Investment Analyst",
        goal="Analyze recently launched startups for their innovation, market potential, and execution quality",
        backstory="Venture Capital analyst at a top-tier firm, specialized in early-stage tech startups.",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Task: Analysis
    analysis_task = Task(
        description=(
            "Analyze the following recently launched startup.\n"
            "Name: {name}\n"
            "Description: {description}\n"
            "URL: {url}\n"
            "Country: {country}\n\n"
            "Evaluate and provide scores (1-10) for: innovation_score, market_potential_score, and execution_score. "
            "Calculate total_rating (sum of scores). "
            "Provide a brief summary of your analysis. "
            "Determine the startup's category and confirm the country. "
            "Return TOON format with: innovation_score, market_potential_score, execution_score, total_rating, summary, country, category."
        ),
        expected_output="TOON data with startup analysis and ratings.",
        agent=analyst
    )

    return Crew(
        agents=[analyst],
        tasks=[analysis_task],
        process=Process.sequential,
        verbose=True
    )

@retry(reraise=True, stop=stop_after_attempt(LLM_ANALYSIS_RETRIES), wait=wait_exponential(multiplier=RETRY_WAIT_SECONDS, min=1, max=30))
def analyze_startup(startup: StartupRaw) -> StartupRecord:
    """
    Runs the CrewAI analysis on a single startup launch.
    """
    crew = build_startup_crew()
    result = crew.kickoff(inputs={
        "name": startup.name,
        "description": startup.description,
        "url": startup.url,
        "country": startup.country
    })

    try:
        analysis_out = parse_llm_output(result.raw)

        return StartupRecord(
            name=startup.name,
            url=startup.url,
            description=startup.description,
            country=analysis_out.get("country", startup.country),
            category=analysis_out.get("category", "Unknown"),
            innovation_score=analysis_out.get("innovation_score", 0),
            market_potential_score=analysis_out.get("market_potential_score", 0),
            execution_score=analysis_out.get("execution_score", 0),
            total_rating=analysis_out.get("total_rating", 0),
            summary=analysis_out.get("summary", ""),
            date_found=datetime.now()
        )
    except Exception:
        logger.exception("Error parsing CrewAI output for startup %s", startup.url)
        return None
