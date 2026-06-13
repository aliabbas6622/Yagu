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
    SUBREDDITS,
)
from product_idea_miner.tools import reddit_tool, tinyfish_tool, supabase_tool, hn_tool, webhook_tool, status_tool
from product_idea_miner.agents import crewai_crew

tracker = status_tool.tracker

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
    logger.info("Scraping sources")
    tracker.update_step("Scraping Reddit, Hacker News, and Quora...", 10)
    reddit_posts = reddit_tool.scrape_reddit(SUBREDDITS, PAIN_POINT_KEYWORDS)
    tracker.add_log_msg(f"Reddit scrape completed: found {len(reddit_posts)} candidates.")
    
    quora_posts = tinyfish_tool.scrape_quora(QUORA_SEARCHES) if QUORA_SCRAPE_ENABLED else []
    if QUORA_SCRAPE_ENABLED:
        tracker.add_log_msg(f"Quora scrape completed: found {len(quora_posts)} candidates.")
        
    hn_posts = hn_tool.scrape_hn()
    tracker.add_log_msg(f"Hacker News scrape completed: found {len(hn_posts)} candidates.")

    state.raw_posts = reddit_posts + quora_posts + hn_posts
    tracker.set_stats(scraped=len(state.raw_posts))
    tracker.add_log_msg(f"Total raw posts scraped: {len(state.raw_posts)}.")
    logger.info(
        "Scraped %s posts total (Reddit: %s, Quora: %s, HN: %s)",
        len(state.raw_posts),
        len(reddit_posts),
        len(quora_posts),
        len(hn_posts),
    )
    return state

def dedup_node(state: PipelineState) -> PipelineState:
    logger.info("Deduplicating posts")
    tracker.update_step("Deduplicating posts against existing database entries...", 35)
    new_posts = supabase_tool.check_duplicates(state.raw_posts)
    state.deduplicated_posts = new_posts
    removed_count = len(state.raw_posts) - len(new_posts)
    tracker.add_log_msg(f"Deduplication finished. Removed {removed_count} duplicates. {len(new_posts)} new posts to analyze.")
    logger.info("%s duplicates removed. %s new posts to analyze.", removed_count, len(new_posts))
    return state

def analyze_node(state: PipelineState) -> PipelineState:
    logger.info("Scoring posts before AI analysis")
    tracker.update_step("Running heuristic filters on posts...", 50)
    analyzed_ideas = []
    scored_posts = sorted(
        ((post, _heuristic_score(post)) for post in state.deduplicated_posts),
        key=lambda item: item[1],
        reverse=True,
    )
    candidates = [(post, score) for post, score in scored_posts if score >= MIN_TOTAL_SCORE]

    if not candidates:
        tracker.add_log_msg("No posts passed the cheap heuristic filter.")
        logger.info("No posts passed the cheap heuristic filter.")
        state.analyzed_ideas = []
        return state

    can_use_ai = AI_ANALYSIS_ENABLED and bool(AI_PROVIDER_KEY) and MAX_AI_POSTS_PER_RUN > 0
    ai_candidates = candidates[:MAX_AI_POSTS_PER_RUN] if can_use_ai else []
    manual_candidates = candidates[len(ai_candidates):]

    tracker.add_log_msg(
        f"Heuristic filter kept {len(candidates)}/{len(state.deduplicated_posts)} posts. "
        f"Configured AI provider={AI_PROVIDER}. AI analyzing top {len(ai_candidates)} candidates."
    )
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
        for idx, (post, _score) in enumerate(batch):
            current_index = i + idx + 1
            progress_val = 50 + int((current_index / len(ai_candidates)) * 30)
            tracker.update_step(f"AI Analyzing candidate {current_index}/{len(ai_candidates)}: {post.title[:40]}...", progress_val)
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
                    tracker.add_log_msg(f"→ Pain point identified: '{idea_record.problem_summary}' (Score: {idea_record.total_score}/30)")
                    # Instant notification for high-scoring ideas
                    if idea_record.total_score >= 25:
                        tracker.add_log_msg(f"High opportunity score ({idea_record.total_score}/30). Triggering webhooks...")
                        webhook_tool.notify_all(idea_record)
                else:
                    tracker.add_log_msg(f"→ Evaluated: Not a high-potential pain point (reasoning filtered).")
            except Exception as e:
                logger.exception("Error analyzing post %s", post.url)
                state.errors.append(f"Analysis error for {post.url}: {str(e)}")
                tracker.add_log_msg(f"Error analyzing post {post.url}: {str(e)}")

    if SAVE_MANUAL_CANDIDATES:
        remaining_slots = max(0, MAX_MANUAL_CANDIDATES_PER_RUN - len(analyzed_ideas))
        if remaining_slots > 0 and manual_candidates:
            tracker.add_log_msg(f"Saving {min(remaining_slots, len(manual_candidates))} manual candidates for manual review.")
        for post, score in manual_candidates[:remaining_slots]:
            analyzed_ideas.append(_manual_candidate_record(post, score))

    state.analyzed_ideas = analyzed_ideas
    logger.info("%s ideas passed the filter.", len(analyzed_ideas))
    return state

def save_node(state: PipelineState) -> PipelineState:
    logger.info("Saving ideas")
    tracker.update_step("Saving validated ideas to database...", 85)
    if state.analyzed_ideas:
        saved_count = supabase_tool.save_ideas(state.analyzed_ideas)
        state.saved_count = saved_count
        tracker.set_stats(saved=saved_count)
        tracker.add_log_msg(f"Successfully saved {saved_count} ideas to Supabase.")
        logger.info("Saved %s new ideas to database.", saved_count)
    else:
        tracker.add_log_msg("No ideas to save.")
        logger.info("No ideas to save.")
    return state

def should_continue_after_dedup(state: PipelineState):
    if not state.deduplicated_posts:
        return "end"
    return "analyze"

def should_continue_after_analyze(state: PipelineState):
    if not state.analyzed_ideas:
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
    tracker.start_run()
    try:
        graph = build_graph()
        initial_state = PipelineState()
        final_state_dict = graph.invoke(initial_state)
        # LangGraph invoke returns a dict if the state is a Pydantic model/TypedDict
        final_state = PipelineState(**final_state_dict)
        tracker.complete_run(saved_count=final_state.saved_count)
        return final_state
    except Exception as e:
        logger.exception("Pipeline run failed")
        tracker.complete_run(saved_count=0, error_msg=str(e))
        raise e
