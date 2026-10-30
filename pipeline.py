
"""Runs the Course Substitution Eligibility and Rejection Agents."""

import sys

from agents.agent import (
    run_request,
    display_request_information,
    display_check,
)

from agents.rejection_agent import explain_rejection_workflow


def run_pipeline(request_id: str) -> dict:
    """Run both agents for one Course Substitution request."""

    request, eligibility_result = run_request(request_id)

    if request is None:
        return {
            "error": "No matching Course Substitution request found."
        }

    rejection_result = explain_rejection_workflow(eligibility_result)

    return {
        "request": request,
        "eligibility_result": eligibility_result,
        "rejection_result": rejection_result,
    }


def display_pipeline_report(result: dict) -> None:
    """Display eligibility results and rejection explanations."""

    if "error" in result:
        print(f"\nERROR: {result['error']}")
        return

    request = result["request"]
    eligibility = result["eligibility_result"]
    rejection = result["rejection_result"]

    print("\n" + "=" * 58)
    print("COURSE SUBSTITUTION ELIGIBILITY RESULTS")
    print("=" * 58)

    display_request_information(request)

    print("\nCurrent Term:", eligibility.get("current_term"))
    print("Current Semester:", eligibility.get("current_semester"))

    print("\n--- Eligibility Checks ---")

    for number, check in enumerate(eligibility["checks"], start=1):
        display_check(check, number)

    print("\n" + "=" * 58)
    print("OVERALL RESULT:", eligibility["overall_result"])
    print("=" * 58)

    if eligibility["overall_result"] == "NOT_ELIGIBLE":

        print("\nREJECTION REASONS:")

        reasons = rejection.get("suggested_reasons", [])

        if reasons:
            tone_order = ["formal", "concise", "supportive"]

            for tone in tone_order:
                suggestion = next(
                    (
                        item for item in reasons
                        if item.get("tone") == tone
                    ),
                    None
                )

                if suggestion:
                    print(f"\n[{tone.upper()}]")
                    print(f"- {suggestion['text']}")

        else:
            print("- Rejection explanations could not be generated.")
            print("- Please refer to the failed eligibility checks.")

    print("\nFinal decision: Authorized staff member.")


def main():
    """Main entry point."""

    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <request_id>")
        sys.exit(1)

    request_id = sys.argv[1].strip()

    try:
        result = run_pipeline(request_id)
        display_pipeline_report(result)

    except Exception as exc:
        print(f"\nPipeline failed: {type(exc).__name__}: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
