"""
main.py - starts the whole system.
Run: python main.py
"""
import os
import sys

# Add the parent directory of product_idea_miner to sys.path.
# This allows 'from product_idea_miner.xxx' style imports to work correctly.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from product_idea_miner.config.logging_config import configure_logging
from product_idea_miner.agents.adk_orchestrator import main

if __name__ == "__main__":
    configure_logging()
    main()
