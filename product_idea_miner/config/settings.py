import os
from dotenv import load_dotenv

load_dotenv()

# Reddit
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ProductIdeaMiner/1.0")

# TinyFish
TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Email
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Webhooks
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Tunable settings
RUN_INTERVAL_HOURS = int(os.getenv("RUN_INTERVAL_HOURS", 6))
MIN_UPVOTES = int(os.getenv("MIN_UPVOTES", 10))
MIN_TOTAL_SCORE = int(os.getenv("MIN_TOTAL_SCORE", 15))
TOP_IDEAS_PER_DIGEST = int(os.getenv("TOP_IDEAS_PER_DIGEST", 10))

# Scraper Config
SUBREDDITS = ["SaaS", "SideProject", "startups", "Entrepreneur", "BusinessIdeas"]
PAIN_POINT_KEYWORDS = [
    "I wish there was a tool for",
    "why is there no app that",
    "frustrated with",
    "pain in the neck",
    "hard to manage",
    "manual process",
    "takes too much time"
]

QUORA_SEARCHES = [
    "I wish there was a tool for",
    "why is there no app that",
    "best software for small business problems",
    "I need a tool that can",
    "frustrated with current tools"
]
