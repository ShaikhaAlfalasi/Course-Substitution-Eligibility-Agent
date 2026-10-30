
"""Input handling for the Course Substitution Rejection Agent."""

import json


class InvalidEligibilityResultError(Exception):
    """Raised when the eligibility agent's result is invalid."""


def parse_eligibility_text(text: str) -> dict:
    """Parse JSON from the eligibility agent's output."""

    if not isinstance(text, str) or not text.strip():
        raise InvalidEligibilityResultError(
            "The eligibility agent result is empty."
        )

    start = text.find("{")

    if start == -1:
        raise InvalidEligibilityResultError(
            "No JSON object found in the eligibility agent output."
        )

    try:
        result, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as exc:
        raise InvalidEligibilityResultError(
            f"The eligibility agent JSON could not be parsed: {exc}"
        ) from exc

    return validate_eligibility_result(result)


def load_eligibility_result(path: str) -> dict:
    """Load an eligibility result saved as a JSON file."""

    try:
        with open(path, "rb") as file:
            raw = file.read()

    except OSError as exc:
        raise InvalidEligibilityResultError(
            f"Cannot read '{path}': {exc}"
        ) from exc

    try:
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            text = raw.decode("utf-16")
        else:
            text = raw.decode("utf-8-sig")

    except UnicodeDecodeError as exc:
        raise InvalidEligibilityResultError(
            f"The file encoding could not be read: {exc}"
        ) from exc

    return parse_eligibility_text(text)


def validate_eligibility_result(result) -> dict:
    """Validate the structure of the eligibility agent's output."""

    if not isinstance(result, dict):
        raise InvalidEligibilityResultError(
            "The eligibility result must be a JSON object."
        )

    if "overall_result" not in result:
        raise InvalidEligibilityResultError(
            "Missing 'overall_result'."
        )

    valid_results = {
        "ELIGIBLE",
        "NOT_ELIGIBLE",
        "MANUAL_REVIEW",
    }

    overall_result = result.get("overall_result")

    if overall_result not in valid_results:
        raise InvalidEligibilityResultError(
            f"Invalid overall result: {overall_result}"
        )

    checks = result.get("checks")

    if not isinstance(checks, list):
        raise InvalidEligibilityResultError(
            "Missing or invalid 'checks'."
        )

    for index, check in enumerate(checks, start=1):

        if not isinstance(check, dict):
            raise InvalidEligibilityResultError(
                f"Eligibility check {index} must be an object."
            )

        required_fields = ("condition", "status", "evidence")

        if not all(field in check for field in required_fields):
            raise InvalidEligibilityResultError(
                f"Eligibility check {index} is missing required fields."
            )

        if check["status"] not in {
            "PASS",
            "FAIL",
            "REQUIRES_REVIEW",
        }:
            raise InvalidEligibilityResultError(
                f"Eligibility check {index} has an invalid status."
            )

    return result
