# Weather Agent Example

This runnable example is deliberately small. It uses one Python function as a tool and prints the complete message state so you can observe the agentic loop.

## Run it

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY.
uv sync
uv run python main.py
```

## What to observe

For a weather request, the output should contain a user message, an AI tool-call message, a tool result, and a final AI message. The exact objects and wording vary by model.

The tool returns mock data. Replacing it with a live API is intentionally deferred until the tools module.
