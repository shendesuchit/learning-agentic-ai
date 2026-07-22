"""Send a typed conversation and inspect an AIMessage as an application object."""

import os

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


def main() -> None:
    model = init_chat_model(os.getenv("LC_MODEL", "openai:gpt-4.1-mini"), temperature=0)
    messages = [
        SystemMessage(
            content="You are a concise support assistant. Do not invent order status."
        ),
        HumanMessage(content="My order is delayed. What information do you need?"),
        AIMessage(content="Please share the order number and delivery postcode."),
        HumanMessage(content="The order number is A-104."),
    ]

    response = model.invoke(messages)
    print("Text:\n", response.text)
    print("\nMessage ID:", response.id)
    print("Usage metadata:", response.usage_metadata)
    print("Tool calls:", response.tool_calls)
    print("Response metadata keys:", list(response.response_metadata))


if __name__ == "__main__":
    main()
