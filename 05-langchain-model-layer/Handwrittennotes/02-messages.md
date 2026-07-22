# Messages = supplied memory

```text
System  → rules / role
Human   → current request
AI      → previous model output + tool requests
Tool    → application result linked by tool_call_id
```

An LLM does not retain a prior API call. The application selects and sends the next message list.
