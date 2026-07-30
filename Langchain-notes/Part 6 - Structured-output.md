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

================================================================================================================================

# Structured Output: Provider Strategy → Tool Strategy → Union Schemas

*Module: learning-agentic-ai · Level: Beginner · Language: Python · Framework: LangChain*

---

## 1. The Problem, in Plain Words

Okay, let's understand this with a proper desi example — a movie-booking bot. Let's call it Cinebot.

- Customer number one types: *"I want to watch Inception tonight, 2 tickets."* Cinebot replies nicely, confirms the booking in a proper sentence. Sounds fine, no?
- Customer number two asks almost the exact same thing. But this time the reply comes back with the seat numbers written differently, no showtime mentioned anywhere, and the ticket count hidden somewhere in the middle of a sentence — you'd need to write some clever string-matching just to pull that number out.
- Customer number three gets a reply where the movie name mentioned isn't even exactly what they typed.

Now here's the thing — if a human reads all three replies, nobody's confused. Each one makes sense on its own. But *you*, as the engineer sitting behind this bot, have a real problem. Your backend needs something like:

```
{"movie": "Inception", "showtime": "9:00 PM", "seats": 2}
```

...every single time, in exactly this shape, so it can go and actually book the tickets. A nice, friendly sentence doesn't help your code one bit. You can't build a booking system, an order pipeline, or any form-filling flow on top of "the model said something that sounded reasonable." You need a guarantee about the *shape* of the answer, not just whether the content made sense.

That, in one line, is what structured output solves: it forces the model's reply into a fixed shape your code can trust, every single time — not just when the model happens to be in a good mood.

---

## 2. Why Do We Even Need This as a Separate Thing?

Let's go back a bit in time, because this helps the "why" stick better than just memorizing rules.

- Before structured output became a proper built-in feature, engineers used to handle this the jugaad way — they'd write in the prompt, "please respond only in valid JSON matching this format," and then wrap the whole thing in a `try/except` and just hope for the best.
- This worked *often enough* to ship something. But it also failed often enough to become a genuine headache in production: sometimes the JSON was broken, sometimes the model added extra chit-chat before or after the JSON block, sometimes field names got slightly renamed, sometimes numbers came back as text instead of actual numbers. Basically, every failure mode you'd expect when you ask a text-generating model to *also* behave like a strict data form — and the only thing enforcing that form was a polite request. No teeth behind it.

Structured output exists to fix exactly this — by making "follow the schema" the *provider's* job (when the AI company's own model can do it natively) or *LangChain's* job (when it can't), instead of leaving it entirely on your prompt's shoulders.

- You define your schema once — usually using something called a Pydantic model, which is just Python's standard way of saying "here's exactly what fields I expect, and what type each one should be."
- Once you've defined that, the framework guarantees the response either matches it, or it fails *loudly* — not silently sneaking a wrong answer into your system.

Now, why isn't there just *one* simple way of doing this? Because different AI model providers support this differently.

- Some companies have built native support right into their API — a proper "constrained decoding" or "JSON schema" feature.
- Others haven't, or only support it partially.
- So LangChain needed a way to give you the *same guarantee* no matter which model you're using underneath. That's exactly why there are two strategies here — **Provider Strategy** and **Tool Strategy** — not because someone wanted to make the API complicated for fun.

---

## 3. Breaking This Down the Way a Good Teacher Would

The best way to introduce this topic is by deliberately *breaking* Cinebot in front of the class, so the problem feels real instead of theoretical.

- Ask it the same kind of booking question in three slightly different ways, in plain free text.
- Show, live, that all three replies come back in three *different* shapes — no fixed set of fields, no consistent formatting, nothing your backend could reliably parse without writing separate, fragile logic for every possible phrasing the model decides to use that day.

The one-line lesson worth underlining here:

> **The model can be completely right in what it says, and still be useless to your code — if the shape isn't guaranteed.**

From here, there are really two strategies, and it helps to understand *why* both exist, rather than just memorizing them as two random API options.

### Provider Strategy — let the AI company itself do the heavy lifting

- This is your default option, and you get it more or less for free the moment you write `model.with_structured_output(YourPydanticModel)` — or set `response_format=YourPydanticModel` on an agent.
- What's actually happening: some AI providers can restrict their own model, at the moment it's generating text, so that it's *physically incapable* of producing anything except valid output matching your schema. This is faster and far more reliable than any prompt trick, because it's enforced *while the answer is being written*, not checked afterward.
- Important catch: this only works if the *specific* model you're using actually supports it. Not every model does, even from the same company.
- How do you check? There's a simple property called `model.profile` you can look at — think of it like checking the spec sheet of a phone before buying it, to see which features it actually has. It tells you plainly whether native structured output is supported for that model.
- A good example to remember: GPT-3.5-Turbo is a model where this check comes back "no." That's exactly why the second strategy needs to exist at all — not every model can do this trick.

### Tool Strategy — the backup plan that works almost everywhere

- This is what you fall back to (or deliberately choose) when Provider Strategy isn't available.
- The idea here is genuinely clever, and worth appreciating: LangChain doesn't actually *need* the provider to support structured output natively — because almost every reasonably modern model already knows how to do something called "tool calling" (basically, asking the model to use a function when needed).
- So Tool Strategy takes your Pydantic schema and pretends it's a tool the model can "call." When the model calls this pretend tool, whatever arguments it fills in *become* your structured data.
- From the model's side, it just thinks it's doing normal tool calling — something it already knows how to do well. From your code's side, you get clean, validated structured data.
- The trade-off: it works almost everywhere, but it costs a little more overhead than the native provider path, since it's going through the tool-calling route instead of a purpose-built shortcut.

### Making Tool Strategy actually reliable — the retry mechanism

The naive version of this — just hand over a schema and hope for the best — breaks the moment the model returns something that doesn't fit. So there are two settings worth knowing properly:

- **`tool_message_content`** — lets you control exactly what message gets sent back to the model once your schema has been filled correctly, confirming the "tool call" is done.
- **`handle_errors`** — controls what happens the moment validation *fails*. There are three modes here, and each behaves differently:
  - `handle_errors=True` (this is the default) — triggers an automatic retry. The validation error gets turned into a message and sent back to the model, almost like telling it, "beta, that tool call didn't work, try again" — and the model gets another honest shot at getting it right.
  - `handle_errors=False` — lets the failure become a real error/exception in your code, instead of quietly retrying behind the scenes.
  - A custom string — this is where you write your own message, telling the model *exactly* what went wrong. And this matters a lot — a vague error message gets you a vague, half-hearted retry, while a specific one (like *"ticket count must be between 1 and 10"*) actually gets you a targeted, correct fix.

Here's a lovely demo to try yourself, and honestly one of the best "aha" moments in this whole topic:

- Add a constraint on the ticket-count field — something like `Field(le=10)`, meaning "not more than 10."
- Now deliberately write a prompt asking for 15 tickets, and even tell the model to *ignore any limits*.
- What happens? The agent doesn't just crash or misbehave. It catches the validation failure, sends that feedback back to the model, and the model corrects itself on the retry — coming back with a proper, valid number.
- This is the real payoff of the whole mechanism: validation isn't just a strict gatekeeper standing at the door saying "no entry." It's actually *teaching* the model, turn by turn, what "correct" looks like.

### Union Schemas — letting the model pick between multiple options

Cinebot needs to handle two very different kinds of requests: a new booking, and a cancellation. These aren't the same shape at all —

- A booking needs movie, showtime, and number of seats.
- A cancellation just needs a booking reference number.

Instead of writing a separate "intent classifier" — some extra piece of logic that first decides *what kind of request this even is*, before you even call the model — you can simply hand the model a **Union**, i.e., both schemas together, and let it decide which one fits the customer's actual message, as part of the very same call.

- Send it a booking-style message, and it correctly picks and fills the booking schema.
- Send it a cancellation-style message, and it correctly picks and fills the cancellation schema instead.
- No separate classification step. No extra branching logic sitting on your end.

### One more important point — and this one's genuinely worth remembering

Here's something people often assume works, but doesn't: if you take a plain model and just add `.with_structured_output()` *and* `.bind_tools()` on top, you do **not** automatically get tool-calling and structured output working together, smoothly, across multiple turns.

- A raw model call is a one-shot thing. It can either ask to use a tool, *or* it can return a structured answer — but there's no built-in loop connecting the two. Nothing brings the model back after a tool finishes running. Nothing keeps trying until a genuinely valid structured answer finally comes out.
- That kind of "keep going until it's actually correct" loop only exists once you wrap things inside `create_agent`.
- So structured output and tool calling only really start working together properly *inside* the agent setup. Outside of it, you're back to doing the round trip by hand — and on any single call, you get one or the other, not both, working together automatically.

---

## 4. A Slightly Deeper Look Under the Hood

Here are a few extra details worth knowing, since they explain the "how," not just the "what."

- **What Provider Strategy is really doing.** Providers that support this usually expose a `response_format` or `json_schema` setting on their own API. Under the hood, they use something called constrained decoding — meaning, at every single step of generating the answer, the model is only allowed to pick from tokens (small chunks of text) that keep it on a valid path toward matching your schema. This is why it's both faster *and* more trustworthy than Tool Strategy where it's available — the model isn't "trying its best" and getting checked afterward, it's simply not *able* to produce anything invalid in the first place.
- **What Tool Strategy is actually sending across.** Your Pydantic schema gets converted into something called a JSON Schema and registered as a fake, synthetic "tool." The model receives it exactly like it would receive any real tool. When the model "calls" this fake tool, LangChain quietly intercepts that call, checks the arguments against your schema, and — if everything checks out — treats that as your final structured answer, instead of actually running any real function. This is why Tool Strategy works almost everywhere — it only needs the provider to support ordinary tool calling in general, which is a much more common and basic feature than native structured-output support.
- **The retry loop, in a bit more detail.** When validation fails, LangChain doesn't just throw the bad answer away quietly. It builds a fake "tool result" message describing exactly what went wrong (either the default message or your own custom one), adds it into the conversation, and asks the model again. From the model's point of view, this looks exactly like ordinary feedback on a failed tool call — something it already knows how to respond to sensibly. And don't worry, this retry loop isn't infinite — there's a cap on how many times it'll try, so you don't end up burning your token budget forever on a genuinely broken schema.
- **How Union schemas actually decide which one to use.** Passing `Union[SchemaA, SchemaB]` doesn't quietly run a separate classification step behind your back. Both options are shown to the model in the *same* request — either as multiple schema choices, or as two pretend tools, depending on which strategy you're using — and the model makes one single decision: which schema fits, and how to fill it in. This is genuinely different (and better) than running a separate classifier first and an extractor second, because there's no risk of the classifier and the extractor disagreeing with each other about what the customer actually meant.
- **A nuance that's very easy to miss, so let's say it clearly:** structured output only guarantees the *shape* of the answer — not whether it's *true*. A field with `Field(le=10)` guarantees the model literally cannot hand you back 15 — either it self-corrects, or the whole call fails. But nothing here stops the model from confidently filling a field with something that *looks* plausible but is actually wrong — say, a showtime that doesn't even exist for that movie. Structured output is a promise about the data contract, not a promise about correctness. Getting the actual *content* right is still a separate job — one for good prompting, good retrieval, and good tool-grounding, layered on top of this.

---

## 5. Step-by-Step, What Actually Happens Behind the Scenes

**Provider Strategy — the smooth, happy path:**

1. You call `model.with_structured_output(Schema)`, or set `response_format=Schema` inside `create_agent`.
2. LangChain checks `model.profile` (or similar internal info) to confirm the model genuinely supports native structured output.
3. Your Pydantic schema is converted into JSON Schema and sent to the provider as a native constraint.
4. The provider's own decoding process is restricted, token by token, to stay on a path that satisfies your schema.
5. The raw JSON response comes back already guaranteed to match your schema — no surprises.
6. LangChain parses this straight into your Pydantic model and hands it back to you. No retry needed on the happy path, because an invalid answer was never even possible to begin with.

**Tool Strategy — including what happens when validation fails:**

1. Your schema gets registered as a pretend tool: `ToolStrategy(schema=Schema)`.
2. The model receives this fake tool definition, alongside any real tools you've actually given it.
3. The model responds by "calling" this schema-tool, filling in arguments it *believes* are correct.
4. LangChain intercepts this and checks the arguments against your Pydantic model.
5. **If it's valid** — that validated data becomes your final structured response. Optionally, `tool_message_content` gets sent back to close things off neatly from the model's point of view.
6. **If it's invalid** — LangChain builds a fake error message (default, or your custom one), adds it to the conversation, and asks the model again. This repeats up to a set limit, or raises a real error if you've set `handle_errors=False`.
7. Once a valid answer finally comes through, it's handed back to you exactly the same way as the Provider Strategy path.

**Union schema selection (works the same way under either strategy):**

1. Both candidate schemas are shown to the model in the same request.
2. The model looks at the customer's actual message and picks whichever schema genuinely fits, filling in its fields.
3. Validation, and retrying if needed, happens exactly as described above — just against whichever schema got picked.
4. Your code simply gets back an instance of whichever schema matched. You check which one it is using `isinstance()` — there's no separate upstream classification step to write yourself.

**Why you need `create_agent` to combine this with live tool calls:**

1. A plain model call is one request in, one response out. If the model wants to use a real tool *and* also eventually give you a structured answer, a single `.invoke()` simply can't sequence "call the tool → get the result → factor that in → then produce the final structured answer." There's no loop to make that happen on its own.
2. `create_agent` is exactly that missing loop. It dispatches real tool calls, actually runs them, feeds the results back in, and keeps going until the model is genuinely ready to produce a final answer — and only *then* does the structured-output check (Provider or Tool Strategy, whichever applies) kick in.
3. That's precisely why a plain `model.bind_tools(...).with_structured_output(...)`, without an agent wrapped around it, won't behave the way you'd hope. Nothing is driving that multi-turn loop — you'd have to build it yourself by hand, the same manual round trip covered earlier in this course.

---

## 6. Let's See It Working — A Real Example

Picture a real support-ticket intake system. It needs to handle two genuinely different kinds of requests — a brand-new complaint, and a check on an existing one — through the *same* endpoint, using a model that may or may not support native structured output.

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

Now let's talk through *why* this is built the way it is, because just reading the code top to bottom, you might miss the reasoning:

- Notice `gpt-3.5-turbo` is chosen deliberately here — this is a model that we already know doesn't support native structured output. So Tool Strategy isn't a random pick in this example, it's the *only* strategy that would actually work reliably for this model. That's the whole reason `ToolStrategy(...)` is used explicitly, instead of just calling `.with_structured_output()` and hoping.
- Look at `handle_errors` in this example — instead of leaving it as the default generic message, a specific, human-readable sentence has been written: *"The severity must be between 1 and 5. Please correct and resubmit."* If the model ever tries to sneak in a severity of, say, 9, this exact message goes back to it, and it gets a real, useful hint about what to fix — not a vague "something went wrong."
- `Union[NewComplaint, StatusCheck]` is doing quiet, important work here. The customer's message — *"My package never arrived, this is unacceptable, fix it now"* — clearly sounds like a fresh complaint, not a status check. Nobody wrote an if-else to detect that. The model itself decides which schema fits, based on the wording, and fills in the right one.
- Right at the end, `isinstance(structured, NewComplaint)` is simply asking, "okay, which one did the model pick?" — and based on that, your code either creates a brand-new ticket, or looks up an existing one. That's the entire routing logic for two completely different flows, and it's just two lines.

---

## 7. Real-World Advice — What to Actually Do in Production

- **On reliability.** Whenever the model you're using supports Provider Strategy, use it as your default — it's enforced right at the moment of generation, which is a much stronger guarantee than checking after the fact and retrying. Save Tool Strategy for models where you've *actually confirmed*, using `model.profile` and not just a guess, that native support is missing — or where you specifically want your schema-handling logic to behave the same way no matter which model happens to be plugged in.
- **On speed and cost.** Every time Tool Strategy has to retry because of a validation failure, that's a real extra round trip — real time lost, real tokens spent, real cost added. Writing tight, sensible field constraints (proper `ge`/`le` number ranges, using `Literal` instead of an open-ended string wherever the possible values are limited) reduces how often the model gets it wrong in the first place. That's always cheaper than depending on the retry loop to clean up a lazily written schema.
- **On security and being honest about limits.** Structured output is a promise about *shape*, not about *truth*. Just because a `NewComplaint` object passed validation doesn't mean its `summary` field is actually accurate — it only means it's the right *type* of data. Anything downstream that acts on these values — issuing a refund, escalating a ticket — should still run its own proper business checks, exactly like you would for any input coming from a real user.
- **On keeping an eye on things.** Log both the validation failures *and* the eventual retry outcome — not just the final successful answer. If a schema keeps failing validation on the first try, again and again, across many different real users, that's telling you something — your schema or your prompt probably needs tightening. It's not "proof the retry loop is working as designed," it's a signal something upstream needs fixing. Also worth saving: whatever custom `handle_errors` messages actually got triggered in the wild — patterns in *why* the model keeps failing are some of the best free feedback you'll get for improving your field descriptions.
- **On testing.** Since both strategies eventually hand your downstream code the *same* kind of Pydantic object, you can test your actual business logic against manually constructed instances, without caring which strategy or which model produced them. Keep two things separate: "does the model reliably produce this schema" (this genuinely needs live model calls, or recorded examples, to test properly) versus "does my code behave correctly given a valid instance" (this doesn't need any of that — it's just normal Python testing).
- **On being upfront about trade-offs.** Union schemas save you from writing a separate intent-classification step — but they also mean that if the model picks the *wrong* schema, it won't look like a clean validation failure, it'll look like a wrong (but perfectly valid) answer. A Union of two very similar-looking schemas is more likely to get mixed up than two schemas with clearly different fields. And if your customers' messages are genuinely ambiguous — even a human reading them wouldn't be 100% sure what's meant — a Union schema isn't magic. It won't resolve that ambiguity any better than a person would.

---

## 8. Mistakes People Keep Making — Please Avoid These

- **Assuming `with_structured_output` behaves the same on every model, without ever checking `model.profile`.** This is genuinely one of those "gotcha" gaps that shows a shaky understanding — just knowing that structured output *exists* isn't the same as knowing which strategy is actually running for the model you're using right now.
- **Using a plain model with `.bind_tools()` and `.with_structured_output()`, and expecting it to behave like a full agent.** There's simply no loop at that level. You'll get one attempt, not a self-correcting back-and-forth. If you genuinely need tools and structured output working together properly, that's exactly what `create_agent` is built for.
- **Writing loose schemas with no real constraints.** A schema made entirely of open `str` fields will validate almost anything you throw at it — which quietly defeats the whole purpose. Constraints like `Literal`, `ge`/`le`, and `min_length` are what actually let the retry loop teach the model something specific when it gets things wrong.
- **Leaving `handle_errors` vague, or not setting it at all.** Relying on the generic default error message puts the entire burden of fixing things on a vague retry. A clear, specific error string gets you a specific, correct fix on the very next attempt.
- **Using a Union schema when the two intents barely differ.** If two possible intents differ by just one optional field, the model has very little to go on to tell them apart correctly. Union schemas work best when the branches are genuinely, structurally different — not just differently worded versions of the same idea.
- **Mixing up "shape is correct" with "content is true."** Building a system that blindly trusts a field's *content* just because it passed schema validation, without adding your own separate business-logic checks on top.

---

## 9. Small Lines Worth Remembering

- Try the Cinebot "three different shapes for three similar questions" demo yourself, on any model, before deciding you don't really need structured output. Free-text inconsistency is very easy to underestimate — until you actually watch it happen live, back to back, using the exact same prompt.
- `model.profile` is the real thing to check — don't just assume based on "which company's model I'm generally using." Native structured-output support can genuinely differ from model to model within the *same* company's lineup, not only between different companies.
- The `Field(le=10)` plus "please ignore any limits" test is a lovely, honest way to show a skeptical colleague (or answer confidently in an interview) that structured-output validation isn't just a formatting nicety — it's a real constraint the model genuinely cannot talk its way around, unlike a plain instruction sitting in a system prompt.
- Don't chase token-efficiency before you've nailed correctness. Yes, Tool Strategy costs a bit more than Provider Strategy — but that's a completely fair trade when it's the only strategy that actually guarantees correctness for the model you're stuck using.
- The difference between "a plain model" and "a proper agent" when it comes to structured output plus tools is one of the most important things to really internalize here — it tends to come up again and again, anywhere the conversation turns to "why do I even need `create_agent` in the first place?"

---

## 10. Where to Read More, Straight from the Source

- LangChain Structured Output guide: https://docs.langchain.com/oss/python/langchain/structured-output
- `create_agent` and `response_format`: https://docs.langchain.com/oss/python/langchain/agents
- `ToolStrategy` / `ProviderStrategy` API reference: https://python.langchain.com/api_reference/langchain/agents/langchain.agents.structured_output.html
- Pydantic `Field` constraints reference: https://docs.pydantic.dev/latest/concepts/fields/
- LangChain GitHub repository: https://github.com/langchain-ai/langchain

---

## 11. If You Remember Just a Few Things, Remember These

- Structured output turns "the model said something that sounds reasonable" into "my code can trust this exact shape, every single time." That guarantee — not the content itself — is what makes it a genuine production need, not a nice-to-have extra.
- Provider Strategy is faster and stronger whenever it's available, since the schema is enforced right while the answer is being generated. Tool Strategy is your universal backup, enforced through the tool-calling route, with a built-in validate-and-retry loop. Always check `model.profile` first — don't just assume.
- `handle_errors` isn't merely about hiding errors quietly — with a good, specific custom message, it becomes a genuine self-correction loop the model can actually act on and learn from, turn by turn.
- Union schemas let one single structured-output call pick between multiple possible intents, with no separate classification step needed — but they work best when the candidate schemas are genuinely different in structure, not just worded differently.
- Structured output on its own doesn't give you tool calling and guaranteed-shape output working together smoothly across multiple turns — that combination only really exists inside the agent loop (`create_agent`), because a plain model call has no built-in way to sequence "call a tool, get the result back, then produce a properly validated final answer."


