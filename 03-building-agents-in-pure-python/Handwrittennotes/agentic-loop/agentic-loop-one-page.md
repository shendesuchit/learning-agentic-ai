# Agentic Loop — One-Page Notebook Notes

## The short definition

An agentic loop is a controlled cycle where the model requests a tool, the application runs it, and the model sees the result before answering.

## Five things to draw

1. **Model** — chooses a possible tool.
2. **Tool schema** — tells the model what tools exist and what arguments they need.
3. **Tool registry** — application-owned mapping from tool name to Python function/API.
4. **Tool result message** — observation returned to the model with the matching call ID.
5. **Stop condition** — final response, error, or budget limit.

## The key distinction

```text
Tool selection = model output
Tool execution = application code
```

## The loop

```text
user message
  ↓
model decides: answer OR request tool
  ↓
application validates and executes tool
  ↓
append tool result to messages
  ↓
model sees result and answers / requests another tool
```

## Do not forget

- Keep the assistant tool-call message and the tool-result message in order.
- Match every result to `tool_call_id`.
- Never execute a tool only because the model named it.
- `max_iterations` prevents unbounded looping; it is not the complete safety strategy.
