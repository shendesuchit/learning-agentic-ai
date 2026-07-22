# LLM Fundamentals — Source Map and Corrections

This repository is derived from the supplied class materials. The raw transcript is treated as a learning source, not as an authority for provider-specific behaviour or current commercial terms.

## Supplied material

| Source | Used for | Scope decision |
| --- | --- | --- |
| `5 July GenAl Basics & Agentic Al.txt` | Token discussion, stateless API calls, chat-history rebuilding, context growth, Web App/API comparison | Primary transcript |
| `04 - 5 July - Anatomy of an Agent.md` | Distilled explanations and initial visual framing | Companion notes |
| `Pasted markdown(2).md` | Repository-generation requirements | Governing prompt |
| `https://github.com/mayank953/Live-Class-2026` | Named reference | Not used as an evidence source: it was unavailable for direct inspection in the analysis environment |

## Chapter-to-source map

| Repository chapter | Main source basis | Important enrichment/correction |
| --- | --- | --- |
| Tokens | Both class sources | Avoids fixed token-to-word ratios |
| Web App vs API | Both class sources | Avoids treating pricing analogies as provider guarantees |
| Statelessness | Both class sources | Separates model state from application state |
| Conversation reconstruction | Both class sources | Explains that products may use selection, summaries, retrieval, and caching—not necessarily full-history replay |
| Context window | Both class sources | Separates model capacity from current request occupancy and overflow policy |
| Token growth | Both class sources | States caching and application policy caveats; recommends measurement |
| Knowledge cutoff | User-requested module scope | Kept conceptual; no unsupported provider claims |

## Technical corrections preserved in the repository

| Classroom shorthand | Engineering interpretation |
| --- | --- |
| “The entire chat history is resent every time.” | A model can use only the current context. An application/product may use full history, selected turns, summaries, retrieved facts, tool results, or cached prefixes. |
| “The oldest content falls off.” | Exceeding capacity can produce rejection, truncation, summarisation, selection, or altered output allowance, depending on the system. |
| “A new chat makes the cost zero.” | A new chat may remove much user-visible history, but instructions, summaries, profiles, or tool definitions can remain. |
| “Long chats are slow and expensive.” | Larger/less-focused context creates pressure on cost, latency, capacity, and quality, but the curve depends on model, cache, and application policy. |
| “Web App is a buffet; API is pay per token.” | Web products and APIs have different interaction/control models; current commercial terms must be verified per provider and plan. |

## Later modules, intentionally excluded

- Embeddings, vector stores, semantic retrieval, and RAG
- Tools, tool schemas, execution loops, and agents
- Provider-specific SDK calls, credentials, streaming, retries, and structured output
- Long-term memory policies, evaluation, retention, and privacy engineering

## Reference practice for the next module

For provider APIs, cite the official documentation for the exact model and endpoint being implemented. Record the documentation access date, because payload shapes, context limits, rates, and behaviour change.
