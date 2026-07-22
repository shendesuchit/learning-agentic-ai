"""Demonstrate state selection without hiding it behind a memory abstraction."""

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage


def build_request_state(
    durable_summary: str, recent_messages: list[BaseMessage]
) -> list[BaseMessage]:
    """Keep durable facts compactly, then retain a small window of recent turns."""
    return [
        SystemMessage(
            "Use this prior-conversation summary as context. "
            "If a critical fact is missing, ask rather than invent it.\n\n"
            f"Summary: {durable_summary}"
        ),
        *recent_messages[-4:],
    ]


def main() -> None:
    durable_summary = (
        "Customer: Priya. Product: annual Pro plan. Unresolved issue: duplicate charge. "
        "Never expose payment data; ask for the last four digits only if identity verification is needed."
    )
    recent_messages = [
        HumanMessage("I also need the invoice for the second charge."),
        HumanMessage("Can you tell me what you need from me?"),
    ]

    state = build_request_state(durable_summary, recent_messages)
    for message in state:
        print(f"{message.type}: {message.content}\n")


if __name__ == "__main__":
    main()
