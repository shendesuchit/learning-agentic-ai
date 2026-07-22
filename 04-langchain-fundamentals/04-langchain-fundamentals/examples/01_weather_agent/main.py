"""A deliberately small LangChain agent with one deterministic tool."""

from os import getenv

from dotenv import load_dotenv
from langchain.agents import create_agent

load_dotenv()

MODEL_NAME = getenv("MODEL_NAME", "openai:gpt-5.5")


def get_weather(city: str) -> str:
    """Return a demo weather report for a city; this is not live weather data."""
    reports = {
        "pune": "Warm and partly cloudy in the demo dataset.",
        "mumbai": "Humid with a chance of rain in the demo dataset.",
        "delhi": "Hot and hazy in the demo dataset.",
    }
    return reports.get(city.strip().lower(), f"No demo weather report is available for {city}.")


def main() -> None:
    if not getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and add a valid key."
        )

    agent = create_agent(
        model=MODEL_NAME,
        tools=[get_weather],
        system_prompt=(
            "You are a concise weather assistant. Use get_weather for weather "
            "questions. Clearly say that its data is a demo dataset."
        ),
    )

    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "What is the weather in Pune today?"}
            ]
        }
    )

    print("\n--- Full message state ---")
    for message in result["messages"]:
        print(f"{message.type}: {message.content}")

    print("\n--- Final answer ---")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
