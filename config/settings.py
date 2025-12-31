"""
Application configuration settings for Vach
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if exists
ENV_PATH = Path(".") / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# === Database === #
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/vach.db")

# Ensure DB directory exists
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

# === LLM Model / Ollama === #
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")

OLLAMA_API_URL = f"{OLLAMA_HOST}:{OLLAMA_PORT}"
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# === Logging === #
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR_PATH = os.getenv("LOG_DIR_PATH", "logs")

# === Scraper / Network defaults === #
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
# Use a realistic browser User-Agent by default to reduce 403s from some sites
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Debug mode for scrapers: when enabled, skip keyword relevance filtering so
# a few articles are persisted for testing. Set SCRAPER_DEBUG=1 in .env to enable.
SCRAPER_DEBUG = os.getenv("SCRAPER_DEBUG", "0") == "1"

# === Target / Keywords === #
TARGET_CITY = os.getenv("TARGET_CITY", "San Jose")
PROJECT_TYPES = [
    "housing", "transit", "infrastructure", "parks", "public_safety", "other"
]

# RSS feeds and keywords (simple defaults; override via .env if needed)
RSS_FEEDS = [
    "https://www.mercurynews.com/feed/", 
    "https://sanjosespotlight.com/feed/"
]
PROJECT_KEYWORDS = [
    "project", "construction", "approved", "council", "budget", "housing", "infrastructure"
]
MAX_ARTICLES_PER_SOURCE = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "20"))

# Government sources
SAN_JOSE_PRESS_URL = os.getenv("SAN_JOSE_PRESS_URL", "https://www.sanjoseca.gov/Home/Components/News/")
SAN_JOSE_OPEN_DATA_URL = os.getenv("SAN_JOSE_OPEN_DATA_URL", "https://data.sanjoseca.gov")
