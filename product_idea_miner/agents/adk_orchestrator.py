import time
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from google.adk import Agent
from google.adk.tools import FunctionTool
from product_idea_miner.agents.langgraph_pipeline import run_pipeline
from product_idea_miner.tools import supabase_tool, email_tool, export_tool
from product_idea_miner.config.settings import (
    ORCHESTRATOR_MODEL,
    RUN_INTERVAL_HOURS,
    TOP_IDEAS_PER_DIGEST,
    RECIPIENT_EMAIL
)

logger = logging.getLogger(__name__)

def pipeline_task():
    """
    Function to be called by ADK or Scheduler to run the pipeline.
    """
    logger.info("Starting pipeline task")
    try:
        final_state = run_pipeline()
        return f"Pipeline completed. Scraped: {len(final_state.raw_posts)}, Saved: {final_state.saved_count}"
    except Exception as e:
        return f"Pipeline failed: {str(e)}"

def digest_task():
    """
    Function to be called by ADK or Scheduler to send the daily digest.
    """
    logger.info("Starting digest task")
    try:
        ideas = supabase_tool.get_unsent_ideas(limit=TOP_IDEAS_PER_DIGEST)
        if ideas:
            # Send Email
            success = email_tool.send_digest_email(ideas, RECIPIENT_EMAIL)

            # Export for backup
            today = datetime.now().strftime("%Y-%m-%d")
            export_tool.export_to_json(ideas, f"digest_{today}.json")
            export_tool.export_to_csv(ideas, f"digest_{today}.csv")

            if success:
                idea_ids = [idea.id for idea in ideas if idea.id]
                supabase_tool.mark_as_sent(idea_ids)
                return f"Digest sent and exported with {len(ideas)} ideas."
            else:
                return "Failed to send digest email, but exported locally."
        else:
            return "No new ideas for digest."
    except Exception as e:
        return f"Digest task failed: {str(e)}"

def build_orchestrator():
    # Define tools for the orchestrator
    tools = [
        FunctionTool(pipeline_task, name="run_pipeline_tool", description="Runs the scrape-to-store pipeline"),
        FunctionTool(digest_task, name="send_digest_tool", description="Sends the daily digest email")
    ]

    # Root Orchestrator Agent
    orchestrator = Agent(
        name="ProductIdeaMinerOrchestrator",
        model=ORCHESTRATOR_MODEL,
        instructions=(
            "You are an orchestrator for a product idea mining system. "
            "Your job is to: "
            "1. Run the scraping pipeline every 6 hours. "
            "2. Send a daily digest of top ideas every morning. "
            "3. Log all outcomes clearly. "
            "If any task fails, log the error and continue."
        ),
        tools=tools
    )
    return orchestrator

def run_orchestrator_command(command: str):
    """
    Tells the ADK orchestrator agent to perform a specific action.
    """
    orchestrator = build_orchestrator()
    logger.info("Orchestrator received command: %s", command)
    # In a real ADK setup, you might use a Runner or a Session.
    # Here we use a simple run call to let the agent decide which tool to call.
    response = orchestrator.run(command)
    # response is a list of Messages, the last one is the agent's final answer
    if response:
        logger.info("Orchestrator response: %s", response[-1].text)

def main():
    scheduler = BackgroundScheduler()

    # Schedule Pipeline every X hours via the Orchestrator Agent
    scheduler.add_job(
        run_orchestrator_command,
        'interval',
        args=["Run the scraping pipeline now."],
        hours=RUN_INTERVAL_HOURS
    )

    # Schedule Digest every day at 8:00 AM via the Orchestrator Agent
    scheduler.add_job(
        run_orchestrator_command,
        'cron',
        args=["Send the daily digest of top ideas."],
        hour=8,
        minute=0
    )

    scheduler.start()
    logger.info("Product Idea Miner is running... (Pipeline every %sh, Digest at 08:00)", RUN_INTERVAL_HOURS)

    # Also run once on startup for development/verification
    # print("Running initial pipeline on startup...")
    # pipeline_task()

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
