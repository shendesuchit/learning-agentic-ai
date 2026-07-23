# 4. Understanding the Agentic Loop

This is the heart of the project.

## Why one model call is not enough

Suppose the model requests:

```text
get_weather(city="Pune")
```

That request contains no weather value. Python must execute the function. After execution,
Python has structured data:

```json
{"city": "Pune", "temperature_c": 27, "condition": "partly cloudy"}
```

The model has not seen this result yet. Therefore, the agent appends the tool result to the
messages and calls the model again.

## The loop in plain language

1. Ask the model what should happen.
2. If it answers, finish.
3. If it requests a tool, execute the tool.
4. Add the result to the conversation.
5. Ask the model again.

In this focused project, one round of tool requests is supported. The code still demonstrates
the essential loop without hiding it behind framework terminology.

## The crucial separation

- A **tool result** is machine-oriented data.
- A **final answer** is a human-oriented explanation.

Returning raw data immediately would skip the model's job of interpreting it in relation to
the original question.

See the [complete agent-loop visual](../visualizationDiagram/complete-agent-loop.md).

Next: [Conversation history and memory](05-conversation-history-and-memory.md).

