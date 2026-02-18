"""
Configuration settings for the Business AI Copilot.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.1"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))

# Jira Configuration
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

# Vector Database Configuration
CHROMA_PERSIST_DIRECTORY = os.getenv(
    "CHROMA_PERSIST_DIRECTORY", 
    str(BASE_DIR / "data" / "chroma_db")
)

# Application Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Tool Configurations
TOOL_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
CACHE_TTL_SECONDS = 300  # 5 minutes

# Validation Settings
MIN_CONFIDENCE_THRESHOLD = 0.7
ENABLE_FACTUAL_VERIFICATION = True

# Create necessary directories
Path(CHROMA_PERSIST_DIRECTORY).mkdir(parents=True, exist_ok=True)