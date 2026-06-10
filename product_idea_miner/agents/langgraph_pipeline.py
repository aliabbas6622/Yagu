import logging
from datetime import datetime
from langgraph.graph import StateGraph, END
from product_idea_miner.config.models import PipelineState, IdeaRecord, ProductIdea
from product_idea_miner.config.settings import (
    AI_ANALYSIS_ENABLED,
    AI_MODEL,
    AI_PROVIDER,
    AI_PROVIDER_KEY,
    MAX_AI_POSTS_PER_RUN,
    MAX_MANUAL_CANDIDATES_PER_RUN,
    MIN_TOTAL_SCORE,
    PAIN_POINT_KEYWORDS,
    QUORA_SCRAPE_ENABLED,
    QUORA_SEARCHES,
    SAVE_MANUAL_CANDIDATES,
    STARTUP_SCRAPE_ENABLED,
    SUBREDDITS,
)
from product_idea_miner.tools import reddit_tool, tinyfish_tool, supabase_tool, hn_tool, webhook_tool, startup_tool
from product_idea_miner.agents import crewai_crew, startup_analyzer

logger = logging.getLogger(__name__)

HIGH_INTENT_TERMS = [
    "frustrated",
    "manual",
    "takes too much time",
    "hard to manage",
    "pain",
    "problem",
    "struggling",
    "wish there was",
    "why is there no",
    "looking for a tool",
    "need a tool",
]

BUYING_INTENT_TERMS = [
    "pay",
    "paid",
    "budget",
    "expensive",
    "client",
    "customer",
    "business",
    "revenue",
    "workflow",
]

def _heuristic_score(post) -> int:
    text = f"{post.title} {post.body}".lower()
    score = min(post.upvotes, 10) + min(post.num_comments, 10)
    score += sum(3 for term in HIGH_INTENT_TERMS if term in text)
    score += sum(2 for term in BUYING_INTENT_TERMS if term in text)
    return score

def _manual_candidate_record(post, score: int) -> IdeaRecord:
    summary = post.title.strip() or "Manual review candidate"
    return IdeaRecord(
        source=post.source,
        original_url=post.url,
        post_title=post.title,
        post_body=post.body,
        problem_summary=f"Manual review needed: {summary[:220]}",
        urgency_score=max(1, min(10, score // 3)),
        frequency_score=max(1, min(10, post.num_comments or 1)),
        monetization_score=max(1, min(10, score // 4)),
        total_score=max(MIN_TOTAL_SCORE, min(30, score)),
        product_ideas=[
            ProductIdea(
                idea="Manual validation candidate",
                type="Research",
                description="Review this post manually before spending LLM tokens on deeper product ideation.",
            )
        ],
        category="manual-review",
        target_audience="Unknown until reviewed",
        date_found=datetime.now(),
        sent_in_digest=False,
    )

def scrape_node(state: PipelineState) -> PipelineState:
    logger.info("Scraping sources for pain points")
    reddit_posts = reddit_tool.scrape_reddit(SUBREDDITS, PAIN_POINT_KEYWORDS)
    quora_posts = tinyfish_tool.scrape_quora(QUORA_SEARCHES) if QUORA_SCRAPE_ENABLED else []
    hn_posts = hn_tool.scrape_hn()

    state.raw_posts = reddit_posts + quora_posts + hn_posts
    logger.info(
        "Scraped %s posts total (Reddit: %s, Quora: %s, HN: %s)",
        len(state.raw_posts),
        len(reddit_posts),
        len(quora_posts),
        len(hn_posts),
    )

    logger.info("Scraping sources for recently launched startups")
    state.raw_startups = startup_tool.scrape_recent_startups(limit=5) if STARTUP_SCRAPE_ENABLED else []
    logger.info("Scraped %s startups", len(state.raw_startups))

    return state

def dedup_node(state: PipelineState) -> PipelineState:
    logger.info("Deduplicating posts")
    new_posts = supabase_tool.check_duplicates(state.raw_posts)
    state.deduplicated_posts = new_posts
    logger.info("%s duplicates removed. %s new posts to analyze.", len(state.raw_posts) - len(new_posts), len(new_posts))

    logger.info("Deduplicating startups")
    new_startups = supabase_tool.check_startup_duplicates(state.raw_startups)
    state.deduplicated_startups = new_startups
    logger.info("%s startup duplicates removed. %s new startups to analyze.", len(state.raw_startups) - len(new_startups), len(new_startups))

    return state

def analyze_node(state: PipelineState) -> PipelineState:
    logger.info("Scoring posts before AI analysis")
    analyzed_ideas = []
    scored_posts = sorted(
        ((post, _heuristic_score(post)) for post in state.deduplicated_posts),
        key=lambda item: item[1],
        reverse=True,
    )
    candidates = [(post, score) for post, score in scored_posts if score >= MIN_TOTAL_SCORE]

    if not candidates:
        logger.info("No posts passed the cheap heuristic filter.")
        state.analyzed_ideas = []
        return state

    can_use_ai = AI_ANALYSIS_ENABLED and bool(AI_PROVIDER_KEY) and MAX_AI_POSTS_PER_RUN > 0
    ai_candidates = candidates[:MAX_AI_POSTS_PER_RUN] if can_use_ai else []
    manual_candidates = candidates[len(ai_candidates):]

    logger.info(
        "Heuristic filter kept %s/%s posts. AI provider=%s model=%s AI candidates=%s manual candidates=%s",
        len(candidates),
        len(state.deduplicated_posts),
        AI_PROVIDER,
        AI_MODEL,
        len(ai_candidates),
        len(manual_candidates),
    )

    # Process in small batches to avoid rate limits and too many concurrent LLM calls
    batch_size = 5
    for i in range(0, len(ai_candidates), batch_size):
        batch = ai_candidates[i:i+batch_size]

        # CrewAI is generally not async-friendly out of the box for sequential processes,
        # but we can run them in parallel if needed. For now, sequential per post.
        for post, _score in batch:
            try:
                result = crewai_crew.analyze_post(post)
                if result.is_pain_point and result.total_score >= MIN_TOTAL_SCORE:
                    idea_record = IdeaRecord(
                        source=post.source,
                        original_url=post.url,
                        post_title=post.title,
                        post_body=post.body,
                        problem_summary=result.problem_summary,
                        urgency_score=result.urgency_score,
                        frequency_score=result.frequency_score,
                        monetization_score=result.monetization_score,
                        total_score=result.total_score,
                        product_ideas=result.product_ideas,
                        category=result.category,
                        target_audience=result.target_audience,
                        date_found=datetime.now(),
                        sent_in_digest=False
                    )
                    analyzed_ideas.append(idea_record)
                    # Instant notification for high-scoring ideas
                    if idea_record.total_score >= 25:
                        webhook_tool.notify_all(idea_record)
            except Exception as e:
                logger.exception("Error analyzing post %s", post.url)
                state.errors.append(f"Analysis error for {post.url}: {str(e)}")

    if SAVE_MANUAL_CANDIDATES:
        remaining_slots = max(0, MAX_MANUAL_CANDIDATES_PER_RUN - len(analyzed_ideas))
        for post, score in manual_candidates[:remaining_slots]:
            analyzed_ideas.append(_manual_candidate_record(post, score))

    state.analyzed_ideas = analyzed_ideas
    logger.info("%s ideas passed the filter.", len(analyzed_ideas))

    logger.info("Analyzing startups")
    analyzed_startups = []
    for startup in state.deduplicated_startups:
        try:
            result = startup_analyzer.analyze_startup(startup)
            if result:
                analyzed_startups.append(result)
        except Exception as e:
            logger.exception("Error analyzing startup %s", startup.url)
            state.errors.append(f"Startup analysis error for {startup.url}: {str(e)}")

    state.analyzed_startups = analyzed_startups
    logger.info("%s startups analyzed.", len(analyzed_startups))

    return state

def save_node(state: PipelineState) -> PipelineState:
    logger.info("Saving ideas")
    saved_ideas_count = 0
    if state.analyzed_ideas:
        saved_ideas_count = supabase_tool.save_ideas(state.analyzed_ideas)
        logger.info("Saved %s new ideas to database.", saved_ideas_count)
    else:
        logger.info("No ideas to save.")

    logger.info("Saving startups")
    saved_startups_count = 0
    if state.analyzed_startups:
        saved_startups_count = supabase_tool.save_startups(state.analyzed_startups)
        logger.info("Saved %s new startups to database.", saved_startups_count)
    else:
        logger.info("No startups to save.")

    state.saved_count = saved_ideas_count + saved_startups_count
    return state

def should_continue_after_dedup(state: PipelineState):
    if not state.deduplicated_posts and not state.deduplicated_startups:
        return "end"
    return "analyze"

def should_continue_after_analyze(state: PipelineState):
    if not state.analyzed_ideas and not state.analyzed_startups:
        return "end"
    return "save"

def build_graph():
    workflow = StateGraph(PipelineState)

    workflow.add_node("scrape", scrape_node)
    workflow.add_node("dedup", dedup_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("save", save_node)

    workflow.set_entry_point("scrape")

    workflow.add_edge("scrape", "dedup")

    workflow.add_conditional_edges(
        "dedup",
        should_continue_after_dedup,
        {
            "analyze": "analyze",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "analyze",
        should_continue_after_analyze,
        {
            "save": "save",
            "end": END
        }
    )

    workflow.add_edge("save", END)

    return workflow.compile()

def run_pipeline() -> PipelineState:
    graph = build_graph()
    initial_state = PipelineState()
    final_state_dict = graph.invoke(initial_state)
    # LangGraph invoke returns a dict if the state is a Pydantic model/TypedDict
    return PipelineState(**final_state_dict)
