# How Does an Agent Remember What Just Happened?

The model only sees the input included in the current request. If an agent should remember that the user asked about Tokyo, the application must store that fact and include the relevant state in a future request.

## Start with message history

For a small chat session, memory can be a list of protocol messages:

```python
messages = [
    {"role": "user", "content": "What is the weather in Tokyo?"},
    {"role": "assistant", "tool_calls": [...]},
    {"role": "tool", "tool_call_id": "call_123", "content": "..."},
    {"role": "assistant", "content": "Tokyo is 24°C and clear."},
]
```

The key insight is that tool output is also memory. Without recording it, the next model call cannot ground its final answer in the tool’s result.

## Memory is not a database

“Memory” describes information selected for a model call; it does not prescribe where that information lives.

| Need | Possible approach | Important trade-off |
|---|---|---|
| One active script | In-memory list | Simple, but disappears on restart |
| Resume a conversation | Database-backed messages | Needs retention, privacy, and retrieval rules |
| Long conversation | Summary plus recent messages | Saves tokens but can lose detail |
| Domain knowledge | Retrieval results | Needs source quality and access control |

At this stage, keep the model simple: an in-memory message list is enough to understand the protocol. It is *session state*, not durable long-term memory.

## Context is a budget

History grows with every user message, assistant answer, and tool result. That affects context-window capacity, latency, and cost. A real application therefore chooses what to carry forward; it does not blindly append forever.

Useful future strategies include trimming old turns, summarising verified history, retrieving relevant facts, and enforcing a data-retention policy. Those are separate engineering topics, not magic capabilities of the model.

## Next step

Memory provides continuity, but it does not give the system a live-weather lookup or the ability to update another system. That requires tools and a precise contract for using them.

**Source basis:** S1, S2, S3. See the [source map](references/source-map.md).
