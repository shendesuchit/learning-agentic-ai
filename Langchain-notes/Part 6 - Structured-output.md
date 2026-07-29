# Structured Output: Provider Strategy → Tool Strategy → Union Schemas

*Module: learning-agentic-ai · Level: Beginner · Language: Python · Framework: LangChain*

---

## 1. Engineering Problem

Picture a movie-booking assistant, Cinebot. A customer types "I want to watch Inception tonight, 2 tickets." Cinebot replies with a nice sentence confirming the booking. A second customer asks something almost identical, and this time the reply comes back with the seat numbers listed differently, no showtime mentioned, and the ticket count buried in a sentence you'd need a regex to pull out. A third customer gets a response that mentions a movie title that isn't quite what they typed.

None of these are "wrong" answers in the sense that a human reading them would be confused. They're wrong in the sense that matters to you as an engineer: your backend needs `{"movie": str, "showtime": str, "seats": int}` to actually reserve the tickets, and free text doesn't reliably give you that. You can't build a booking system, an order pipeline, a form-filling flow, or anything that hands off to code, on top of "the model said something reasonable." You need a guarantee about *shape*, not just content.

That's the problem structured output solves: forcing a model's response into a schema your code can trust, every single time, not just when the model happens to feel like it.

---

## 2. Why This Concept Exists

Before structured output was a first-class feature, engineers dealt with this by prompt-engineering their way to JSON — "please respond only in valid JSON matching this format" — and then wrapping the parse in a `try/except` and hoping. It worked often enough to ship, and failed often enough to be a real production liability: malformed JSON, extra commentary before or after the JSON block, fields renamed slightly, numbers returned as strings. All the failure modes you'd expect from asking a text generator to also be a strict data contract, with nothing enforcing the contract but a polite request.

Structured output exists to close that gap by making schema conformance the model provider's job (when it can do it natively) or LangChain's job (when the provider can't), instead of your prompt's job. You define a schema once — a Pydantic model is the natural fit here since it's how most Python engineers already define data contracts — and the framework guarantees the response either matches it or fails loudly, not silently.

The reason there isn't just *one* mechanism for this, and instead a layered set of strategies, is that not every model provider supports structured output the same way. Some have a native "constrained decoding" or "JSON schema" feature baked into their API. Some don't, or only support it inconsistently. LangChain needs a way to give you the same guarantee regardless of which model is underneath — which is exactly why Provider Strategy and Tool Strategy both exist as options, not just one.

---

## 3. How the Instructor Taught It

The instructor introduced structured output by breaking Cinebot on purpose. He asked it the same kind of question three different ways in free text and showed, live, that the three responses had three different shapes — no consistent set of fields, no consistent formatting, nothing a backend could parse without writing bespoke logic for every phrasing the model happened to choose. His framing was direct: "the model can be right in content and still be useless to your code if the shape isn't guaranteed."

From there he built up structured output as a two-strategy system, and was careful to teach *why* two strategies exist rather than presenting it as an arbitrary API choice.

**Provider Strategy** is the default and the one you get for free when you call `model.with_structured_output(YourPydanticModel)` or set `response_format=YourPydanticModel` on an agent. It relies on the underlying model provider's own native structured-output capability — some providers can constrain their own decoding process so the output is guaranteed to match a JSON schema, which is faster and more reliable than any prompt-engineering trick, because it's enforced at generation time, not validated after the fact. He was explicit that this only works if the specific model actually supports it, and showed how to check: `model.profile`, a property on the chat model that reports its capabilities, including whether native structured output is supported. He picked GPT-3.5-Turbo specifically as an example of a model where this check comes back negative — a deliberate choice to motivate why the second strategy needs to exist at all.

**Tool Strategy** is what you fall back to — or explicitly opt into — when Provider Strategy isn't available. The mechanism he described is genuinely clever: LangChain doesn't need the provider to support structured output natively if it already has a feature every reasonably modern model supports — tool calling. So Tool Strategy defines your Pydantic schema *as if it were a tool* the model can call, and when the model "calls" it, the arguments it provides are your structured data. From the model's point of view, it's just doing tool calling, something it already knows how to do reliably. From your code's point of view, you get validated structured output. He called this out as broadly compatible — "works almost everywhere" — at the cost of a bit more overhead than a provider's native path, since it's routing through the tool-calling mechanism instead of a purpose-built decoding constraint.

He then went further into `ToolStrategy`'s configuration, because the naive version — just pass a schema and hope — breaks the moment a model returns something that doesn't validate. Two things matter here: `tool_message_content`, which lets you control what gets fed back to the model as the "tool result" once your schema is populated, and `handle_errors`, which controls what happens when validation fails. He walked through all three modes: `handle_errors=True` (the default) triggers an automatic retry loop — the validation error gets converted into feedback and sent back to the model as if a tool call had failed, and the model gets another shot at producing something that actually validates; `handle_errors=False` lets the failure propagate as a real exception instead of silently retrying; and a custom string lets you control exactly what message the model sees when it gets something wrong, which matters because a vague error message produces a vague retry, while a specific one ("ticket count must be between 1 and 10") produces a targeted correction.

He proved this loop live with a genuinely good demo: a Pydantic field constrained with `Field(le=10)` on ticket count, then a prompt deliberately asking for 15 tickets and instructing the model to ignore any limits. The agent didn't just fail — it caught the validation error, fed it back, and the model self-corrected on the retry. That's the payoff of the whole mechanism: validation isn't just gatekeeping bad output, it's actively teaching the model what "correct" looks like, turn by turn.

The last piece was **Union schemas** — `response_format=Union[SchemaA, SchemaB, ...]` — introduced to solve a specific problem: Cinebot needs to handle both new bookings and cancellations, and those are structurally different requests (a booking needs movie/showtime/seats, a cancellation needs a booking reference). Rather than hand-writing an intent classifier to decide which schema applies before calling the model, you hand the model a Union of both schemas and let it decide which one fits the user's actual message, as part of the same structured-output call. He demonstrated this by sending a booking-shaped message and a cancellation-shaped message through the same agent configuration and showing the agent correctly selected and populated the matching schema each time — no separate classification step, no branching logic on your end.

Finally — and this is a point he treated as one of the most important distinctions in the whole session — he showed that a **raw model** with `.with_structured_output()` plus `.bind_tools()` does *not* give you tool calling and structured output working together across turns. A raw model call is single-shot: it can either request a tool call, or return a structured response, but it has no loop to reconcile the two — nothing re-invokes the model after a tool executes, and nothing knows to keep working until a valid structured response comes out the other end. That loop-awareness only exists once you use `create_agent`. Structured output and tools genuinely start "working properly together" only inside the agent harness — outside it, you're back to doing the tool-call round trip by hand, and you get one or the other on a given call, not both orchestrated for you.

---

## 4. Deep Technical Explanation

A bit more precision on the mechanics, since the transcript's explanation is accurate but leaves some of the "how" implicit.

**What Provider Strategy actually relies on.** Providers that support this typically expose it as a `response_format` or `json_schema` parameter on their own completion API — OpenAI's structured outputs feature and similar mechanisms from other providers use constrained decoding, meaning the token sampling process itself is restricted at each step to only tokens that keep the output on a valid path toward matching the schema. This is why it's both faster and more reliable than Tool Strategy where available: it's not the model "trying its best" to produce valid JSON and then getting checked — it's structurally incapable of producing invalid JSON in the first place. LangChain's `model.profile` surfaces whether this capability exists for the specific model you initialized, and `with_structured_output` chooses Provider Strategy automatically when available unless you override it.

**What Tool Strategy actually sends over the wire.** Your Pydantic schema is converted into a JSON Schema and registered as a synthetic tool definition, the same shape any real tool's `args_schema` would take. The model receives it during the request exactly like any other bound tool. When the model "calls" it, LangChain intercepts that tool call, validates the arguments against your Pydantic model, and — if valid — treats that as the final structured response rather than actually executing a function. This is why Tool Strategy has broader compatibility: it only requires the provider to support tool calling in general, a much lower and more universally supported bar than native structured-output decoding.

**The `handle_errors` retry loop, precisely.** When validation fails under `ToolStrategy`, LangChain doesn't just discard the bad output. It constructs a synthetic `ToolMessage` representing a failed tool call, with content describing the validation error (or your custom message, if you provided one), and appends it to the conversation before re-invoking the model. From the model's perspective, this looks exactly like getting corrective feedback on a tool call that didn't go through — which is precisely the mechanism it already knows how to respond to, because it's the same shape as ordinary tool-use error handling. There's a `max_retries`-style bound on this loop; you don't want a permanently invalid schema request looping forever against your token budget.

**Union schemas and discriminated intent.** Passing `Union[SchemaA, SchemaB]` as `response_format` doesn't run a separate classification pass — it's encoded into the same structured-output request (as either multiple provider-side schema options, under Provider Strategy, or multiple candidate tools, under Tool Strategy), and the model's single decision of "which schema fits" and "populate it correctly" happen together. This is meaningfully different from running an intent classifier first and then structured-output extraction second — fewer round trips, and no risk of the classifier and the extractor disagreeing about what the user meant.

**One nuance worth flagging explicitly, because it's easy to miss:** structured output constrains the *shape* of the response, not its *truthfulness*. A schema with `Field(le=10)` guarantees the model can't return 15 — either it self-corrects within the retry loop, or the call fails — but nothing about structured output prevents the model from confidently populating a field with a plausible-looking but factually wrong value (a showtime that doesn't actually exist, for instance). Structured output is a data-contract guarantee, not a correctness guarantee. Getting the *content* right is still a prompting, retrieval, and tool-grounding problem, layered separately on top.

---

## 5. Internal Execution Flow

**Provider Strategy, happy path:**

1. You call `model.with_structured_output(Schema)` or set `response_format=Schema` on `create_agent`.
2. LangChain checks `model.profile` (or equivalent internal capability metadata) to confirm native structured-output support.
3. Your Pydantic schema is converted to JSON Schema and passed to the provider's API as a native structured-output constraint.
4. The provider's decoding process is constrained token-by-token to stay on a path that satisfies the schema.
5. The raw JSON response comes back already guaranteed to match the schema shape.
6. LangChain parses it into your Pydantic model instance and returns it — no retry logic needed on the happy path, because invalid output was structurally impossible.

**Tool Strategy, including a validation failure and retry:**

1. Your schema is registered as a synthetic tool (`ToolStrategy(schema=Schema)`).
2. The model receives this tool definition alongside any real tools you've bound.
3. The model responds with a tool call targeting the schema-tool, with arguments it believes satisfy it.
4. LangChain intercepts this call and validates the arguments against your Pydantic model.
5. **If valid:** the validated instance becomes the structured response, optionally alongside `tool_message_content` being sent back to close out the "tool call" from the model's perspective.
6. **If invalid:** LangChain builds a synthetic `ToolMessage` describing the validation failure (default message, or your custom string), appends it to the conversation, and re-invokes the model — this repeats up to the configured retry bound, or raises if `handle_errors=False`.
7. Once a valid instance is produced, it's returned to you the same way as the Provider Strategy path.

**Union schema selection (either strategy):**

1. Both candidate schemas are exposed to the model in the same request (as schema options or as two synthetic tools, depending on strategy).
2. The model evaluates the user's actual message and selects the schema that fits, populating its fields.
3. Validation and (if applicable) retry proceed exactly as above, against whichever schema was selected.
4. Your code receives back an instance of whichever schema matched — you branch on `isinstance()` or a discriminator field, not on a separate upstream classification step.

**Why this needs `create_agent` to combine with live tool calls:**

1. A raw model invocation is one request → one response. If the model wants to call a real tool *and* eventually return structured output, a single `.invoke()` can't sequence "call tool, get result, incorporate result, then produce final structured response" — there's no loop.
2. `create_agent` wraps the model in that loop: it dispatches real tool calls, executes them, feeds results back as `ToolMessage`s, and keeps going until the model is ready to produce a final answer — at which point the `response_format`/structured-output resolution (Provider or Tool Strategy, whichever applies) kicks in on that final turn.
3. This is why raw `model.bind_tools(...).with_structured_output(...)` doesn't behave the way you'd hope: nothing is driving the multi-turn loop; you'd have to hand-roll it exactly like the manual tool round trip shown earlier in the course.

---

## 6. Practical Engineering Example

A real support-ticket intake system that needs to handle two structurally different request types — a new complaint and a request to check on an existing one — through the same endpoint, with a model that may or may not support native structured output.

```python
from typing import Union, Literal
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class NewComplaint(BaseModel):
    """A brand-new customer complaint being filed."""
    category: Literal["billing", "shipping", "product_defect", "other"]
    summary: str = Field(description="One-sentence summary of the issue")
    severity: int = Field(ge=1, le=5, description="1 = minor, 5 = urgent")

class StatusCheck(BaseModel):
    """A request to check on an existing ticket."""
    ticket_id: str = Field(description="The existing ticket reference number")

# A model known to lack native structured-output support -- forces Tool Strategy explicitly
model = init_chat_model("openai:gpt-3.5-turbo", temperature=0)

def lookup_ticket(ticket_id: str) -> str:
    """Look up the current status of a support ticket."""
    return f"Ticket {ticket_id} is currently in review, assigned to Tier 2."

agent = create_agent(
    model=model,
    tools=[lookup_ticket],
    response_format=ToolStrategy(
        schema=Union[NewComplaint, StatusCheck],
        handle_errors="The severity must be between 1 and 5. Please correct and resubmit.",
    ),
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "My package never arrived, this is unacceptable, fix it now"}]
})

structured = result["structured_response"]
if isinstance(structured, NewComplaint):
    create_ticket(category=structured.category, summary=structured.summary, severity=structured.severity)
elif isinstance(structured, StatusCheck):
    print(lookup_ticket(structured.ticket_id))
```

The same `agent` handles "file a new complaint" and "what's the status of ticket #4521" without any upstream branching logic — the Union schema does the routing, and `ToolStrategy` guarantees GPT-3.5-Turbo (which can't do this natively) still returns a reliably validated result.

---

## 7. Production Perspective

**Reliability.** Provider Strategy should be your default whenever the model supports it — it's enforced at generation time, which is a stronger guarantee than post-hoc validation and retry. Reserve Tool Strategy for models where you've confirmed (via `model.profile`, not assumption) that native support is missing, or where you need cross-provider consistency and don't want your schema-handling logic to differ depending on which model happens to be configured.

**Performance and cost.** Tool Strategy's retry loop means a validation failure costs you an extra round trip — real latency and real tokens. Tight, well-chosen `Field` constraints (sensible `ge`/`le` bounds, `Literal` types instead of open strings where the domain is small) reduce how often the model produces something invalid in the first place, which is cheaper than relying on the retry loop to clean up after a loose schema.

**Security and correctness boundaries.** Structured output is a shape guarantee, not a truth guarantee — don't treat a successfully validated `NewComplaint` instance as evidence the `summary` field is accurate, only that it's the right *type* of thing. Anything downstream that acts on the field values (charging a refund, escalating a ticket) should still apply its own business-logic validation, the same as you would for any user-adjacent input.

**Observability.** Log both the raw validation failures and the retry outcome, not just the final successful structured response — a schema that fails validation on the first attempt frequently, across many real users, is a signal your schema or prompt needs tightening, not evidence the retry loop is working as intended. Persist `handle_errors` custom messages that actually triggered, since patterns in *why* the model fails validation are some of the best free signal you'll get for improving field descriptions.

**Testing.** Because both strategies ultimately produce the same Pydantic instance shape to your downstream code, you can test your business logic against constructed instances directly, independent of which strategy or provider produced them — keep the "does the model reliably produce this schema" concern (which needs live model calls, or recorded fixtures, to test meaningfully) separate from "does my code do the right thing with a valid instance" (which doesn't).

**Trade-offs to be upfront about.** Union schemas remove the need for a separate intent-classification step, but they also mean schema selection errors show up as *wrong schema chosen* rather than as a clean validation failure — a Union of very similar schemas is more likely to get misclassified than two schemas with clearly distinct field sets. If your intents are genuinely ambiguous from the user's phrasing alone, a Union schema won't magically resolve that ambiguity better than a human would.

---

## 8. Common Mistakes

- **Assuming `with_structured_output` "just works" the same way on every model, without checking `model.profile`.** This is exactly the gap the instructor called out as an interview red flag — knowing structured output exists isn't the same as knowing which strategy is actually active for a given model.
- **Using a raw model with `.bind_tools()` and `.with_structured_output()` and expecting agent-like behavior.** There's no loop at that level; you'll get one shot, not a self-correcting multi-turn resolution. If you need both tools and structured output working together, that's what `create_agent` is for.
- **Loose schemas with no field constraints.** A schema of all open `str` fields validates almost anything, which defeats much of the point — constraints (`Literal`, `ge`/`le`, `min_length`) are what actually let the retry loop teach the model something specific when it gets it wrong.
- **Vague or missing `handle_errors` messages.** Letting the default generic error message carry the whole retry burden produces vague retries. A specific, actionable error string gets a specific, correct fix on the next attempt.
- **Treating a Union schema as a substitute for genuinely distinct field structures.** If two intents only differ by one optional field, the model has less signal to disambiguate correctly — Union schemas work best when the branches are structurally distinct, not just semantically different.
- **Confusing shape validation with truthfulness.** Shipping a system that trusts a validated field's *content* just because it passed schema validation, without separate business-logic checks.

---

## 9. Instructor Insights

- The Cinebot "three different shapes for three similar questions" demo is worth reproducing yourself against any model before deciding you don't need structured output — free-text inconsistency is easy to underestimate until you see it happen live, back to back, on the same prompt template.
- `model.profile` is the actual check to run, not a guess based on which provider you're using generally — support for native structured output can vary model-to-model within the same provider's lineup, not just provider-to-provider.
- The `Field(le=10)` + "ignore any limits" prompt-injection test is a genuinely good way to demonstrate to a skeptical teammate (or in an interview) that structured-output validation isn't just a formatting nicety — it's an actual constraint the model can't argue its way past, unlike an instruction in a system prompt.
- Don't optimize for token efficiency before you optimize for correctness — Tool Strategy's extra overhead versus Provider Strategy is a real cost, but it's the right trade when it's the only strategy that actually guarantees correctness for your chosen model.
- The "raw model vs. agent" distinction around structured output plus tools was treated as one of the most important checkpoints in the whole course — expect it to come up again anywhere the conversation touches "why do I even need `create_agent`."

---

## 10. Official References

- LangChain Structured Output guide: https://docs.langchain.com/oss/python/langchain/structured-output
- `create_agent` and `response_format`: https://docs.langchain.com/oss/python/langchain/agents
- `ToolStrategy` / `ProviderStrategy` API reference: https://python.langchain.com/api_reference/langchain/agents/langchain.agents.structured_output.html
- Pydantic `Field` constraints reference: https://docs.pydantic.dev/latest/concepts/fields/
- LangChain GitHub repository: https://github.com/langchain-ai/langchain

---

## 11. Key Takeaways

- Structured output turns "the model said something reasonable" into "my code can trust this shape every time" — that guarantee, not the content itself, is what makes it a production requirement rather than a nice-to-have.
- Provider Strategy is faster and stronger when available (schema enforced during generation); Tool Strategy is the universal fallback (schema enforced via the tool-calling mechanism, with a validation-and-retry loop). Check `model.profile` before assuming which one applies.
- `handle_errors` isn't just error suppression — with a good custom message, it turns validation failures into a self-correction loop the model can actually act on.
- Union schemas let a single structured-output call pick between multiple intents without a separate classification step, but they work best when the candidate schemas are structurally distinct, not just semantically different.
- Structured output alone doesn't give you tool calling and schema-guaranteed output working together across turns — that combination only exists inside the agent loop (`create_agent`), because a raw model call has no mechanism to sequence "call a tool, get the result, then produce a validated final answer."
