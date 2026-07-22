# 03 — Messages are the conversation

A chat model does not remember previous calls by itself. If the application wants continuity, it sends the relevant prior state again. LangChain represents that state as typed message objects rather than one large, ambiguous string.

```python
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

messages = [
    SystemMessage("You are a precise support assistant. Cite only supplied facts."),
    HumanMessage("My order is delayed. What should I do?"),
    AIMessage("I can help. Please share the order number."),
    HumanMessage("It is A-104."),
]
response = model.invoke(messages)
```

## Common message roles

| Message | Who/what created it | Why it exists |
| --- | --- | --- |
| `SystemMessage` | application | Durable instructions, boundaries, audience, output contract |
| `HumanMessage` | user/application | User intent, follow-up, files or multimodal content where supported |
| `AIMessage` | model | Previous answer, metadata, and sometimes `tool_calls` |
| `ToolMessage` | application | A tool result attached to the tool-call ID that requested it |

The exact provider mapping may vary, but the state model is consistent: each message records *who said what* and sometimes more than plain text.

## Read responses as objects

An `AIMessage` may contain text/content, model/provider metadata, usage metadata, IDs, and tool-call requests. For a quick demo, printing `.text` is convenient. In an application, inspect metadata carefully and decide which fields are safe to persist or expose.

```python
response = model.invoke("Give one SQL indexing tip.")
print(response.text)
print(response.usage_metadata)  # may be absent or provider-dependent
print(response.tool_calls)      # [] unless the model requested tools
```

## History and few-shot examples

Message history provides continuity but consumes the context window. A few carefully selected `HumanMessage`/`AIMessage` pairs can show the output style better than a long instruction. Neither approach gives the model durable memory; the application owns selection, retention, summarization, and privacy.

See [the message example](../examples/02_messages_and_metadata.py), then continue to [execution modes](04-invocation-streaming-and-batching.md).
