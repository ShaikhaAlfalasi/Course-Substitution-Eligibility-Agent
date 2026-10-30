from sqlalchemy import text
from services.database import get_connection


def test_connection():
    try:
        with get_connection() as conn:

            print(
                "Connected role:",
                conn.execute(
                    text("SELECT current_user")
                ).scalar()
            )

            query = text("""
                SELECT
                    "Student_ID",
                    "Course_ID",
                    "Grade",
                    "Section_ID",
                    "Term"
                FROM public."Takes"
                WHERE "Student_ID" = :sid
                ORDER BY "Term", "Course_ID"
            """)

            results = conn.execute(
                query,
                {"sid": "U22299999"}
            ).mappings().all()

            print(f"\nTranscript records retrieved: {len(results)}")

            for record in results:
                print(dict(record))

    except Exception as e:
        print(f"\nDatabase test failed: {e}")


if __name__ == "__main__":
    test_connection()
    