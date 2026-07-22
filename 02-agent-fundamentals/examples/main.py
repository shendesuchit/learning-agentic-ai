"""A provider-free demonstration of a bounded agentic tool-calling loop.

Replace simulated_model() with a real model client only after understanding the
message protocol. The application remains responsible for validation, execution,
state, and stop conditions.
"""

from __future__ import annotations

import json
from typing import Any, Callable


Message = dict[str, Any]
Tool = Callable[..., dict[str, Any]]

WEATHER_BY_CITY = {
    "pune": {"temperature_c": 27, "condition": "partly cloudy"},
    "tokyo": {"temperature_c": 24, "condition": "clear"},
    "delhi": {"temperature_c": 33, "condition": "hazy"},
}

TOOL_SCHEMAS = [
    {
        "name": "get_weather",
        "description": "Return current mock weather for a supported city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
]


def get_weather(city: str) -> dict[str, Any]:
    """A mock external capability with a predictable result for learning."""
    weather = WEATHER_BY_CITY.get(city.lower())
    if weather is None:
        return {"ok": False, "error": f"No mock weather data for {city!r}."}
    return {"ok": True, "city": city.title(), **weather}


TOOL_REGISTRY: dict[str, Tool] = {"get_weather": get_weather}


def simulated_model(messages: list[Message], tools: list[dict[str, Any]]) -> Message:
    """Simulate a model response so this example runs without a provider/API key."""
    last_message = messages[-1]

    if last_message["role"] == "tool":
        result = json.loads(last_message["content"])
        if result["ok"]:
            return {
                "role": "assistant",
                "content": (
                    f"The mock weather in {result['city']} is "
                    f"{result['temperature_c']}°C and {result['condition']}."
                ),
            }
        return {"role": "assistant", "content": f"The lookup failed: {result['error']}"}

    question = last_message["content"].lower()
    if "weather" in question:
        city = next((name for name in WEATHER_BY_CITY if name in question), "Pune")
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_weather_001",
                    "name": "get_weather",
                    "arguments": {"city": city},
                }
            ],
        }

    return {
        "role": "assistant",
        "content": "A dictionary stores key-value pairs; for example, {'city': 'Pune'}.",
    }


def validate_and_execute(tool_call: dict[str, Any]) -> Message:
    """Perform host-side validation before invoking a registered tool."""
    name = tool_call.get("name")
    arguments = tool_call.get("arguments")
    tool_call_id = tool_call.get("id")

    if not isinstance(name, str) or name not in TOOL_REGISTRY:
        result = {"ok": False, "error": f"Unknown or disallowed tool: {name!r}"}
    elif not isinstance(arguments, dict) or not isinstance(arguments.get("city"), str):
        result = {"ok": False, "error": "get_weather requires a string 'city' argument."}
    else:
        # A real implementation would also enforce authorization, timeouts,
        # input constraints, audit logging, and side-effect policies here.
        result = TOOL_REGISTRY[name](**arguments)

    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": name,
        "content": json.dumps(result),
    }


def run_agent(user_input: str, max_turns: int = 4) -> tuple[str, list[Message]]:
    """Run a bounded loop and return the final answer plus inspectable state."""
    messages: list[Message] = [{"role": "user", "content": user_input}]

    for _ in range(max_turns):
        response = simulated_model(messages, TOOL_SCHEMAS)
        messages.append(response)
        tool_calls = response.get("tool_calls", [])

        if not tool_calls:
            return response["content"], messages

        for tool_call in tool_calls:
            messages.append(validate_and_execute(tool_call))

    return "Stopped safely: the agent reached its maximum number of turns.", messages


if __name__ == "__main__":
    for question in (
        "Explain what a Python dictionary is.",
        "What is the weather in Tokyo?",
    ):
        answer, trace = run_agent(question)
        print(f"\\nUser: {question}")
        print(f"Assistant: {answer}")
        print("Protocol trace:")
        for message in trace:
            print(" ", json.dumps(message, ensure_ascii=False))
