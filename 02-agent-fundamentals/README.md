# Agent Fundamentals

An LLM can produce useful language, but it cannot independently keep application state, access a weather service, or run local Python. An **agent** is the controlled application loop that supplies context to a model, lets it request approved capabilities, executes those capabilities, and returns the evidence to the model for a final response.

This module explains that loop before any framework hides it.

## Learning path

1. [From LLM to Agent](01-from-llm-to-agent.md)
2. [The Agent Brain](02-the-agent-brain.md)
3. [Memory Is Managed State](03-memory-is-managed-state.md)
4. [Tools and Tool Schemas](04-tools-and-tool-schemas.md)
5. [Agent Architecture](05-agent-architecture.md)
6. [The Agentic Loop and Workflow Boundary](06-the-agentic-loop-and-workflow-boundary.md)

## Run the example

The example is deliberately provider-free: it uses a tiny deterministic `simulated_model` so you can inspect the agent protocol without an API key or framework.

```bash
cd 02-agent-fundamentals
python examples/main.py
```

It demonstrates two paths:

- a direct model answer, where no tool is needed;
- a tool path, where the model requests `get_weather`, the application validates and runs it, then the model receives a tool-result message and answers.

In a real system, replace only `simulated_model` with a provider client. The host application's responsibilities—message state, validation, permissions, execution, time limits, and observability—remain.

## Module boundaries

Included: brain, memory, tools, schemas, architecture, and the bounded agentic loop.

Deliberately deferred: provider API setup, durable memory and RAG, authentication and authorization design, production resilience, LangChain, LangGraph, and multi-agent systems.

## Study assets

- [Component and runtime diagrams](visualizationDiagram/)
- [Handwritten-style notebook notes](Handwrittennotes/agent-fundamentals-notes.md)
- [Fast revision sticky notes](StickyNotes/agent-fundamentals-revision.md)
- [Source map and corrections](references/source-map.md)

## Core mental model

> The model proposes language or an action request. The application owns every real action.

This distinction is the foundation for building agents that are useful without being uncontrolled.
