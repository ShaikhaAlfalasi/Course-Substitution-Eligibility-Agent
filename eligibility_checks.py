
from datetime import date
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"
REQUIRES_REVIEW = "REQUIRES_REVIEW"

ELIGIBLE = "ELIGIBLE"
NOT_ELIGIBLE = "NOT_ELIGIBLE"

KNOWLEDGE_BASE_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "course_offerings_knowledge_base.txt"
)

PASSING_GRADES = {
    "A+", "A", "A-", "B+", "B", "B-",
    "C+", "C", "C-", "D+", "D", "D-",
    "P", "PASS",
}

NON_COMPLETION_GRADES = {"F", "WF", "W", "WD", "NP"}

INCOMPLETE_GRADES = {"I", "IP", "INC", "INCOMPLETE"}


# =========================================================
# GENERAL HELPERS
# =========================================================

def make_check(condition, status, evidence):
    return {
        "condition": condition,
        "status": status,
        "evidence": evidence,
    }


def parse_term(term):
    """Validate a Fall/Spring academic term code."""
    text = str(term or "").strip()

    if len(text) != 6 or not text.isdigit():
        return None

    year = int(text[:4])
    semester_code = int(text[4:])

    if semester_code not in (1, 2):
        return None

    return year, semester_code


def term_order(term):
    """Return a value that preserves academic term chronology."""
    parsed = parse_term(term)

    if parsed is None:
        return None

    year, semester_code = parsed
    return year * 2 + semester_code - 1


def term_to_semester(term):
    parsed = parse_term(term)

    if parsed is None:
        return None

    return "Fall" if parsed[1] == 1 else "Spring"


def next_term(term):
    """Return the next Fall/Spring term."""
    parsed = parse_term(term)

    if parsed is None:
        return None

    year, semester_code = parsed

    if semester_code == 1:
        return year * 100 + 2

    return (year + 1) * 100 + 1


def get_current_term(today=None):
    """
    Determine the current academic term using approximate
    calendar boundaries.

    January-May: Spring
    August-December: Fall
    June-July: Unknown

    Adjust these boundaries if the official university
    academic calendar requires different dates.
    """
    today = today or date.today()

    if 1 <= today.month <= 5:
        return (today.year - 1) * 100 + 2

    if 8 <= today.month <= 12:
        return today.year * 100 + 1

    return None


def valid_course_id(course_id):
    text = str(course_id or "").strip()
    return len(text) == 7 and text.isdigit()


# =========================================================
# LOAD COURSE OFFERINGS KNOWLEDGE BASE
# =========================================================

def load_course_knowledge_base(file_path=None):
    """
    Load course offerings from the knowledge base.

    Supports rows with leading and trailing pipes, such as:
    | 1501372 | Formal Languages and Automata Theory | No | Yes | No |

    This function handles course offerings only.
    Gemini verifies whether a course is compulsory or elective.
    """
    path = Path(file_path) if file_path else KNOWLEDGE_BASE_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Course offerings knowledge base not found: {path}"
        )

    courses = {}

    with path.open("r", encoding="utf-8-sig") as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line or "|" not in line:
                continue

            # Remove outer pipes before splitting into columns.
            line = line.strip("|").strip()
            parts = [part.strip() for part in line.split("|")]

            # Expected columns:
            # Course ID | Course Name | Fall | Spring | Summer
            if len(parts) != 5:
                continue

            course_id, course_name, fall, spring, summer = parts

            # Ignore headings, section titles, and other non-course rows.
            if not valid_course_id(course_id):
                continue

            def normalize_offering(value):
                value = value.strip().lower()

                if value == "yes":
                    return "YES"

                if value == "no":
                    return "NO"

                # Includes Unknown and older dash-based entries.
                return "UNKNOWN"

            courses[course_id] = {
                "course_id": course_id,
                "course_name": course_name,
                "offerings": {
                    "Fall": normalize_offering(fall),
                    "Spring": normalize_offering(spring),
                    "Summer": normalize_offering(summer),
                },
            }

    return courses


# =========================================================
# CHECK 1: ORIGINAL COURSE UNAVAILABLE BEFORE GRADUATION
# =========================================================

def check_original_course_unavailable(
    original_course,
    student,
    courses,
    current_term,
):
    """
    PASS means the original course is not offered in any
    remaining opportunity before or during graduation.
    """
    name = "Original course unavailable before graduation"

    course_id = str(
        original_course.get("course_id", "")
    ).strip()

    if not valid_course_id(course_id):
        return make_check(
            name,
            REQUIRES_REVIEW,
            "The original course ID is missing or invalid.",
        )

    course = courses.get(course_id)

    if course is None:
        return make_check(
            name,
            REQUIRES_REVIEW,
            (
                f"Course {course_id} is missing from the "
                "offerings knowledge base."
            ),
        )

    graduation_term = student.get("expected_graduation_term")

    current_order = term_order(current_term)
    graduation_order = term_order(graduation_term)

    if current_order is None:
        return make_check(
            name,
            REQUIRES_REVIEW,
            "The current academic term could not be determined.",
        )

    if graduation_order is None:
        return make_check(
            name,
            REQUIRES_REVIEW,
            "The expected graduation term is missing or invalid.",
        )

    if graduation_order < current_order:
        return make_check(
            name,
            REQUIRES_REVIEW,
            (
                "The expected graduation term is earlier "
                "than the current academic term."
            ),
        )

    checked = []
    term = current_term

    while term_order(term) <= graduation_order:
        semester = term_to_semester(term)
        offering = course["offerings"][semester]

        checked.append(f"{semester} ({term}): {offering}")

        if offering == "YES":
            return make_check(
                name,
                FAIL,
                (
                    f"{course['course_name']} is offered in "
                    f"a remaining {semester} semester. "
                    f"Checked: {', '.join(checked)}."
                ),
            )

        if offering == "UNKNOWN":
            return make_check(
                name,
                REQUIRES_REVIEW,
                (
                    f"The offering status for {course['course_name']} "
                    f"is unknown in {semester}. "
                    f"Checked: {', '.join(checked)}."
                ),
            )

        # Check Summer between Spring and a later graduation term.
        if (
            semester == "Spring"
            and term_order(term) < graduation_order
        ):
            summer = course["offerings"]["Summer"]
            checked.append(f"Summer after {term}: {summer}")

            if summer == "YES":
                return make_check(
                    name,
                    FAIL,
                    (
                        f"{course['course_name']} is offered in "
                        "Summer before the expected graduation semester."
                    ),
                )

            if summer == "UNKNOWN":
                return make_check(
                    name,
                    REQUIRES_REVIEW,
                    "The Summer offering status is unknown.",
                )

        if term == graduation_term:
            break

        term = next_term(term)

        if term is None:
            return make_check(
                name,
                REQUIRES_REVIEW,
                "Could not determine the remaining academic terms.",
            )

    return make_check(
        name,
        PASS,
        (
            f"{course['course_name']} is not offered in any remaining "
            "semester through graduation. "
            f"Checked: {', '.join(checked)}."
        ),
    )


# =========================================================
# CHECK 2: PROPOSED COURSE AT SAME LEVEL OR HIGHER
# =========================================================

def check_course_level(original_course, proposed_course):
    name = "Proposed course is at the same level or higher"

    original_id = str(
        original_course.get("course_id", "")
    ).strip()

    proposed_id = str(
        proposed_course.get("course_id", "")
    ).strip()

    if (
        not valid_course_id(original_id)
        or not valid_course_id(proposed_id)
    ):
        return make_check(
            name,
            REQUIRES_REVIEW,
            "One or both course IDs are missing or invalid.",
        )

    # Project rule:
    # Fifth digit = intended year.
    # Final two digits = course level.
    original_year = int(original_id[4])
    proposed_year = int(proposed_id[4])

    original_level = int(original_id[-2:])
    proposed_level = int(proposed_id[-2:])

    evidence = (
        f"Original year/level: {original_year}/{original_level}; "
        f"proposed year/level: {proposed_year}/{proposed_level}."
    )

    if (
        proposed_year > original_year
        or (
            proposed_year == original_year
            and proposed_level >= original_level
        )
    ):
        return make_check(name, PASS, evidence)

    return make_check(
        name,
        FAIL,
        evidence + " The proposed course is lower under the defined rule.",
    )


# =========================================================
# CHECK 3: ORIGINAL COURSE IS CORE
# =========================================================

def check_original_course_is_core_placeholder():
    """
    The actual core-course classification is performed by Gemini
    in study_plan_check.py.

    This placeholder is used only by the deterministic evaluator.
    """
    return make_check(
        "Original course is a core course",
        REQUIRES_REVIEW,
        "Awaiting Gemini verification against the official program study plan.",
    )


# =========================================================
# CHECK 4: PROPOSED COURSE OFFERED IN CURRENT SEMESTER
# =========================================================

def check_proposed_course_offering(
    proposed_course,
    courses,
    current_term,
):
    name = "Proposed course is offered in the current semester"

    course_id = str(
        proposed_course.get("course_id", "")
    ).strip()

    if not valid_course_id(course_id):
        return make_check(
            name,
            REQUIRES_REVIEW,
            "The proposed course ID is missing or invalid.",
        )

    course = courses.get(course_id)

    if course is None:
        return make_check(
            name,
            REQUIRES_REVIEW,
            (
                f"Course {course_id} is missing from the "
                "offerings knowledge base."
            ),
        )

    semester = term_to_semester(current_term)

    if semester is None:
        return make_check(
            name,
            REQUIRES_REVIEW,
            "The current Fall/Spring semester could not be determined.",
        )

    offering = course["offerings"][semester]

    if offering == "YES":
        return make_check(
            name,
            PASS,
            f"{course['course_name']} is listed as offered in {semester}.",
        )

    if offering == "NO":
        return make_check(
            name,
            FAIL,
            f"{course['course_name']} is listed as not offered in {semester}.",
        )

    return make_check(
        name,
        REQUIRES_REVIEW,
        (
            f"The knowledge base does not specify whether "
            f"{course['course_name']} is offered in {semester}."
        ),
    )


# =========================================================
# CHECK 5: PROPOSED COURSE NOT COMPLETED PREVIOUSLY
# =========================================================

def check_proposed_course_not_completed(
    proposed_course,
    transcript,
):
    name = "Proposed course has not been completed previously"

    proposed_id = str(
        proposed_course.get("course_id", "")
    ).strip()

    if not valid_course_id(proposed_id):
        return make_check(
            name,
            REQUIRES_REVIEW,
            "The proposed course ID is missing or invalid.",
        )

    if not isinstance(transcript, list):
        return make_check(
            name,
            REQUIRES_REVIEW,
            "The transcript is missing or has an unexpected format.",
        )

    records = [
        record
        for record in transcript
        if isinstance(record, dict)
        and str(record.get("course_id", "")).strip() == proposed_id
    ]

    if not records:
        return make_check(
            name,
            PASS,
            f"Course {proposed_id} does not appear in the transcript.",
        )

    grades = [
        str(record.get("grade", "")).strip().upper()
        for record in records
    ]

    if any(grade in PASSING_GRADES for grade in grades):
        return make_check(
            name,
            FAIL,
            (
                f"Course {proposed_id} appears with a passing grade: "
                f"{', '.join(grades)}."
            ),
        )

    if any(
        not grade
        or grade in INCOMPLETE_GRADES
        or grade not in NON_COMPLETION_GRADES
        for grade in grades
    ):
        return make_check(
            name,
            REQUIRES_REVIEW,
            (
                f"Course {proposed_id} appears, but completion cannot "
                f"be confirmed. Grades: {', '.join(grades)}."
            ),
        )

    return make_check(
        name,
        PASS,
        (
            f"Course {proposed_id} appears only with non-completion "
            f"grade(s): {', '.join(grades)}."
        ),
    )


# =========================================================
# OVERALL ELIGIBILITY RESULT
# =========================================================

def build_overall_result(request, current_term, checks):
    statuses = [check["status"] for check in checks]

    if FAIL in statuses:
        overall = NOT_ELIGIBLE
    elif statuses and all(status == PASS for status in statuses):
        overall = ELIGIBLE
    else:
        overall = REQUIRES_REVIEW

    return {
        "request_id": request.get("request_id"),
        "current_term": current_term,
        "current_semester": term_to_semester(current_term),
        "overall_result": overall,
        "checks": checks,
    }


def evaluate_deterministic_checks(
    request,
    current_date=None,
    knowledge_base_path=None,
):
    """
    Run deterministic checks.

    The compulsory/core classification is intentionally left to Gemini.
    """
    if not isinstance(request, dict):
        raise ValueError("Request must be a dictionary.")

    student = (
        request.get("student")
        if isinstance(request.get("student"), dict)
        else {}
    )

    original = (
        request.get("original_course")
        if isinstance(request.get("original_course"), dict)
        else {}
    )

    proposed = (
        request.get("proposed_course")
        if isinstance(request.get("proposed_course"), dict)
        else {}
    )

    transcript = request.get("transcript")
    current_term = get_current_term(current_date)

    try:
        courses = load_course_knowledge_base(knowledge_base_path)

    except (OSError, UnicodeError) as exc:
        message = (
            f"Could not load course offerings knowledge base: {exc}"
        )

        checks = [
            make_check(
                "Original course unavailable before graduation",
                REQUIRES_REVIEW,
                message,
            ),
            check_course_level(original, proposed),
            check_original_course_is_core_placeholder(),
            make_check(
                "Proposed course is offered in the current semester",
                REQUIRES_REVIEW,
                message,
            ),
            check_proposed_course_not_completed(proposed, transcript),
        ]

        return build_overall_result(request, current_term, checks)

    checks = [
        check_original_course_unavailable(
            original,
            student,
            courses,
            current_term,
        ),
        check_course_level(original, proposed),
        check_original_course_is_core_placeholder(),
        check_proposed_course_offering(
            proposed,
            courses,
            current_term,
        ),
        check_proposed_course_not_completed(
            proposed,
            transcript,
        ),
    ]

    return build_overall_result(request, current_term, checks)
