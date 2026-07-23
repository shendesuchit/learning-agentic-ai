# 7. Guided Practice

Complete these exercises in order. Run `python main.py --self-test` after each change.

## Exercise 1: add sample data

Add your city to `SAMPLE_WEATHER`, then ask the agent about it.

**Observe:** Does the tool receive the same city spelling that you typed?

## Exercise 2: inspect quiet mode

Compare:

```bash
python main.py "What is the weather in Pune?"
python main.py --quiet "What is the weather in Pune?"
```

**Explain:** Which details belong to the agent's internal execution and which belong to the
user-facing answer?

## Exercise 3: create a normal Python tool

Create this function:

```python
def add_numbers(first: float, second: float) -> dict[str, float]:
    return {"result": first + second}
```

Then complete all three integration steps:

1. Add its schema to `TOOL_SCHEMAS`.
2. Add it to `TOOL_REGISTRY`.
3. Extend `DemoModel` so a suitable question requests it.

**Lesson:** Writing a function is only one part of exposing a tool.

## Exercise 4: draw the messages

For one weather question, write every message on paper in chronological order. Label the
message roles: `system`, `user`, `assistant`, and `tool`.

If you can explain why the final model call needs all four, you understand the core mechanism.

