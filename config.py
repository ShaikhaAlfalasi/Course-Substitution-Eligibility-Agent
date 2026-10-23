
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def validate_config():
    required = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "GEMINI_API_KEY": GEMINI_API_KEY,
    }

    missing = [
        name for name, value in required.items()
        if not value or value.startswith("your_")
    ]

    if missing:
        raise ValueError(
            f"Missing or invalid environment variables: {', '.join(missing)}"
        )