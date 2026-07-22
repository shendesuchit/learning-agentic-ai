"""Compare complete, streamed, and independent concurrent model invocations."""

import os

from langchain.chat_models import init_chat_model


def main() -> None:
    model = init_chat_model(
        os.getenv("LC_MODEL", "openai:gpt-4.1-mini"),
        temperature=0.2,
        max_tokens=180,
        timeout=30,
        max_retries=2,
    )

    complete = model.invoke("Give one sentence explaining exponential backoff.")
    print("INVOKE:\n", complete.text)

    print("\nSTREAM:")
    pieces: list[str] = []
    for chunk in model.stream("Explain why a timeout needs a retry policy in two sentences."):
        print(chunk.text, end="", flush=True)
        pieces.append(chunk.text)
    print("\nAssembled length:", len("".join(pieces)))

    prompts = [
        "Define a context window in one sentence.",
        "Define a tool schema in one sentence.",
        "Define structured output in one sentence.",
    ]
    print("\nBATCH:")
    for prompt, response in zip(prompts, model.batch(prompts), strict=True):
        print(f"- {prompt}\n  {response.text}")

    print("\nBATCH AS COMPLETED:")
    for index, response in model.batch_as_completed(prompts):
        if isinstance(response, Exception):
            print(f"- request {index} failed: {response}")
        else:
            print(f"- request {index}: {response.text}")


if __name__ == "__main__":
    main()
