
"""Test the Course Substitution Rejection Explanation Agent."""

import json

from agents.rejection_agent import (
    explain_rejection_workflow,
    display_rejection_report,
)


def main():

    # Simulated output from the Course Substitution Eligibility Agent.
    sample_result = {
        "overall_result": "NOT_ELIGIBLE",
        "checks": [
            {
                "condition": "Original course unavailable before graduation",
                "status": "PASS",
                "evidence": "The original course is not offered in Fall."
            },
            {
                "condition": "Proposed course is at the same level or higher",
                "status": "FAIL",
                "evidence": "Original level: 72. Proposed level: 42."
            },
            {
                "condition": "Original course is a core course",
                "status": "PASS",
                "evidence": "Confirmed compulsory in the official study plan."
            },
            {
                "condition": "Proposed course is offered in the current semester",
                "status": "PASS",
                "evidence": "The proposed course is offered in Fall."
            },
            {
                "condition": "Proposed course has not been completed previously",
                "status": "PASS",
                "evidence": "No passing completion record was found."
            }
        ]
    }

    print("Testing Course Substitution Rejection Agent...")

    result = explain_rejection_workflow(sample_result)

    display_rejection_report(result)

    print("\nFull JSON result:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
