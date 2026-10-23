
from database import get_course_substitution_request

request_id = input("Enter a Course Substitution Request ID: ").strip()

try:
    request = get_course_substitution_request(request_id)

    if request is None:
        print("No matching Course Substitution request found.")

    else:
        print("\nRequest retrieved successfully!")

        print("\n--- Request Information ---")
        print("Request ID:", request.get("request_id"))
        print("Request type:", request.get("request_type"))
        print("Student:", request.get("student"))
        print("Original course:", request.get("original_course"))
        print("Proposed course:", request.get("proposed_course"))
        print("Reason:", request.get("reason"))

        # Show the complete set of top-level fields.
        print("\n--- Available Request Fields ---")
        print(list(request.keys()))

        # Requested semester may be stored in the request or
        # within another returned object, so inspect the fields first.
        print("\n--- Semester Information ---")
        print("Requested term:", request.get("requested_term"))
        print("Term:", request.get("term"))
        print("Semester:", request.get("semester"))

        # Transcript information.
        transcript = request.get("transcript", [])

        print("\n--- Transcript Information ---")
        print("Transcript courses:", len(transcript))
        print("Transcript sample (first 2 records):")
        print(transcript[:2])

        # Course offering information.
        original_offerings = request.get(
            "original_course_offerings", []
        )
        proposed_offerings = request.get(
            "proposed_course_offerings", []
        )

        print("\n--- Original Course Offerings ---")
        print("Number of records:", len(original_offerings))
        print(original_offerings[:2])

        print("\n--- Proposed Course Offerings ---")
        print("Number of records:", len(proposed_offerings))
        print(proposed_offerings[:2])

except Exception as exc:
    print(
        f"Database test failed: "
        f"{type(exc).__name__}: {exc}"
    )
