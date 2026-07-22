# The LangChain Model Layer

This module turns a raw chat-model call into a dependable application boundary. You will configure a provider-neutral model, construct messages, choose an execution mode, handle tool requests, and turn model output into typed Python data.

## Why this module exists

An LLM API call is not yet an agent. Before an agent can reason over tools, its application must know how to:

1. select and configure a model;
2. express conversation state as structured messages;
3. consume complete, streamed, or concurrent responses;
4. treat tool calls as requests that application code must validate and execute; and
5. validate data returned to the rest of the program.

LangChain offers a common programming interface for those tasks. It does **not** make every provider, model, capability, limit, or security concern the same.

## Learning path

| Chapter | Question it answers | Example |
| --- | --- | --- |
| [01](docs/01-the-model-interface.md) | Why use `init_chat_model()`? | `01_init_and_config.py` |
| [02](docs/02-configuring-a-model-call.md) | Which settings affect quality and reliability? | `01_init_and_config.py` |
| [03](docs/03-messages-are-the-conversation.md) | What does the model actually receive and return? | `02_messages_and_metadata.py` |
| [04](docs/04-invocation-streaming-and-batching.md) | When should a request wait, stream, or run independently? | `03_invoke_stream_batch.py` |
| [05](docs/05-tool-binding-is-not-tool-execution.md) | What happens when a model asks for a tool? | `04_bind_tools_manual_loop.py` |
| [06](docs/06-typed-output-and-context-control.md) | How does a text response become safe application data? | `05_structured_output.py`, `06_context_summary_pattern.py` |

## Setup

```bash
cd 05-langchain-model-layer
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -e .
export OPENAI_API_KEY="..."  # PowerShell: $env:OPENAI_API_KEY="..."
python examples/01_init_and_config.py
```

The examples use an OpenAI-style model string only as a concrete default. Replace it with a provider/model that your account and installed LangChain integration support. Never commit API keys.

## Repository map

```text
05-langchain-model-layer/
├── docs/                   # progressive engineering explanations
├── examples/               # small, independently runnable programs
├── visualizationDiagram/   # editable Mermaid and SVG diagrams
├── Handwrittennotes/       # compact study notes + visual cheat sheet
├── StickyNotes/            # misconceptions worth remembering
└── tests/                  # deterministic checks with no model/API call
```

## Completion criteria

You are ready for LangChain tool-calling and agent execution when you can explain why:

- a message list is application state, not just prompt text;
- streaming optimizes perceived responsiveness, while batching handles independent work;
- `bind_tools()` gives the model a schema but does not run Python; and
- valid Pydantic output is not automatically true, authorized, or business-valid.

## Sources and version note

The teaching flow was derived from the supplied course transcripts and class summaries. Framework APIs change; before adopting code in a production service, verify the installed package version against [LangChain’s model documentation](https://docs.langchain.com/oss/python/langchain/models) and the relevant provider integration.

See [docs/references.md](docs/references.md) for the source map and external documentation.
