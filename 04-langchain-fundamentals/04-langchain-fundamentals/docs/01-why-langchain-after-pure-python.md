# 1. Why LangChain After a Pure-Python Agent?

## The short answer

Pure Python is the right way to learn the agentic loop. It exposes every moving part. LangChain becomes useful when recreating those moving parts stops being educational and starts becoming repeated integration work.

In a hand-built agent, you normally own all of this:

```text
prepare messages → call provider SDK → inspect tool request →
validate arguments → execute function → append tool result →
call the model again → stop safely
```

That design is valuable because it makes the loop visible. But a production-oriented prototype quickly adds more work: provider adapters, tool-schema conversion, retries, consistent message objects, tracing, state persistence, streaming, and guardrails.

## What a framework changes

LangChain gives a common interface for common agent concerns. It does **not** make model capability equal across providers, and it does not make architectural choices for you.

| Responsibility | Manual implementation | With LangChain |
| --- | --- | --- |
| Model invocation | Call a provider-specific SDK | Use a standard model interface |
| Tool description | Write and maintain a schema | Infer schema from a callable or use a tool object |
| Agent loop | Write `while` and stopping logic | Let an agent harness orchestrate the usual loop |
| Messages | Build provider-specific payloads | Use a consistent message/state model |
| Cross-cutting policies | Scatter logic through application code | Attach middleware where appropriate |
| Tracing/evaluation | Design and operate it yourself | Integrate with an observability platform such as LangSmith |

## The trade-off is not “manual bad, framework good”

A framework trades some transparency for reusable conventions. That is often a good trade after you understand the underlying loop. It is a bad trade when a learner treats `create_agent()` as a magic command and cannot debug an unexpected tool call.

Use raw Python when you are learning, experimenting with unusual control flow, or need total control. Use LangChain when conventional orchestration and integrations reduce more work than the abstraction costs.

## Portability has limits

The following statement is directionally useful but incomplete:

> “Change the model string and any provider works.”

Changing a provider also requires the matching integration package, credential configuration, and a model with the required features. Tool calling, structured output, multimodality, latency, pricing, and quotas vary by model. A uniform interface reduces adapter code; it cannot erase provider differences.

## Takeaway

LangChain’s value is not that it makes an LLM intelligent. Its value is that it helps engineers compose and operate the harness around the LLM without rebuilding standard plumbing every time.

Next: [What turns a model into a useful system?](02-agent-harness-model-to-useful-system.md)
