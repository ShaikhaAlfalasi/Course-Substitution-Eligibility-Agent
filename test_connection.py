
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is missing from .env")

with psycopg.connect(database_url, sslmode="require") as conn:
    with conn.cursor() as cur:
        # Confirm which database role is connected.
        cur.execute("SELECT current_user")
        print("Connected role:", cur.fetchone()[0])

        # Verify direct table access is denied.
        try:
            cur.execute('SELECT * FROM public."Request" LIMIT 1')
            print("WARNING: Direct table access succeeded.")
        except psycopg.errors.InsufficientPrivilege:
            conn.rollback()
            print("Direct table access correctly denied.")

        # Verify that the RPC can be executed.
        request_id = input("Enter a test Course Substitution Request ID: ")

        cur.execute(
            """
            SELECT public.get_course_substitution_request(%s)
            """,
            (request_id,)
        )

        result = cur.fetchone()[0]
        print("RPC returned data:", result is not None)
