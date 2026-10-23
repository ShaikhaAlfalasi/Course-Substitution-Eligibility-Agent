
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")


def get_course_substitution_request(request_id):
    """
    Retrieve a Course Substitution request and its supporting
    student, course, transcript, and offering information.

    Uses the restricted PostgreSQL role and approved read-only RPC.
    Returns the request as a dictionary, or None if not found.
    """

    if not request_id or not request_id.strip():
        raise ValueError("Request ID cannot be empty.")

    query = """
        SELECT public.get_course_substitution_request(%s);
    """

    with psycopg.connect(
        DATABASE_URL,
        sslmode="require",
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (request_id.strip(),))
            row = cur.fetchone()

    if row is None or row[0] is None:
        return None

    return row[0]
