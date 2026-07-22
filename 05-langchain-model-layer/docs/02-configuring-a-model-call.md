# 02 — Configure a call deliberately

Model parameters fall into two different categories: controls that influence sampled output and controls that define an operational budget. Do not blur them together.

| Parameter | Primary purpose | Practical guidance |
| --- | --- | --- |
| `temperature` | Sampling variability | Lower for repeatable extraction/classification; higher only when variety is useful. It is not a “thinking” or direct cost dial. |
| `max_tokens` | Generated-output budget | Set an explicit ceiling that fits the feature. It does not expand the model’s context window. |
| `timeout` | How long one request may wait | Use a product-specific time budget; a background job and interactive chat need different values. |
| `max_retries` | Retry attempts for eligible transient failures | Make this explicit policy. Defaults and retryable errors vary by provider/integration. |

```python
model = init_chat_model(
    "openai:gpt-4.1-mini",
    temperature=0.2,
    max_tokens=300,
    timeout=20,
    max_retries=2,
)
```

## Temperature, without mythology

The model assigns likelihoods to possible next tokens. Temperature changes how sharply it prefers high-probability choices. A lower value generally makes choices more concentrated; a higher value permits more variation. It cannot guarantee factuality or determinism, and some providers impose their own constraints.

Cost depends on the provider’s pricing and the actual input/output (and, where applicable, reasoning) tokens. Temperature may change response length indirectly, but it is not a direct cost control.

## Token limits: three different limits

Do not assume `max_tokens` repairs every “too many tokens” error.

- **Input tokens:** prompt + message history + tool schemas + document context.
- **Output tokens:** the answer the model may generate; `max_tokens` usually caps this.
- **Context window:** the combined amount a particular model can accept under its rules.

Reducing history or retrieved context is the usual response to an input/context overflow. Increasing output budget can make an output too short problem worse if the combined context is already near its limit.

## Reliability needs a policy

A retry can help with transient overload or a brief network fault. It should not blindly repeat invalid credentials, a malformed request, or a rejected safety policy. Production code normally also uses exponential backoff, jitter, request deadlines, cancellation, rate/concurrency limits, and idempotency protection for side effects.

Use [the example](../examples/01_init_and_config.py) to make the choices visible. Next: [messages](03-messages-are-the-conversation.md).
