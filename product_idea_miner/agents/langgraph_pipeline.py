import asyncio
from datetime import datetime
from typing import List
from langgraph.graph import StateGraph, END
from product_idea_miner.config.models import PipelineState, IdeaRecord
from product_idea_miner.config.settings import SUBREDDITS, PAIN_POINT_KEYWORDS, QUORA_SEARCHES, MIN_TOTAL_SCORE
from product_idea_miner.tools import reddit_tool, tinyfish_tool, supabase_tool, hn_tool, webhook_tool
from product_idea_miner.agents import crewai_crew

def scrape_node(state: PipelineState) -> PipelineState:
    print("--- SCRAPING ---")
    reddit_posts = reddit_tool.scrape_reddit(SUBREDDITS, PAIN_POINT_KEYWORDS)
    quora_posts = tinyfish_tool.scrape_quora(QUORA_SEARCHES)
    hn_posts = hn_tool.scrape_hn()

    state.raw_posts = reddit_posts + quora_posts + hn_posts
    print(f"Scraped {len(state.raw_posts)} posts total (Reddit: {len(reddit_posts)}, Quora: {len(quora_posts)}, HN: {len(hn_posts)}).")
    return state

def dedup_node(state: PipelineState) -> PipelineState:
    print("--- DEDUPLICATING ---")
    new_posts = supabase_tool.check_duplicates(state.raw_posts)
    state.deduplicated_posts = new_posts
    print(f"{len(state.raw_posts) - len(new_posts)} duplicates removed. {len(new_posts)} new posts to analyze.")
    return state

def analyze_node(state: PipelineState) -> PipelineState:
    print("--- ANALYZING ---")
    analyzed_ideas = []

    # Process in small batches to avoid rate limits and too many concurrent LLM calls
    batch_size = 5
    for i in range(0, len(state.deduplicated_posts), batch_size):
        batch = state.deduplicated_posts[i:i+batch_size]

        # CrewAI is generally not async-friendly out of the box for sequential processes,
        # but we can run them in parallel if needed. For now, sequential per post.
        for post in batch:
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
                print(f"Error analyzing post {post.url}: {e}")
                state.errors.append(f"Analysis error for {post.url}: {str(e)}")

    state.analyzed_ideas = analyzed_ideas
    print(f"{len(analyzed_ideas)} ideas passed the filter.")
    return state

def save_node(state: PipelineState) -> PipelineState:
    print("--- SAVING ---")
    if state.analyzed_ideas:
        saved_count = supabase_tool.save_ideas(state.analyzed_ideas)
        state.saved_count = saved_count
        print(f"Saved {saved_count} new ideas to database.")
    else:
        print("No ideas to save.")
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
    graph = build_graph()
    initial_state = PipelineState()
    final_state_dict = graph.invoke(initial_state)
    # LangGraph invoke returns a dict if the state is a Pydantic model/TypedDict
    return PipelineState(**final_state_dict)
