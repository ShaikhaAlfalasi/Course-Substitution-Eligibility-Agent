
from llm_client import generate_with_fallback


if __name__ == "__main__":
    try:
        response = generate_with_fallback(
            "Reply with exactly: LLM client working!"
        )

        print("\nFinal response:")
        print(response.text)

    except Exception as error:
        print(f"\nLLM client test failed: {type(error).__name__}: {error}")
