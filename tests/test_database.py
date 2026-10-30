
from services.database import get_course_substitution_request


def test_database():

    request_id = input(
        "Enter a Course Substitution Request ID: "
    ).strip()

    try:
        request = get_course_substitution_request(request_id)

        if request is None:
            print("\nNo matching Course Substitution request found.")
            return

        print("\nRequest retrieved successfully!")

        print("\n--- Request Information ---")
        print("Request ID:", request["request_id"])
        print("Request type:", request["request_type"])
        print("Request date:", request["request_date"])
        print("Submission time:", request["submission_time"])
        print("Current status:", request["current_status"])

        print("\n--- Student Information ---")
        print(request["student"])

        print("\n--- Course Information ---")
        print("Original course:", request["original_course"])
        print("Proposed course:", request["proposed_course"])
        print("Reason:", request["reason"])

        print("\n--- Course Completion Check ---")

        completion = request["course_completion"]

        print(
            "Original course completed:",
            completion["original_course_completed"]
        )

        print(
            "Proposed course completed:",
            completion["proposed_course_completed"]
        )

        print("\n--- Semester Information ---")
        print("Current term:", request["current_term"])
        print(
            "Expected graduation term:",
            request["student"]["expected_graduation_term"]
        )

    except Exception as e:
        print(
            f"\nDatabase test failed: "
            f"{type(e).__name__}: {e}"
        )


if __name__ == "__main__":
    test_database()
