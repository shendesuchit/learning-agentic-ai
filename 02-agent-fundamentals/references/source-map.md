# Source Map and Technical Corrections

## Source inventory

| ID | Supplied source | Used for |
|---|---|---|
| S1 | `upload/11 July LangChain - 1.txt` | Model/chatbot/agent comparison; brain, memory, tools; schemas; raw-Python setup |
| S2 | `upload/12 July LangChain - 2.txt` | Tool-result protocol, repeated model calls, multiple calls, turn limits, caching discussion |
| S3 | `upload/06 - 12 July - Introduction to LangChain.md` | Compact recap of the raw-Python agent loop and framework boundary |
| S4 | `upload/Pasted markdown(3).md` | Two-mode analysis/build workflow constraints |
| S5 | [Live-Class-2026 repository](https://github.com/mayank953/Live-Class-2026) | Course-reference context: Agents in Python and LangChain transition |

## Chapter mapping

| Repository file | Primary sources |
|---|---|
| `01-from-llm-to-agent.md` | S1, S3 |
| `02-the-agent-brain.md` | S1, S2, S3 |
| `03-memory-is-managed-state.md` | S1, S2, S3 |
| `04-tools-and-tool-schemas.md` | S1, S2, S3 |
| `05-agent-architecture.md` | S1, S2, S3 |
| `06-the-agentic-loop-and-workflow-boundary.md` | S1, S2, S3 |
| `examples/main.py` | S1, S2, S3; simplified as a provider-free teaching simulation |

## Corrections applied during repository generation

| Source-level shortcut | Engineering correction used here |
|---|---|
| “The model is the brain.” | Useful analogy only. The model is an inference component; it has no direct execution or durable state. |
| “A chatbot has memory.” | Conversation continuity is application-managed state; it is not automatically persistent memory. |
| “Memory is a database.” | A database is one storage option. Memory is selected information supplied back to the model. |
| “The LLM decides which tool to call.” | It proposes a request. The application validates, authorizes, and executes. |
| “A response is text or a tool call.” | Provider formats vary; text and one or more tool calls may coexist. Treat responses as protocol objects. |
| “Max turns prevents problems.” | It bounds iterations only. Time, cost, tool failure, permissions, and auditability need their own controls. |

## Intentional omissions

This module does not claim that its mock tools are production-grade. Authentication, authorization, least privilege, durable memory, RAG, retries, circuit breakers, observability, and deterministic workflow orchestration are identified as later modules.
