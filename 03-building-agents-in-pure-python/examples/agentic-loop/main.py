from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from uuid import uuid4


Message = dict[str, Any]
Tool = Callable[..., str]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelResponse:
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()


@dataclass(frozen=True)
class AgentResult:
    status: str
    answer: str
    messages: tuple[Message, ...]


def get_weather(city: str) -> str:
    weather = {
        "tokyo": "Tokyo: 22°C and partly cloudy",
        "delhi": "Delhi: 34°C and sunny",
    }
    return weather.get(city.lower(), f"No weather data is available for {city}.")


class ScriptedModel:
    """A deterministic model substitute that makes the agent protocol visible."""

    def invoke(self, messages: list[Message], tool_schemas: list[dict[str, Any]]) -> ModelResponse:
        user_request = next(
            message["content"] for message in messages if message["role"] == "user"
        ).lower()
        tool_results = [message for message in messages if message["role"] == "tool"]

        if "repeat" in user_request:
            return ModelResponse(
                tool_calls=(ToolCall(str(uuid4()), "get_weather", {"city": "Tokyo"}),)
            )

        if "currency" in user_request and not tool_results:
            return ModelResponse(
                tool_calls=(ToolCall(str(uuid4()), "convert_currency", {"amount": 1}),)
            )

        if "weather" in user_request and not tool_results:
            cities = [city for city in ("Tokyo", "Delhi") if city.lower() in user_request]
            cities = cities or ["Tokyo"]
            return ModelResponse(
                tool_calls=tuple(
                    ToolCall(str(uuid4()), "get_weather", {"city": city}) for city in cities
                )
            )

        if tool_results:
            errors = [result["content"] for result in tool_results if result.get("is_error")]
            if errors:
                return ModelResponse(content=f"I could not complete that request: {errors[-1]}")
            observations = "; ".join(result["content"] for result in tool_results)
            return ModelResponse(content=f"Here is what I found: {observations}.")

        return ModelResponse(content="I can answer that without using a tool.")


def tool_schema(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }


def execute_tool(call: ToolCall, tools_by_name: dict[str, Tool]) -> Message:
    tool = tools_by_name.get(call.name)
    if tool is None:
        return {
            "role": "tool",
            "tool_call_id": call.id,
            "content": f"Tool '{call.name}' is not available.",
            "is_error": True,
        }

    try:
        result = tool(**call.arguments)
    except (TypeError, ValueError) as error:
        return {
            "role": "tool",
            "tool_call_id": call.id,
            "content": f"Invalid arguments for '{call.name}': {error}",
            "is_error": True,
        }

    return {"role": "tool", "tool_call_id": call.id, "content": result, "is_error": False}


def run_agent(user_request: str, max_iterations: int = 4) -> AgentResult:
    tools_by_name = {"get_weather": get_weather}
    schemas = [tool_schema("get_weather", "Return weather for a supported city.")]
    messages: list[Message] = [{"role": "user", "content": user_request}]
    model = ScriptedModel()

    for _ in range(max_iterations):
        response = model.invoke(messages, schemas)
        assistant_message: Message = {"role": "assistant", "content": response.content}
        if response.tool_calls:
            assistant_message["tool_calls"] = [
                {"id": call.id, "name": call.name, "arguments": call.arguments}
                for call in response.tool_calls
            ]
        messages.append(assistant_message)

        if not response.tool_calls:
            return AgentResult("completed", response.content, tuple(messages))

        for call in response.tool_calls:
            messages.append(execute_tool(call, tools_by_name))

    return AgentResult(
        "max_iterations_reached",
        "Stopped before a final answer was produced.",
        tuple(messages),
    )


def print_trace(request: str, max_iterations: int = 4) -> None:
    result = run_agent(request, max_iterations=max_iterations)
    print(f"\nUser: {request}")
    print(f"Status: {result.status}")
    print(f"Answer: {result.answer}")
    print("Messages:")
    for message in result.messages:
        print(f"  {message}")


if __name__ == "__main__":
    print_trace("Hello")
    print_trace("What is the weather in Tokyo?")
    print_trace("What is the weather in Tokyo and Delhi?")
    print_trace("Convert currency")
    print_trace("Repeat the weather lookup", max_iterations=2)
