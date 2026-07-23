# Sources and Validation

## Supplied course material

| Source | Used for |
| --- | --- |
| `06 - 12 July - Introduction to LangChain(2).md` | Pure-Python-to-framework transition, initial `create_agent()` example, setup habits |
| `07 - 18 July - LangChain - 1(1).md` | Harness framing, LangChain family, project setup, components map |
| `11 July LangChain - 1(2).txt` | Model/chatbot/agent prerequisite context |
| `12 July LangChain - 2(2).txt` | Why LangChain, harness, family, and setup discussion |
| `18 July Lanchain - 2 - Concepts(1).txt` | Setup, providers, credentials, and terminology |
| `19 July Lanchain -3 Continued - POC & Mini Project.txt` | Boundary check for later content |

## Official LangChain documentation

- [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview)
- [Agents and `create_agent`](https://docs.langchain.com/oss/python/langchain/agents)
- [Middleware overview](https://docs.langchain.com/oss/python/langchain/middleware/overview)

## Corrections applied during repository generation

1. LangChain itself does not require an API key; a selected hosted provider usually does.
2. Changing a provider string is not sufficient without the compatible integration, credentials, access, and model capabilities.
3. `create_agent()` is an abstraction over the agentic loop, not a replacement for the underlying concepts.
4. Persistent memory needs explicit state/checkpoint configuration and a stable thread identity.
5. Middleware can shape behaviour across the loop; it is broader than tool before/after hooks.
6. LangSmith is an observability/evaluation platform and is not limited to LangChain applications.
