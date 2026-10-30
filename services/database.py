from functools import lru_cache
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from config import DATABASE_URL


def _normalize_database_url(url: str) -> str:

    if url.startswith("postgres://"):

        url = url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    if url.startswith("postgresql://"):

        url = url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    return url


@lru_cache(maxsize=1)
def get_engine() -> Engine:

    if not DATABASE_URL:

        raise RuntimeError(
            "DATABASE_URL is missing from .env"
        )

    engine = create_engine(
        _normalize_database_url(DATABASE_URL),
        pool_pre_ping=True,
        connect_args={
            "sslmode": "require"
        }
    )

    @event.listens_for(engine, "connect")
    def set_read_only(
        dbapi_connection,
        connection_record
    ):

        with dbapi_connection.cursor() as cursor:

            cursor.execute(
                "SET default_transaction_read_only = on"
            )

    return engine


def get_connection():

    try:

        return get_engine().connect()

    except SQLAlchemyError as exc:

        raise RuntimeError(
            f"Database connection failed: {exc}"
        ) from exc


def get_current_term():

    """
    Academic term mapping:
    August-December = Fall
    January-May = Spring
    June-July = Unknown
    """

    today = datetime.now(
        ZoneInfo("Asia/Dubai")
    )

    if 8 <= today.month <= 12:

        return int(
            f"{today.year}01"
        )

    if 1 <= today.month <= 5:

        return int(
            f"{today.year - 1}02"
        )

    return None


def get_course_substitution_request(request_id: str):

    """
    Retrieve the information required to evaluate
    a Course Substitution request.

    The agent only reads data from Supabase.
    Course offerings are NOT retrieved from the database.
    """

    if not request_id or not request_id.strip():

        raise ValueError(
            "Request ID cannot be empty."
        )

    request_id = request_id.strip()

    # -----------------------------------------------------
    # DATABASE QUERIES
    # -----------------------------------------------------

    queries = {

        "request": text('''
            SELECT
                "Request_ID",
                "Request_Type",
                "Request_Date",
                "Submission_Time",
                "Description",
                "Current_Status",
                "Student_ID"
            FROM public."Request"
            WHERE "Request_ID" = :rid
              AND "Request_Type" = 'Course Substitution'
        '''),

        "substitution": text('''
            SELECT
                "Original_Course_ID",
                "Proposed_Course_ID",
                "Reason"
            FROM public."Course_Substitution"
            WHERE "Request_ID" = :rid
            LIMIT 1
        '''),

        "student": text('''
            SELECT
                "Student_ID",
                "Student_Name",
                "Student_Email",
                "CGPA",
                "Completed_Hours",
                "Program_ID",
                "Program_Name",
                "Expected_Graduation_Term"
            FROM public."Student"
            WHERE "Student_ID" = :sid
        '''),

        "course": text('''
            SELECT
                "Course_ID",
                "Course_Name",
                "Credit_Hours"
            FROM public."Course"
            WHERE "Course_ID" = :cid
        '''),

        "completion": text('''
            SELECT DISTINCT
                "Course_ID"
            FROM public."Takes"
            WHERE "Student_ID" = :sid
              AND "Course_ID" IN (:original, :proposed)
              AND "Grade" IN (
                  'A',
                  'B+',
                  'B',
                  'C+',
                  'C',
                  'D+',
                  'D'
              )
        ''')
    }

    try:

        with get_connection() as conn:

            # Retrieve request
            request_row = conn.execute(
                queries["request"],
                {"rid": request_id}
            ).mappings().first()

            if request_row is None:

                return None

            request_data = dict(request_row)

            student_id = request_data["Student_ID"]

            # Retrieve substitution details
            substitution_row = conn.execute(
                queries["substitution"],
                {"rid": request_id}
            ).mappings().first()

            if substitution_row is None:

                raise ValueError(
                    f"Course Substitution details not found "
                    f"for request {request_id}."
                )

            substitution_data = dict(
                substitution_row
            )

            original_id = substitution_data[
                "Original_Course_ID"
            ]

            proposed_id = substitution_data[
                "Proposed_Course_ID"
            ]

            # Retrieve student information
            student_row = conn.execute(
                queries["student"],
                {"sid": student_id}
            ).mappings().first()

            if student_row is None:

                raise ValueError(
                    f"Student {student_id} was not found."
                )

            student_data = dict(student_row)

            # Retrieve original course information
            original_row = conn.execute(
                queries["course"],
                {"cid": original_id}
            ).mappings().first()

            # Retrieve proposed course information
            proposed_row = conn.execute(
                queries["course"],
                {"cid": proposed_id}
            ).mappings().first()

            if original_row is None:

                raise ValueError(
                    f"Original course {original_id} was not found."
                )

            if proposed_row is None:

                raise ValueError(
                    f"Proposed course {proposed_id} was not found."
                )

            # Check whether either course was completed
            # with a passing grade
            completed_rows = conn.execute(
                queries["completion"],
                {
                    "sid": student_id,
                    "original": original_id,
                    "proposed": proposed_id
                }
            ).mappings().all()

            completed_ids = {
                row["Course_ID"]
                for row in completed_rows
            }

        # -------------------------------------------------
        # RETURN REQUIRED INFORMATION
        # -------------------------------------------------

        return {

            "request_id": request_data["Request_ID"],

            "request_type": request_data["Request_Type"],

            "request_date": request_data["Request_Date"],

            "submission_time": request_data["Submission_Time"],

            "description": request_data["Description"],

            "current_status": request_data["Current_Status"],

            "student": {

                "student_id": student_data["Student_ID"],

                "student_name": student_data["Student_Name"],

                "student_email": student_data["Student_Email"],

                "cgpa": student_data["CGPA"],

                "completed_hours": student_data["Completed_Hours"],

                "program_id": student_data["Program_ID"],

                "program_name": student_data["Program_Name"],

                "expected_graduation_term":
                    student_data["Expected_Graduation_Term"]
            },

            "original_course": {

                "course_id": original_row["Course_ID"],

                "course_name": original_row["Course_Name"],

                "credit_hours": original_row["Credit_Hours"]
            },

            "proposed_course": {

                "course_id": proposed_row["Course_ID"],

                "course_name": proposed_row["Course_Name"],

                "credit_hours": proposed_row["Credit_Hours"]
            },

            "reason": substitution_data["Reason"],

            "course_completion": {

                "original_course_completed":
                    original_id in completed_ids,

                "proposed_course_completed":
                    proposed_id in completed_ids
            },

            "current_term": get_current_term()
        }

    except (SQLAlchemyError, ValueError) as exc:

        if isinstance(exc, ValueError):

            raise

        raise RuntimeError(
            f"Failed to retrieve Course Substitution request: {exc}"
        ) from exc