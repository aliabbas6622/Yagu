import os
import sys

# Add the parent directory so product_idea_miner imports resolve when this
# script is run from either the repo root or its parent folder.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from product_idea_miner.config import models, settings
    from product_idea_miner.tools import reddit_tool, tinyfish_tool, supabase_tool, email_tool
    from product_idea_miner.agents import crewai_crew, langgraph_pipeline, adk_orchestrator
    from google.adk import Agent
    print("All modules imported successfully!")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)
