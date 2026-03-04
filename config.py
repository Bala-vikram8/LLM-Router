import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DB_PATH = os.environ.get("DB_PATH", "llm_router.db")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not set. Add it to your .env file.")
