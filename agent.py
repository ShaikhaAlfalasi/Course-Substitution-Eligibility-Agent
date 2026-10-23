
from database import get_course_substitution_request
from eligibility_checks import (
    evaluate_deterministic_checks,
    build_overall_result,
)
from study_plan_check import check_original_course_is_core


def evaluate_request(
    request,
    current_date=None,
    knowledge_base_path=None,
):
    """Run eligibility checks and combine their results."""

    result = evaluate_deterministic_checks(
        request,
        current_date=current_date,
        knowledge_base_path=knowledge_base_path,
    )

    checks = result["checks"]
    core_check = check_original_course_is_core(request)

    for index, check in enumerate(checks):
        if check["condition"] == "Original course is a core course":
            checks[index] = core_check
            break
    else:
        checks.append(core_check)

    return build_overall_result(
        request,
        result.get("current_term"),
        checks,
    )


def display_request_information(request):
    """Display the main request details before the eligibility results."""

    student = request.get("student") or {}
    original = request.get("original_course") or {}
    proposed = request.get("proposed_course") or {}

    graduation_term = student.get("expected_graduation_term")

    print("\n--- Request Information ---")
    print("Student:", student.get("student_name", "N/A"))
    print("Student ID:", student.get("student_id", "N/A"))
    print("Program:", student.get("program_name", "N/A"))
    print("Expected Graduation Term:", graduation_term or "N/A")

    print(
        "Original Course:",
        f"{original.get('course_name', 'N/A')} "
        f"({original.get('course_id', 'N/A')})",
    )

    print(
        "Proposed Replacement:",
        f"{proposed.get('course_name', 'N/A')} "
        f"({proposed.get('course_id', 'N/A')})",
    )

    print("Reason:", request.get("reason") or "N/A")


def display_check(check, number):
    """Print one eligibility check with concise evidence."""

    condition = check["condition"]
    status = check["status"]
    evidence = check.get("evidence", "")

    # Keep Gemini's core-course evidence short and readable.
    if condition == "Original course is a core course":
        if status == "PASS":
            evidence = "Confirmed compulsory in the official study plan."
        elif status == "FAIL":
            evidence = "The official study plan classifies it as an elective."
        else:
            evidence = "Could not verify its classification in the official study plan."

    print(f"\n{number}. {condition}")
    print("   Result:", status)
    print("   Evidence:", evidence)


def run_request(request_id):
    request = get_course_substitution_request(request_id)

    if request is None:
        return None, None

    result = evaluate_request(request)
    return request, result


def main():
    request_id = input(
        "Enter a Course Substitution Request ID: "
    ).strip()

    try:
        request, result = run_request(request_id)

        if request is None:
            print("\nNo matching Course Substitution request found.")
            return

        print("\n" + "=" * 58)
        print("COURSE SUBSTITUTION ELIGIBILITY RESULTS")
        print("=" * 58)

        display_request_information(request)

        print("\nCurrent Term:", result["current_term"])
        print("Current Semester:", result["current_semester"])

        print("\n--- Eligibility Checks ---")

        for number, check in enumerate(result["checks"], start=1):
            display_check(check, number)

        print("\n" + "=" * 58)
        print("OVERALL RESULT:", result["overall_result"])
        print("=" * 58)

    except Exception as exc:
        print(f"\nAgent failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
