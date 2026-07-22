# Building Agents in Pure Python: Agentic Loop

An LLM can recommend that a tool should be used. It cannot run the tool by itself.

This section builds the application-side control loop that makes tool use useful:

```text
model requests a tool → application executes it → model receives the result → model answers
```

The loop is deliberately explained before LangChain. A framework can automate the mechanics, but it cannot remove the need to understand message ordering, validation, stopping conditions, or the boundary between model choice and application authority.

## Reading path

1. [Tool schemas and structured arguments](04-tool-schemas-and-structured-arguments.md)
2. [Tool selection and execution](05-tool-selection-and-execution.md)
3. [The agentic loop](06-the-agentic-loop.md)
4. [Calling the model again after execution](07-calling-the-model-again-after-tool-execution.md)
5. [Stopping conditions and maximum iterations](08-stopping-conditions-and-maximum-iterations.md)

## Run the example

The example uses a scripted model, so it needs only Python 3.11+ and has no third-party dependencies.

```bash
uv run python 03-building-agents-in-pure-python/examples/agentic-loop/main.py
```

If you are not using `uv`, `python 03-building-agents-in-pure-python/examples/agentic-loop/main.py` works too.

It demonstrates a direct response, a single tool call, multiple tool calls, an unknown tool, and a loop that reaches its iteration limit.

## Keep this mental model

| Responsibility | Owner |
| --- | --- |
| Decide whether a tool might help | Model |
| Define permitted tools | Application developer |
| Validate tool names and arguments | Application |
| Execute the tool | Application |
| Store the interaction state | Application |
| Turn tool output into a useful response | Model, after re-invocation |
| Stop unsafe or excessive work | Application |

## Source trail

The primary class evidence is mapped in [references/source-map.md](references/source-map.md). The model/tool loop is introduced in the raw-Python transcript and then shown again through LangChain's `create_agent()` abstraction.

## Where this leads

Once the loop is clear, framework APIs become easier to inspect: `agent.invoke()` is not magic. It performs the same branch, execution, message append, and re-invocation cycle described here.
