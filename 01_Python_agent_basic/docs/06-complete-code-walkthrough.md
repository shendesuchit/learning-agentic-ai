# 6. Complete Code Walkthrough

Read [`main.py`](../main.py) in its numbered order.

## Section 1: the tool

`get_weather()` is ordinary Python. Test it independently before thinking about models.

```python
print(get_weather("Pune"))
```

## Section 2: schema and registry

`TOOL_SCHEMAS` teaches the model how to request the function. `TOOL_REGISTRY` lets Python
resolve that request to approved executable code.

## Section 3: model adapters

Both model classes provide a `complete(messages, tools)` method:

- `DemoModel` works offline and produces predictable responses.
- `OpenAICompatibleModel` sends an HTTP request to a configured model endpoint.

Because they share an interface, the agent loop does not care which implementation it uses.

## Section 4: the loop

`run_agent()` owns the message list and coordinates every step. `execute_tool_call()` handles
the boundary between model-generated JSON and a real Python function.

## Section 5: command line and tests

The command-line layer accepts the learner's question. `run_self_tests()` verifies both the
direct-answer path and tool-calling path without extra testing libraries.

## Trace the program yourself

Run:

```bash
python main.py "What is the weather in Pune?"
```

For each printed step, locate the corresponding line inside `run_agent()`. This is more
valuable than memorising the full file.

Next: [Guided practice](07-guided-practice.md).

