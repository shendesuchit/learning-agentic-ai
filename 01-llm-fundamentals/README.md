# Learning Agentic AI

A first-principles learning repository for building reliable AI applications. It begins before frameworks: with the boundary between a language model and the application around it.

## Learning path

| Module | Question it answers | Status |
| --- | --- | --- |
| [01 — LLM Fundamentals](01-llm-fundamentals/README.md) | What does an LLM see on one request, and why does that matter? | Complete |
| 02 — Working with LLM APIs | How do applications make safe, observable model requests? | Planned |
| 03 — Building Agents in Plain Python | How can a model select and use tools? | Planned |
| 04 — LangChain Foundations | What framework responsibilities are worth adopting? | Planned |

## A useful mental model

> The model is not the application. It is one component that produces an output from the context it receives for a single inference.

This module deliberately separates three ideas that beginners often merge:

| Term | What it is | Is it automatically visible to the model? |
| --- | --- | --- |
| Stored history | Messages saved by an application | No |
| Request context | Information assembled for one inference | Yes |
| Memory | A policy for retaining and retrieving useful information | No; it must be implemented |

## How to use this repository

Read the chapter files in numeric order. Run the dependency-free examples after Chapters 03 and 04. Use the study assets before revision or an interview.

The repository uses toy token budgets and generic request shapes on purpose. Exact token counts, limits, pricing, caching, and API payloads are model- and provider-specific; verify them against the documentation for the provider you choose.
