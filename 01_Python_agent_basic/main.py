"""A small, visible tool-calling agent built with the Python standard library.

Start with demo mode:
    python main.py "What is the weather in Pune?"

The numbered sections are intended to be read from top to bottom.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Protocol


# -----------------------------------------------------------------------------
# 1. THE TOOL: ordinary Python code that can perform a useful action
# -----------------------------------------------------------------------------

SAMPLE_WEATHER: dict[str, dict[str, Any]] = {
    "pune": {"temperature_c": 27, "condition": "partly cloudy"},
    "mumbai": {"temperature_c": 30, "condition": "humid"},
    "tokyo": {"temperature_c": 23, "condition": "clear"},
    "london": {"temperature_c": 16, "condition": "light rain"},
}


def get_weather(city: str) -> dict[str, Any]:
    """Return fixed sample weather for a city.

    The function is deliberately predictable. This lets us study the agent flow without
    introducing a second API, networking failures, or changing weather values.
    """

    normalized_city = city.strip().lower()
    weather = SAMPLE_WEATHER.get(normalized_city)

    if weather is None:
        return {
            "city": city.strip(),
            "available": False,
            "message": "No sample weather is available for this city.",
        }

    return {"city": city.strip().title(), "available": True, **weather}


# -----------------------------------------------------------------------------
# 2. THE TOOL SCHEMA: a machine-readable explanation shown to the model
# -----------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get sample weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, for example Pune or Tokyo.",
                    }
                },
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }
]

# A registry connects the name produced by the model to the real Python function.
TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {"get_weather": get_weather}


# -----------------------------------------------------------------------------
# 3. A COMMON MODEL INTERFACE: demo and real API modes return the same shape
# -----------------------------------------------------------------------------


class ChatModel(Protocol):
    """The smallest capability our agent needs from a chat model."""

    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]: ...


@dataclass(slots=True)
class DemoModel:
    """A deterministic teaching model that imitates tool-selection behaviour."""

    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        # If a tool result is already present, the next job is to explain that result.
        if messages[-1]["role"] == "tool":
            result = json.loads(messages[-1]["content"])
            if result.get("available"):
                return {
                    "role": "assistant",
                    "content": (
                        f"The sample weather in {result['city']} is "
                        f"{result['temperature_c']}°C with {result['condition']} conditions."
                    ),
                }
            return {"role": "assistant", "content": result["message"]}

        question = messages[-1]["content"]
        lowered = question.lower()

        if "weather" in lowered:
            city = next(
                (name.title() for name in SAMPLE_WEATHER if name in lowered),
                "Unknown",
            )
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "demo-call-1",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": json.dumps({"city": city}),
                        },
                    }
                ],
            }

        return {
            "role": "assistant",
            "content": (
                "An AI agent is a program that lets a model decide what action to take, "
                "executes the selected action in code, and returns the result to the model."
            ),
        }


@dataclass(slots=True)
class OpenAICompatibleModel:
    """Call an OpenAI-compatible chat-completions endpoint using urllib."""

    api_key: str
    model_name: str
    base_url: str
    timeout_seconds: int = 30

    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        payload = json.dumps(
            {"model": self.model_name, "messages": messages, "tools": tools}
        ).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.base_url.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Model API returned HTTP {error.code}: {details}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Could not reach the model API: {error.reason}") from error

        return body["choices"][0]["message"]


def create_model() -> ChatModel:
    """Choose demo mode by default, or API mode through environment variables."""

    mode = os.getenv("AGENT_MODE", "demo").lower()
    if mode == "demo":
        return DemoModel()
    if mode != "api":
        raise ValueError("AGENT_MODE must be either 'demo' or 'api'.")

    api_key = os.getenv("MODEL_API_KEY")
    if not api_key:
        raise ValueError("MODEL_API_KEY is required when AGENT_MODE=api.")

    return OpenAICompatibleModel(
        api_key=api_key,
        model_name=os.getenv("MODEL_NAME", "gpt-4.1-mini"),
        base_url=os.getenv("MODEL_BASE_URL", "https://api.openai.com/v1"),
    )


# -----------------------------------------------------------------------------
# 4. THE AGENTIC LOOP: model decision -> optional tool -> model response
# -----------------------------------------------------------------------------


def print_step(number: int, title: str, value: Any, *, quiet: bool) -> None:
    """Reveal an otherwise hidden agent step when teaching mode is enabled."""

    if quiet:
        return
    print(f"\nSTEP {number} — {title}")
    print(json.dumps(value, indent=2, ensure_ascii=False) if not isinstance(value, str) else value)


def execute_tool_call(tool_call: dict[str, Any]) -> dict[str, Any]:
    """Validate a model request, call the matching function, and return its message."""

    function_request = tool_call["function"]
    function_name = function_request["name"]
    function = TOOL_REGISTRY.get(function_name)
    if function is None:
        raise ValueError(f"The model requested an unknown tool: {function_name}")

    try:
        arguments = json.loads(function_request["arguments"])
    except json.JSONDecodeError as error:
        raise ValueError("The model returned invalid JSON tool arguments.") from error

    result = function(**arguments)
    return {
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "name": function_name,
        "content": json.dumps(result),
    }


def run_agent(question: str, model: ChatModel, *, quiet: bool = False) -> str:
    """Run one complete agent interaction and return the final text answer."""

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "You are a concise assistant. Use a tool when the question needs it.",
        },
        {"role": "user", "content": question},
    ]
    print_step(1, "The agent receives the question", messages[-1], quiet=quiet)

    assistant_message = model.complete(messages, TOOL_SCHEMAS)
    messages.append(assistant_message)
    print_step(2, "The model makes a decision", assistant_message, quiet=quiet)

    tool_calls = assistant_message.get("tool_calls", [])
    if tool_calls:
        # A model can request several tools. This small lesson supports them in order.
        for tool_call in tool_calls:
            tool_message = execute_tool_call(tool_call)
            messages.append(tool_message)
            print_step(3, "Python executes the requested tool", tool_message, quiet=quiet)

        # Crucial idea: a tool returns data, not the final natural-language response.
        assistant_message = model.complete(messages, TOOL_SCHEMAS)
        messages.append(assistant_message)
        print_step(4, "The model reads the result", assistant_message, quiet=quiet)

    final_answer = assistant_message.get("content") or "The model returned no text answer."
    print_step(5, "Final answer", final_answer, quiet=quiet)
    return final_answer


# -----------------------------------------------------------------------------
# 5. LEARNER-FRIENDLY COMMAND-LINE INTERFACE AND SELF-TESTS
# -----------------------------------------------------------------------------


def run_self_tests() -> None:
    """Check the local teaching logic without an API key or test framework."""

    pune = get_weather(" Pune ")
    assert pune["available"] is True
    assert pune["city"] == "Pune"

    missing = get_weather("Atlantis")
    assert missing["available"] is False

    answer = run_agent("What is the weather in Tokyo?", DemoModel(), quiet=True)
    assert "23°C" in answer
    assert "Tokyo" in answer

    direct_answer = run_agent("What is an agent?", DemoModel(), quiet=True)
    assert "AI agent" in direct_answer

    print("All self-tests passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", help="Question to ask the agent")
    parser.add_argument("--quiet", action="store_true", help="Print only the final answer")
    parser.add_argument("--self-test", action="store_true", help="Run offline checks and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.self_test:
        run_self_tests()
        return
    if not args.question:
        print('Try: python main.py "What is the weather in Pune?"')
        raise SystemExit(2)

    try:
        answer = run_agent(args.question, create_model(), quiet=args.quiet)
        if args.quiet:
            print(answer)
    except (RuntimeError, ValueError, TypeError, KeyError) as error:
        print(f"Agent error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

