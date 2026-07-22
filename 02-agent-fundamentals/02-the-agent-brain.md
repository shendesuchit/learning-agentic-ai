# What Does the LLM Actually Do Inside an Agent?

Calling the model the agent’s **brain** is a helpful shortcut, provided we do not take it literally. The model is an inference service: it receives a constructed context and produces a probabilistic output. It does not hold the tool’s Python reference, open a database connection, or decide its own security policy.

## The model boundary

At each turn, the harness sends the model a structured request containing some combination of:

- instructions that describe the job and constraints;
- messages from the current conversation;
- schemas for tools the application is willing to expose; and
- optional configuration, such as output limits.

The model may return ordinary text. Or it may return a structured request such as:

```json
{
  "tool_call_id": "call_123",
  "name": "get_weather",
  "arguments": {"city": "Pune"}
}
```

This is a proposal, not an execution. The application must still check that `get_weather` is registered, that `city` is valid, that the user is allowed to use it, and that invoking it is safe.

## Decision support, not authority

The model is valuable because it can map an open-ended user request to an available capability and then turn a raw result into helpful language. It is not reliable enough to be the final authority on:

- whether an action should be allowed;
- whether arguments satisfy business rules;
- whether the result is fresh, complete, or trustworthy; or
- whether the loop should continue indefinitely.

For example, a model might propose `refund_customer` with a malformed order identifier. A production harness must reject that request before any external side effect happens. “The model chose it” is not a valid authorization policy.

## One call has no hidden state

When a model call finishes, it does not remember the previous one by itself. The next chapter explains how the application makes continuity possible by managing the message history.

**Source basis:** S1, S2, S3. See the [source map](references/source-map.md).
