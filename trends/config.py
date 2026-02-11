"""
Trend Monitor — Configuration
All targets, sources, and scoring weights in one place.
"""

# ── Reddit: subreddits grouped by domain ──────────────────────────────────────
SUBREDDITS = {
    "tech": [
        "technology", "programming", "machinelearning", "artificial",
        "webdev", "devops", "datascience", "ChatGPT",
    ],
    "business": [
        "entrepreneur", "startups", "smallbusiness", "marketing",
        "SideProject", "passive_income",
    ],
    "finance": [
        "investing", "CryptoCurrency", "wallstreetbets", "personalfinance",
        "stocks",
    ],
    "science": [
        "science", "Futurology", "space", "biotech",
    ],
    "lifestyle": [
        "selfimprovement", "productivity", "getdisciplined",
        "LifeProTips", "Fitness",
    ],
    "creative": [
        "filmmaking", "videography", "youtubers", "NewTubers",
        "ContentCreation",
    ],
}

# Flattened list for scraping
ALL_SUBREDDITS = [sub for group in SUBREDDITS.values() for sub in group]

# ── YouTube categories ────────────────────────────────────────────────────────
# YouTube RSS category IDs (used for Invidious trending endpoint)
YOUTUBE_CATEGORIES = {
    "default": "",        # Overall trending
    "music": "Music",
    "gaming": "Gaming",
    "film": "Film",
    "science": "Science",
    "technology": "Technology",
}

# Invidious public instances (rotate to avoid rate limits)
INVIDIOUS_INSTANCES = [
    "https://vid.puffyan.us",
    "https://invidious.fdn.fr",
    "https://invidious.nerdvpn.de",
    "https://inv.nadeko.net",
    "https://invidious.privacyredirect.com",
]

# ── Google Trends ─────────────────────────────────────────────────────────────
GOOGLE_TRENDS_GEO = ""           # Empty = worldwide, "US" = United States, etc.
GOOGLE_TRENDS_LANGUAGE = "en-US"

# ── Hacker News ───────────────────────────────────────────────────────────────
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
HN_TOP_LIMIT = 60     # How many top stories to fetch
HN_NEW_LIMIT = 30     # How many new stories to fetch

# ── Nitter / Twitter ─────────────────────────────────────────────────────────
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.cz",
]

# Twitter/X search terms to monitor (trends page + specific searches)
TWITTER_SEARCH_TERMS = [
    "trending", "viral", "AI", "startup", "creator economy",
]

# ── Scoring Weights ───────────────────────────────────────────────────────────
# Used by analyze.py to rank opportunities
WEIGHTS = {
    "cross_platform_presence": 3.0,   # Topic appears on multiple platforms
    "velocity": 2.5,                  # How fast it's growing
    "low_competition": 2.0,           # Few YouTube videos on topic
    "recency": 1.5,                   # How recent the trend is
    "community_bridge": 2.0,          # Spans disconnected communities
}

# ── Personal Interest Tags ────────────────────────────────────────────────────
# Topics you care about — boosts relevance score for matching trends
INTEREST_TAGS = [
    "AI", "automation", "content creation", "passive income",
    "SaaS", "open source", "productivity", "creator tools",
    "machine learning", "side hustle", "no-code", "indie hacking",
]

# ── Output Paths ──────────────────────────────────────────────────────────────
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# Ensure dirs exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
