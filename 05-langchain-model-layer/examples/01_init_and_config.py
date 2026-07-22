"""Create a chat model with explicit application-level choices."""

import os

from langchain.chat_models import init_chat_model


def main() -> None:
    model_name = os.getenv("LC_MODEL", "openai:gpt-4.1-mini")
    model = init_chat_model(
        model_name,
        temperature=0.2,
        max_tokens=250,
        timeout=20,
        max_retries=2,
    )

    response = model.invoke(
        "Explain the difference between an input token and an output token in two sentences."
    )
    print(response.text)
    print("\nUsage metadata:", response.usage_metadata)


if __name__ == "__main__":
    main()
