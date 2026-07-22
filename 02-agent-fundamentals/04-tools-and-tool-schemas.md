# How Does an Agent Safely Reach the Outside World?

A **tool** is capability that runs outside the model: a local Python function, an HTTP API call, a database query, or a carefully controlled business action. A **tool schema** is a machine-readable description of that capability supplied to the model.

## Tool versus schema

| Item | Lives in | Purpose |
|---|---|---|
| `get_weather(city)` | Application runtime | Executes the lookup and returns data |
| `get_weather` schema | Model request | Describes when and how the model may request the tool |
| Tool registry | Application runtime | Maps an approved name to its executable implementation |

For example, the model might receive this schema:

```json
{
  "name": "get_weather",
  "description": "Return current conditions for a supported city.",
  "parameters": {
    "type": "object",
    "properties": {"city": {"type": "string"}},
    "required": ["city"]
  }
}
```

The schema is like a service catalogue. It tells the planner which service exists and the form needed to request it. The catalogue does not perform the service.

## The tool-calling contract

1. The application sends the available schemas with the messages.
2. The model returns one or more requested calls with names, arguments, and IDs.
3. The application validates the name, arguments, user permission, and policy.
4. The application executes the tool—or safely returns an error.
5. The application appends a `tool` message linked to the matching `tool_call_id`.
6. The model receives the evidence in a new call and writes the final response or requests another tool.

The ID matters when more than one tool call is requested. It prevents the application and model from confusing which result belongs to which request.

## Design schemas for correct use

Good schemas reduce ambiguity. Use an explicit name, a precise description, clear parameters, and meaningful constraints. A tool called `search` with an unexplained free-text parameter is weaker than `search_customer_orders(customer_id, status)` with defined types and limits.

Even with a good schema, always validate. A model can request an unknown tool, omit a required value, or give a value that is syntactically valid but violates a business rule.

## Mock tools first

The example uses a fixed weather dictionary. That is intentional: it isolates the agent protocol from network failures, authentication, pricing, and changing live data. Swap the implementation for a real API only after the loop and validation are clear.

**Source basis:** S1, S2, S3. See the [source map](references/source-map.md).
