"""A minimal manual tool loop. The tool is deliberately mock and read-only."""

import os
import re

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage


APPROVED_CITIES = {"pune", "mumbai", "delhi", "tokyo"}


def get_weather(city: str) -> str:
    """Return current mock weather for an approved city. Input: city name."""
    normalized = city.strip().lower()
    if normalized not in APPROVED_CITIES:
        return "Weather is unavailable for that city. Ask for an approved city."
    return f"Mock weather in {normalized.title()}: 28°C, clear skies."


def validated_weather_call(arguments: dict[str, object]) -> str:
    """Treat model-generated arguments as untrusted input."""
    city = arguments.get("city")
    if not isinstance(city, str) or not re.fullmatch(r"[A-Za-z ]{2,50}", city):
        return "Tool input rejected: city must be a short alphabetic string."
    return get_weather(city)


def main() -> None:
    base_model = init_chat_model(os.getenv("LC_MODEL", "openai:gpt-4.1-mini"), temperature=0)
    model = base_model.bind_tools([get_weather])
    messages = [
        SystemMessage(
            "Use the weather tool for current weather. Never claim you executed a tool if no result was returned."
        ),
        HumanMessage("What is the weather in Pune today?"),
    ]

    first_response = model.invoke(messages)
    messages.append(first_response)

    if not first_response.tool_calls:
        print("Model chose not to request a tool:\n", first_response.text)
        return

    for call in first_response.tool_calls:
        if call["name"] != "get_weather":
            result = "Tool request rejected: unapproved tool name."
        else:
            result = validated_weather_call(call["args"])
        messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

    final_response = model.invoke(messages)
    print(final_response.text)


if __name__ == "__main__":
    main()
