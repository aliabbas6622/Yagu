"""
main.py - starts the whole system (Orchestrator + API).
Run: python product_idea_miner/main.py
"""
import os
import sys
import threading
import uvicorn

# Add the parent directory of product_idea_miner to sys.path.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from product_idea_miner.config.logging_config import configure_logging
from product_idea_miner.agents.adk_orchestrator import main as run_orchestrator

def start_api():
    uvicorn.run("product_idea_miner.api:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    configure_logging()

    # Start API in a separate thread
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # Start the orchestrator (this will block until interrupted)
    run_orchestrator()
