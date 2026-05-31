import json
from typing import Optional
from crewai import Agent, Task, Crew, Process
from product_idea_miner.config.models import RawPost, AnalysisResult, ProductIdea
from product_idea_miner.config.settings import ANTHROPIC_API_KEY

# LiteLLM is used by CrewAI, we just need to ensure the API key is in the environment
import os
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY or ""

def build_crew() -> Crew:
    # Use claude-3-5-sonnet via LiteLLM/Anthropic
    llm = "anthropic/claude-3-5-sonnet-20241022"

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
            "Return JSON with: is_pain_point (bool), problem_summary (1 clear sentence, only if true), reasoning (str)."
        ),
        expected_output="A JSON object with pain point analysis.",
        agent=researcher
    )

    # Task 2: Scoring
    scoring_task = Task(
        description=(
            "Based on the problem summary, score the business opportunity.\n"
            "Output JSON with: urgency_score (1-10), frequency_score (1-10), monetization_score (1-10), "
            "total_score (sum), category (one of [productivity, finance, health, dev-tools, marketing, education, other]), "
            "target_audience (str)."
        ),
        expected_output="A JSON object with scores and category.",
        agent=scorer,
        context=[research_task]
    )

    # Task 3: Ideation
    ideation_task = Task(
        description=(
            "Generate 2-3 concrete digital product ideas for this problem.\n"
            "Output JSON with: product_ideas (array of objects with: idea, type, description)."
        ),
        expected_output="A JSON object with a list of product ideas.",
        agent=ideator,
        context=[research_task, scoring_task]
    )

    return Crew(
        agents=[researcher, scorer, ideator],
        tasks=[research_task, scoring_task, ideation_task],
        process=Process.sequential,
        verbose=True
    )

def clean_json_string(s: str) -> str:
    """
    Cleans a string that might contain JSON wrapped in markdown code blocks.
    """
    s = s.strip()
    if "```json" in s:
        s = s.split("```json")[1].split("```")[0]
    elif "```" in s:
        s = s.split("```")[1].split("```")[0]
    return s.strip()

def analyze_post(post: RawPost) -> AnalysisResult:
    """
    Runs the CrewAI analysis on a single post.
    """
    crew = build_crew()
    result = crew.kickoff(inputs={"title": post.title, "body": post.body})

    try:
        research_out_raw = clean_json_string(result.tasks_output[0].raw)
        scoring_out_raw = clean_json_string(result.tasks_output[1].raw)
        ideation_out_raw = clean_json_string(result.tasks_output[2].raw)

        research_out = json.loads(research_out_raw)
        scoring_out = json.loads(scoring_out_raw)
        ideation_out = json.loads(ideation_out_raw)

        if not research_out.get("is_pain_point"):
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
    except Exception as e:
        print(f"Error parsing CrewAI output: {e}")
        # Log the raw outputs for debugging
        print(f"Research raw: {result.tasks_output[0].raw}")
        print(f"Scoring raw: {result.tasks_output[1].raw}")
        print(f"Ideation raw: {result.tasks_output[2].raw}")
        return AnalysisResult(is_pain_point=False)
