# When Must an Agent Stop?

An agentic loop should not run simply because it can. Each model call costs time and usually money; each tool call can fail or change an external system. The application needs explicit terminal conditions.

## Normal completion

The usual successful condition is simple:

```text
The latest model response contains no requested tool calls and contains a final user-facing response.
```

## Safety completion

A production-minded agent needs additional limits.

| Guardrail | What it controls | Example response |
| --- | --- | --- |
| Maximum iterations | Repeated model/tool cycles | “Stopped after the allowed number of turns.” |
| Maximum tool calls | Excessive actions inside one request | “Too many tool operations were requested.” |
| Time budget | Slow models or external tools | “The request timed out before completion.” |
| Token/cost budget | Runaway context or expensive calls | “The request exceeded its processing budget.” |
| Consecutive-error limit | Repeated failing tools | “The required service is currently unavailable.” |
| Approval boundary | Consequential side effects | “Please confirm before I submit this booking.” |

## Why `max_iterations` is still valuable

The class example uses a small `max_turns` value. The exact number is a product decision, not a universal constant. Its value is that it gives the runtime a predictable escape route when the model repeatedly asks for tools or fails to reach a final answer.

```python
for _ in range(max_iterations):
    # invoke model, execute permitted tools, append results
    ...

return "Maximum iterations reached without a final answer."
```

This cap is necessary but not sufficient. A two-turn loop can still be expensive if the tools are slow or destructive; a ten-turn loop might be safe in a read-only research workflow. Choose controls based on the capability and risk of each tool.

## Failure states should be explicit

Do not blur these outcomes into one generic error:

- **final answer produced**;
- **tool unavailable or unauthorised**;
- **arguments invalid**;
- **tool failed or timed out**;
- **budget exhausted**;
- **user approval required**.

Clear states improve debugging, observability, user trust, and safe retries.

## Framework connection

Frameworks can provide recursion limits, retries, callbacks, checkpoints, and tracing. They do not decide your safety policy for you. Before relying on a framework default, identify which budget it limits and what happens when that budget is reached.

## Sources

- [Source map](references/source-map.md#loop-iteration-and-termination)
- Previous: [Calling the model again](07-calling-the-model-again-after-tool-execution.md)
- Next: combine these pieces in the complete pure-Python agent chapter.
