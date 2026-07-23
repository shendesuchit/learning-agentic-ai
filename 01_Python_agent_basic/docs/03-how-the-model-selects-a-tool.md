# 3. How the Model Selects a Tool

The agent sends three things to the model:

1. Instructions
2. Conversation messages
3. Available tool schemas

The model then produces one of two response shapes.

## Path A: answer directly

```json
{
  "role": "assistant",
  "content": "An AI agent is ..."
}
```

## Path B: request a tool

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call-1",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\": \"Pune\"}"
      }
    }
  ]
}
```

The model selects; Python controls. Python still checks the name, parses the arguments, and
decides which registered function may run.

## Why demo mode is useful

`DemoModel` uses simple, deterministic logic so you can observe these two response shapes.
It is not pretending to be intelligent. It isolates the mechanism we are studying.

When you later enable API mode, the model implementation changes, but `run_agent()` continues
to process the same type of response.

Explore the [tool-calling sequence](../visualizationDiagram/tool-calling-sequence.md), then
continue to [the agentic loop](04-understanding-the-agentic-loop.md).

