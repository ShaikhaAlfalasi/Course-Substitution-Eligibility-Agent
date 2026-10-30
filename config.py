import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def validate_config():
    required = {
        "DATABASE_URL": DATABASE_URL,
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