"""
main.py — starts the whole system.
Run: python main.py
"""
import sys
import os

# Add the parent directory of product_idea_miner to sys.path
# This allows 'from product_idea_miner.xxx' style imports to work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from product_idea_miner.agents.adk_orchestrator import main

if __name__ == "__main__":
    print("🚀 Starting Product Idea Miner...")
    print("Scraping Reddit + Quora every 6 hours")
    print("Daily digest at 8:00 AM")
    main()
