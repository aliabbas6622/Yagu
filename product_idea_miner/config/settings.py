from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Reddit
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_username: str | None = None
    reddit_password: str | None = None
    reddit_user_agent: str = "ProductIdeaMiner/1.0"
    reddit_use_scrapling_fallback: bool = True

    # TinyFish
    tinyfish_api_key: str | None = None
    quora_scrape_enabled: bool = False
    startup_scrape_enabled: bool = True

    # AI providers
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    gemini_api_1: str | None = None
    gemini_api_2: str | None = None
    gemini_api_3: str | None = None
    openrouter_api_key: str | None = None
    openrouter_1: str | None = None
    openrouter_2: str | None = None
    xai_api_key: str | None = None
    groq_api_key: str | None = None
    groq_api_1: str | None = None
    groq_api_2: str | None = None
    openai_api_key: str | None = None
    ai_provider: str = "anthropic"
    ai_model: str | None = None
    ai_analysis_enabled: bool = True
    max_ai_posts_per_run: int = 1
    save_manual_candidates: bool = True
    max_manual_candidates_per_run: int = 20
    orchestrator_model: str = "gemini-2.0-flash"

    # Supabase
    supabase_url: str | None = None
    supabase_key: str | None = None
    supabase_secret_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_publishable_key: str | None = None
    supabase_anon_key: str | None = None

    # Email
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    recipient_email: str | None = None

    # Webhooks
    discord_webhook_url: str | None = None
    slack_webhook_url: str | None = None

    # Tunable settings
    run_interval_hours: int = 6
    min_upvotes: int = 10
    min_total_score: int = 15
    top_ideas_per_digest: int = 10

    # Reliability
    log_level: str = "INFO"
    request_timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_wait_seconds: int = 2
    llm_analysis_retries: int = 1

settings = AppSettings()

# Reddit
REDDIT_CLIENT_ID = settings.reddit_client_id
REDDIT_CLIENT_SECRET = settings.reddit_client_secret
REDDIT_USERNAME = settings.reddit_username
REDDIT_PASSWORD = settings.reddit_password
REDDIT_USER_AGENT = settings.reddit_user_agent
REDDIT_USE_SCRAPLING_FALLBACK = settings.reddit_use_scrapling_fallback

# TinyFish
TINYFISH_API_KEY = settings.tinyfish_api_key
QUORA_SCRAPE_ENABLED = settings.quora_scrape_enabled
STARTUP_SCRAPE_ENABLED = settings.startup_scrape_enabled

STARTUP_SOURCES = [
    {"country": "India", "url": "https://www.startupindia.gov.in"},
    {"country": "UK", "url": "https://technation.io"},
    {"country": "Nordics", "url": "https://thehub.io"},
    {"country": "Europe", "url": "https://www.eu-startups.com/directory"},
    {"country": "Global", "url": "https://fi.co"},
    {"country": "Global", "url": "https://www.startupblink.com"},
]

# AI provider keys
ANTHROPIC_API_KEY = settings.anthropic_api_key
GEMINI_API_KEY = settings.gemini_api_key or settings.gemini_api_1 or settings.gemini_api_2 or settings.gemini_api_3
OPENROUTER_API_KEY = settings.openrouter_api_key or settings.openrouter_1 or settings.openrouter_2
XAI_API_KEY = settings.xai_api_key
GROQ_API_KEY = settings.groq_api_key or settings.groq_api_1 or settings.groq_api_2
OPENAI_API_KEY = settings.openai_api_key

# AI model provider for CrewAI/LiteLLM analysis.
# Override AI_MODEL directly for any LiteLLM-supported provider/model string.
def _auto_ai_provider() -> str:
    requested = settings.ai_provider.strip().lower()
    if requested != "anthropic" or ANTHROPIC_API_KEY:
        return requested
    if GEMINI_API_KEY:
        return "gemini"
    if GROQ_API_KEY:
        return "groq"
    if OPENROUTER_API_KEY:
        return "openrouter"
    if XAI_API_KEY:
        return "xai"
    if OPENAI_API_KEY:
        return "openai"
    return requested

AI_PROVIDER = _auto_ai_provider()
AI_PROVIDER_DEFAULT_MODELS = {
    "anthropic": "anthropic/claude-3-5-sonnet-20241022",
    "gemini": "gemini/gemini-2.0-flash",
    "openrouter": "openrouter/google/gemini-2.5-flash",
    "grok": "xai/grok-4.3",
    "xai": "xai/grok-4.3",
    "groq": "groq/llama-3.3-70b-versatile",
    "openai": "openai/gpt-4o-mini",
}
AI_MODEL = settings.ai_model or AI_PROVIDER_DEFAULT_MODELS.get(AI_PROVIDER)
AI_PROVIDER_KEYS = {
    "anthropic": ANTHROPIC_API_KEY,
    "gemini": GEMINI_API_KEY,
    "openrouter": OPENROUTER_API_KEY,
    "grok": XAI_API_KEY,
    "xai": XAI_API_KEY,
    "groq": GROQ_API_KEY,
    "openai": OPENAI_API_KEY,
}
AI_PROVIDER_KEY = AI_PROVIDER_KEYS.get(AI_PROVIDER)
AI_ANALYSIS_ENABLED = settings.ai_analysis_enabled
MAX_AI_POSTS_PER_RUN = settings.max_ai_posts_per_run
SAVE_MANUAL_CANDIDATES = settings.save_manual_candidates
MAX_MANUAL_CANDIDATES_PER_RUN = settings.max_manual_candidates_per_run
ORCHESTRATOR_MODEL = settings.orchestrator_model

# Supabase
SUPABASE_URL = settings.supabase_url
SUPABASE_KEY = (
    settings.supabase_key
    or settings.supabase_secret_key
    or settings.supabase_service_role_key
    or settings.supabase_publishable_key
    or settings.supabase_anon_key
)

# Email
SMTP_HOST = settings.smtp_host
SMTP_PORT = settings.smtp_port
SMTP_USER = settings.smtp_user
SMTP_PASSWORD = settings.smtp_password
RECIPIENT_EMAIL = settings.recipient_email

# Webhooks
DISCORD_WEBHOOK_URL = settings.discord_webhook_url
SLACK_WEBHOOK_URL = settings.slack_webhook_url

# Tunable settings
RUN_INTERVAL_HOURS = settings.run_interval_hours
MIN_UPVOTES = settings.min_upvotes
MIN_TOTAL_SCORE = settings.min_total_score
TOP_IDEAS_PER_DIGEST = settings.top_ideas_per_digest

# Reliability
LOG_LEVEL = settings.log_level.upper()
REQUEST_TIMEOUT_SECONDS = settings.request_timeout_seconds
RETRY_ATTEMPTS = settings.retry_attempts
RETRY_WAIT_SECONDS = settings.retry_wait_seconds
LLM_ANALYSIS_RETRIES = settings.llm_analysis_retries

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
