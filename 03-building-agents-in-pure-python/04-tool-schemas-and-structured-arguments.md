# How Does a Model Know Which Tool It Can Use?

Imagine that an application contains ten ordinary Python functions. The model cannot inspect your source code, guess which function is safe, or call it directly. It needs a small, explicit contract describing each capability.

That contract is a **tool schema**.

## The problem

A function such as `get_weather(city: str, unit: str = "celsius")` is meaningful to Python, but not automatically to an LLM API. The application must expose a description of:

- the tool's stable name;
- what it is intended to do;
- the arguments it accepts;
- the expected type and constraints for each argument.

```json
{
  "name": "get_weather",
  "description": "Return the current weather for a supported city.",
  "parameters": {
    "type": "object",
    "properties": {
      "city": {"type": "string", "description": "City name"},
      "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["city"]
  }
}
```

The schema is sent with the conversation when the application invokes a tool-capable model. It gives the model vocabulary for making a structured request such as:

```json
{"name": "get_weather", "arguments": {"city": "Tokyo", "unit": "celsius"}}
```

## Schema, implementation, and registry are different things

These three concepts are often mixed together.

| Thing | Purpose | Visible to the model? |
| --- | --- | --- |
| Tool schema | Explains a capability and its inputs | Yes |
| Python implementation | Performs the actual work | No |
| Tool registry | Maps an approved tool name to its implementation | No |

The schema is an invitation, not permission to execute arbitrary code. The registry and validation logic remain under application control.

## A useful shape, not a universal wire format

Providers differ in the exact JSON envelope they expect. The stable idea is the same: a model receives a typed description and can return a structured request. Avoid writing documentation that assumes every provider uses identical field names.

Pydantic can help define and validate the arguments in Python, but it is not the tool itself. It is a convenient way to author a reliable contract.

## What a good schema prevents

Vague tool names and descriptions force the model to guess. Compare:

| Weak | Better |
| --- | --- |
| `search` | `search_customer_orders` |
| `Get data` | `Return orders for one authorised customer ID` |
| `query: string` | `customer_id: string`, `status: enum`, `limit: integer` |

The clearer schema reduces ambiguity, but it does not make model output trustworthy by itself. The next chapter explains why the application must still validate every requested call.

## What to remember

> A tool schema explains capability to the model. It does not grant the model execution authority.

## Sources

- [Source map](references/source-map.md#tool-schema-and-structured-arguments)
- Next: [Tool selection and execution](05-tool-selection-and-execution.md)
