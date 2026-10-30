
from services.database import get_course_substitution_request
from eligibility_checks import evaluate_eligibility


if __name__ == "__main__":
    request_id = input(
        "Enter a Course Substitution Request ID: "
    ).strip()

    try:
        request = get_course_substitution_request(request_id)

        if request is None:
            print("\nNo matching request found.")

        else:
            result = evaluate_eligibility(request)

            print("\n" + "=" * 55)
            print("COURSE SUBSTITUTION ELIGIBILITY RESULTS")
            print("=" * 55)

            print("Request ID:", result["request_id"])
            print("Current term:", result["current_term"])
            print("Current semester:", result["current_semester"])

            print("\n--- Individual Eligibility Checks ---")

            for number, check in enumerate(result["checks"], start=1):
                print(f"\n{number}. {check['condition']}")
                print("   Result:", check["status"])
                print("   Evidence:", check["evidence"])

            print("\n" + "=" * 55)
            print("OVERALL RESULT:", result["overall_result"])
            print("=" * 55)

    except Exception as error:
        print(
            f"\nEligibility test failed: "
            f"{type(error).__name__}: {error}"
        )
