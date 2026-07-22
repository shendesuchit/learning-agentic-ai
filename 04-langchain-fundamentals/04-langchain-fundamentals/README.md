# LangChain Fundamentals — From a Manual Agent Loop to a Harness

This module is the bridge between a hand-built Python agent and LangChain's `create_agent()` API. The goal is not to memorize framework calls. It is to recognise which engineering responsibilities LangChain takes on and which responsibilities still belong to you.

## What you will learn

1. Why a framework becomes useful after a pure-Python agent works.
2. Why an agent is better understood as **model + harness**.
3. Where LangChain, LangGraph, Deep Agents, and LangSmith fit.
4. How to create a small, reproducible project with `uv` and safe secret handling.
5. What `create_agent()` configures and what happens during `invoke()`.
6. Which component to study next: models, tools, state, middleware, structured output, streaming, and observability.

## Prerequisites

- Python functions and virtual environments.
- The model → chatbot → agent distinction.
- The manual agentic loop: model → tool call → tool result → model.

If the loop is still unclear, revisit the earlier **Agent Fundamentals** and **Agentic Loop** modules first. LangChain makes the loop easier to compose; it does not remove the need to understand it.

## Reading path

| Order | Lesson | Question answered |
| --- | --- | --- |
| 1 | [Why LangChain after pure Python?](docs/01-why-langchain-after-pure-python.md) | What becomes repetitive in a real agent? |
| 2 | [Model to useful system](docs/02-agent-harness-model-to-useful-system.md) | What is a harness? |
| 3 | [The LangChain family](docs/03-langchain-family-choosing-the-right-layer.md) | Which product solves which problem? |
| 4 | [Safe project setup](docs/04-project-setup-uv-credentials-and-reproducibility.md) | How do I start without leaking secrets? |
| 5 | [Smallest `create_agent()`](docs/05-create-agent-smallest-langchain-agent.md) | What does the convenience API do? |
| 6 | [Components and next steps](docs/06-agent-components-and-what-comes-next.md) | What should I learn next? |

## Run the example

```bash
cd examples/01_weather_agent
cp .env.example .env
# Add your provider key to .env; never commit this file.
uv sync
uv run python main.py
```

The sample uses OpenAI only to keep the first example focused. LangChain itself does not require an API key; the selected model provider does. A local provider may use a different setup or no hosted-provider key at all.

## Visual revision aids

- [Architecture and execution diagrams](visualizationDiagram/)
- [Handwritten-style cheat sheet](Handwrittennotes/langchain-fundamentals-cheat-sheet.md)
- [Sticky-note revision cards](StickyNotes/misconceptions-and-revision-cards.md)

## Source discipline

The teaching sequence comes from the supplied class transcripts. Framework-specific behavior has been checked against the current official documentation. See [references/sources.md](references/sources.md).

## Next module

**LangChain Models and Messages**. `create_agent()` receives a model and communicates through messages, so model configuration and message state are the next foundations to make explicit.
