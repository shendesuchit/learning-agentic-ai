# 2. Understanding Tools

## A function is not automatically a model tool

Python understands this function signature:

```python
def get_weather(city: str) -> dict[str, object]:
    ...
```

But a language model cannot inspect your running Python program. We must separately describe
the function in a structured **tool schema**.

## The two halves

| Half | Audience | Responsibility |
|---|---|---|
| Python function | Python runtime | Performs the real operation |
| Tool schema | Model | Explains name, purpose, and arguments |

The schema in this project says that `get_weather` accepts one required string named `city`.
That is enough information for the model to create a structured request such as:

```json
{
  "name": "get_weather",
  "arguments": "{\"city\": \"Pune\"}"
}
```

Notice that `arguments` may arrive as a JSON **string**. Python must parse it before calling
the function.

## The registry

The tool registry is the safe bridge from a model-produced name to real code:

```python
TOOL_REGISTRY = {"get_weather": get_weather}
```

The model returns the text `get_weather`; the registry retrieves the function object.

## Important distinction

The schema does not execute anything. It is similar to a restaurant menu: the menu describes
what can be ordered, while the kitchen performs the work.

Next: [How the model selects a tool](03-how-the-model-selects-a-tool.md).

