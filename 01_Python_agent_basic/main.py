"""A single-file, framework-free introduction to an AI tool-calling agent.

The important idea is simple:

1. Python sends the conversation and tool description to the model.
2. The model either answers or requests a tool.
3. Python executes the requested function.
4. Python sends the tool result back to the model.
5. The model writes the final answer.

The model chooses a tool, but Python—not the model—executes it.
"""

import argparse
import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# 1. A normal Python function that will act as our tool
# ---------------------------------------------------------------------------

SAMPLE_WEATHER = {
    "tokyo": {"celsius": 22, "conditions": "partly cloudy"},
    "delhi": {"celsius": 34, "conditions": "clear skies"},
    "london": {"celsius": 15, "conditions": "light rain"},
}


def get_weather(city: str) -> str:
    """Return sample weather for a city."""
    data = SAMPLE_WEATHER.get(city.lower())
    if data is None:
        return f"No weather data for {city!r}."
    return f"{city.title()}: {data['celsius']}C, {data['conditions']}"


# ---------------------------------------------------------------------------
# 2. The schema tells the model which tool exists and which input it accepts
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get sample weather for Tokyo, Delhi, or London.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }
]

# This mapping lets Python find the real function requested by the model.
TOOLS_BY_NAME = {"get_weather": get_weather}


# ---------------------------------------------------------------------------
# 3. Select an OpenAI-compatible provider using values from .env
# ---------------------------------------------------------------------------

def get_client_and_model() -> tuple[OpenAI, str, str]:
    """Return the first configured client, model, and provider name."""
    load_dotenv()

    if key := os.getenv("GROQ_API_KEY"):
        client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return client, model, "Groq"

    if key := os.getenv("OPENROUTER_API_KEY"):
        client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
        model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        return client, model, "OpenRouter"

    if key := os.getenv("OPENAI_API_KEY"):
        client = OpenAI(api_key=key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return client, model, "OpenAI"

    raise RuntimeError(
        "No API key found. Copy .env.example to .env and configure one provider."
    )


# ---------------------------------------------------------------------------
# 4. Small printing helpers make the hidden execution flow visible
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def print_memory(messages: list[dict[str, Any]]) -> None:
    print_section("CURRENT CONVERSATION MEMORY")
    print(json.dumps(messages, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# 5. The agent loop: model -> tool -> model -> final answer
# ---------------------------------------------------------------------------

def execute_tool(tool_name: str, raw_arguments: str) -> str:
    """Validate a model request and execute the matching Python function."""
    tool = TOOLS_BY_NAME.get(tool_name)
    if tool is None:
        return f"Tool error: unknown tool {tool_name!r}."

    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as error:
        return f"Tool error: invalid JSON arguments ({error.msg})."

    if not isinstance(arguments, dict):
        return "Tool error: arguments must be a JSON object."

    try:
        return str(tool(**arguments))
    except (TypeError, ValueError) as error:
        return f"Tool error: {error}"


def run_agent(
    messages: list[dict[str, Any]], max_turns: int = 4, verbose: bool = True
) -> str:
    """Run the agent until the model answers or the safety limit is reached."""
    client, model, provider = get_client_and_model()

    for turn in range(1, max_turns + 1):
        if verbose:
            print_section(f"AGENT TURN {turn}")
            print(f"Provider: {provider}\nModel: {model}")
            print_memory(messages)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            max_tokens=300,
        )
        assistant = response.choices[0].message

        # No tool request means the model has produced its final answer.
        if not assistant.tool_calls:
            answer = assistant.content or ""
            messages.append({"role": "assistant", "content": answer})
            return answer

        # First store the assistant's tool request in conversation memory.
        messages.append(
            {
                "role": "assistant",
                "content": assistant.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in assistant.tool_calls
                ],
            }
        )

        # Python now executes each requested tool and stores its result.
        for call in assistant.tool_calls:
            result = execute_tool(call.function.name, call.function.arguments)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
            if verbose:
                print_section(f"PYTHON EXECUTED: {call.function.name}")
                print(f"Arguments: {call.function.arguments}\nResult: {result}")

        # The loop runs again so the model can read the new tool result.

    return f"Reached the safety limit of {max_turns} turns without a final answer."


# ---------------------------------------------------------------------------
# 6. Terminal interface
# ---------------------------------------------------------------------------

def run_self_test() -> None:
    """Check the local tool logic without making an API request."""
    assert get_weather("DELHI") == "Delhi: 34C, clear skies"
    assert get_weather("Pune") == "No weather data for 'Pune'."
    assert "unknown tool" in execute_tool("missing", "{}")
    assert "invalid JSON" in execute_tool("get_weather", "not-json")
    print("All 4 local self-tests passed.")


def chat(verbose: bool) -> None:
    """Keep one in-memory conversation until the user exits."""
    messages: list[dict[str, Any]] = []
    print("Ask about sample weather in Delhi, Tokyo, or London.")
    print("Type 'exit' to stop.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            return
        if not question:
            continue

        messages.append({"role": "user", "content": question})
        print(f"\nAgent: {run_agent(messages, verbose=verbose)}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Study a tool-calling agent loop.")
    parser.add_argument("question", nargs="?", help="Ask one question and exit")
    parser.add_argument("--quiet", action="store_true", help="Hide the execution trace")
    parser.add_argument(
        "--self-test", action="store_true", help="Test local code without an API key"
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
    elif args.question:
        messages = [{"role": "user", "content": args.question}]
        print(run_agent(messages, verbose=not args.quiet))
    else:
        chat(verbose=not args.quiet)


if __name__ == "__main__":
    main()
