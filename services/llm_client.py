
import os

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from google.genai import errors


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=GEMINI_API_KEY)


# Models are ordered from preferred to fallback.
# gemini-3.8-flash has already been tested successfully.
GEMINI_MODELS = [
    "gemini-3.5-flash-lite", 
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
]


def generate_with_fallback(prompt, use_url_context=False):
    """
    Generate a response using the configured Gemini models.

    Try the next model after temporary server errors, rate limits,
    or a 404 indicating that a model is unavailable.

    Other client errors and unexpected exceptions are raised.
    """

    errors_encountered = []

    for model in GEMINI_MODELS:
        try:
            print(f"Trying Gemini model: {model}")

            config = None

            if use_url_context:
                config = GenerateContentConfig(
                    tools=[{"url_context": {}}]
                )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )

            if not response.text:
                raise RuntimeError(
                    f"Gemini model {model} returned an empty response."
                )

            print(f"Success with model: {model}")
            return response

        except errors.ServerError as error:
            print(f"Temporary server error with {model}: {error}")

            errors_encountered.append({
                "model": model,
                "error": str(error),
            })

        except errors.ClientError as error:
            status_code = getattr(error, "code", None)

            if status_code in (404, 429):
                print(f"Model unavailable or rate limited: {model}")
                print(error)

                errors_encountered.append({
                    "model": model,
                    "error": str(error),
                })

            else:
                # Authentication, permission, invalid request,
                # and other client errors should not be hidden.
                raise

    raise RuntimeError(
        "All configured Gemini models failed.\n"
        + "\n".join(
            f'{item["model"]}: {item["error"]}'
            for item in errors_encountered
        )
    )
