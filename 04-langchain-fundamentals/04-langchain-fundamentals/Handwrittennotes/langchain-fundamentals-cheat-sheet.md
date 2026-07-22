# LangChain Fundamentals — Handwritten Revision Sheet

> ## One-line memory hook
>
> **Model = brain. Harness = the surrounding system that gives it instructions, tools, state, and safety rules.**

---

## Why LangChain?

```text
Pure Python teaches the loop.
LangChain reduces repeated integration + orchestration work.
```

- It gives conventions—not magic.
- It standardises interfaces—not model capability.
- Understand the loop before relying on the helper.

## `create_agent()` mental model

```text
create_agent(model, tools, system_prompt)
          ↓
configures an agent harness
          ↓
invoke(messages)
          ↓
model → tool? → tool result → model → final answer
```

## Family map

| Name | Remember it as |
| --- | --- |
| LangChain | Agent harness |
| LangGraph | Explicit workflow control |
| Deep Agents | Ready-made agent patterns |
| LangSmith | Trace, test, evaluate |

## Setup safety

```text
.env          = real secret → never commit
.env.example  = placeholders → commit
.gitignore    = protects local secrets
pyproject.toml = dependencies and project definition
```

## Common traps

- “Framework = model” → No. Framework orchestrates; model reasons/generates.
- “Memory is automatic” → No. Persisted state needs a checkpointer + thread identity.
- “Any model string works” → No. Check integration, credentials, access, and tool calling.
- “One-line agent = production ready” → No. Add validation, policy, errors, tracing, and authorization.

## Next topic

**Models and messages** — because every agent starts by sending message state to a chosen model.
