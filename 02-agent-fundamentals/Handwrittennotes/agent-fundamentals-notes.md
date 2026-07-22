# Agent Fundamentals — Notebook Notes

## One-line definition

**Agent = Model + managed state + approved tools + a bounded control loop.**

## The four boxes

```text
Brain  → model proposes text / tool call
Memory → app stores selected messages and results
Tools  → app-owned functions or APIs do real work
Harness → app validates, executes, records, stops
```

## The truth behind the “brain” analogy

- LLM is not a Python runtime.
- LLM does not retain state after a call.
- LLM does not automatically have access to tools.
- LLM proposes; the host application decides whether anything happens.

## Memory

`user message → assistant tool request → tool result → final answer`

All four can become part of the next model call.

Memory is **information supplied back to the model**, not automatically a database or permanent storage.

## Tool = schema + implementation

```text
Schema: name + description + parameter contract
Implementation: actual Python/API code
Registry: approved mapping from name → function
```

Schema tells the model what it may request. It does not run the tool.

## Agentic loop

```text
1. Add user input to messages
2. Call model with messages + tool schemas
3. Text answer? Return it
4. Tool request? Validate it
5. Execute approved tool
6. Add tool result to messages
7. Call model again
8. Stop at max turns / time / budget
```

## Safety sentence to remember

**Never grant authority merely because the model requested an action.**

## Agent vs workflow

- Workflow: application decides the next step.
- Agentic loop: model can propose the next approved step.
- Real systems often combine both.
