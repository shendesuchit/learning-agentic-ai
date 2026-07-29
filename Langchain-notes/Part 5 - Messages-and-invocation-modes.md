# Messages & Invocation Modes

*Module: learning-agentic-ai · Level: Beginner · Language: Python · Framework: LangChain*

---

## 1. Engineering Problem

Say you're building a customer-support bot. You want it to always answer in a certain tone, never reveal internal pricing logic, and remember what the customer said two messages ago. Now try to do that by sending the model a single string:

```python
model.invoke("You are a support agent, never discuss pricing. User: what's my refund status?")
```

This works for exactly one call. The moment you need a second turn, you're back to manually concatenating strings, guessing where the "instructions" end and the "user's question" begins, and hoping the model doesn't get confused about who said what. There's no structural way to say "this part is a permanent rule, this part is what the customer typed, this part is what a tool returned." Everything is one undifferentiated blob of text.

And once your bot starts calling tools — checking an order database, looking up a refund policy — you hit a second problem: how do you get a call-and-response conversation (get history, call model, get tool request, run tool, get final answer) into and out of the model reliably, at the throughput your product actually needs? A support dashboard processing three thousand tickets a night can't afford to wait for each one sequentially, and a live chat widget can't afford to make a customer stare at a blank screen for four seconds waiting for the full response to materialize.

Messages solve the first problem. Invocation modes (`invoke`, `stream`, `batch`) solve the second.

---

## 2. Why This Concept Exists

Before messages, the "prompt" was just a string. Every provider had its own convention for stuffing conversation history and instructions into that string, and if you wanted to switch from OpenAI to Anthropic, you rewrote your prompt-formatting logic. There was no standard way to say "this text came from the system," "this came from the user," or "this came from a tool," so a model reading raw concatenated text had no structural signal for what to trust and what to just answer.

LangChain's message types exist to give conversations *structure*. A `SystemMessage` is not just text with instructions in it — it's a distinct object that every provider's adapter knows to treat as non-negotiable configuration rather than something the user can talk the model out of. A `HumanMessage` is distinct from an `AIMessage` is distinct from a `ToolMessage`, and that separation is what lets a multi-turn, multi-tool conversation actually be reconstructed and replayed correctly, regardless of which underlying provider is answering it.

Invocation modes exist because "get a response from a model" is not one problem, it's three different problems depending on your product surface:

- A backend job that needs one answer and doesn't care about latency → `.invoke()`.
- A chat UI where the user is staring at the screen and every second of dead air feels broken → `.stream()`.
- A batch pipeline processing thousands of independent prompts where total wall-clock time and cost matter more than any single response → `.batch()` / `.batch_as_completed()`.

Trying to force all three onto a single API would mean either every simple call pays the overhead of streaming infrastructure, or every batch job pays for N round trips it doesn't need to pay for. LangChain keeps them as separate, purpose-built methods on the exact same model object.

---

## 3. How the Instructor Taught It

The instructor's framing was blunt and worth repeating: **a raw prompt string is a note slid under a door — there's no way to tell instructions from questions.** A message list stamps every piece of the conversation with who "said" it, so the model (and your code) never has to guess.

He walked through the four message types in this order, each one motivated by a specific failure of the one before it:

**`SystemMessage`** — the one message type you, the developer, fully control and the end user never gets to touch directly. He demonstrated this live: set a system message telling the model to answer only in Java, refuse anything else, and be blunt about it — then tried, as the "user," to talk the model out of that behavior mid-conversation. It held. His point: the system message is your only real lever for locking down behavior, because a user's `HumanMessage` can never override it (it can only *ask* — the model decides whether to comply). He also showed the flip side: asking ChatGPT to reveal its own system prompt, and having it refuse, as proof that a well-designed system message is meant to be invisible to the end user by design, not by accident.

**`HumanMessage`** — whatever the end user actually typed (or spoke, or uploaded). He pointed out something most tutorials skip: a `HumanMessage` isn't just `content`, it can carry `name` and `id` metadata. In a single-user toy chatbot you'll never touch these, but the moment you're building a multi-user system — a Slack bot in a group channel, a support tool with multiple agents on one thread — `name` is how you label who actually said a given line, and `id` is how you correlate a message back to your own database record. He was explicit that this is the kind of detail that separates "I followed a tutorial" from "I built something that survives contact with a real multi-user product."

**`AIMessage`** — the model's response. He made a point of not stopping at `.content`, because `.content` is only the visible reply. The full object also carries `.tool_calls` (any tool requests the model wants made — covered in the tools module), `.id`, `.usage_metadata` (real input/output token counts — what you actually get billed for), and `.response_metadata` (provider-specific extras like finish reason or model version). His running example was a temperature demo: setting `temperature` near 0 versus near 1 and calling the same prompt repeatedly, showing how the probability distribution over the next token shifts — a concrete, visual way of explaining why `AIMessage.content` isn't deterministic even before you touch tools or structured output.

**`ToolMessage`** — the result of a tool call, sent *back* to the model. This is where he was most insistent on a specific point, repeated across multiple sessions as a kind of interview checkpoint: **the model never executes a tool. It only requests one.** The `AIMessage.tool_calls` field is a request; your code (or, later, `create_agent`) is what actually runs the function, and the result has to come back wrapped in a `ToolMessage` carrying the exact `tool_call_id` from the request — not just appended as a plain string — or the model has no way to associate the result with its own request. He walked through this manually, once, before ever introducing `create_agent`, specifically so the automation wouldn't feel like magic later: get the tool call off the `AIMessage`, execute the underlying Python function yourself, wrap the return value in `ToolMessage(content=result, tool_call_id=call["id"])`, append it to the message list alongside the original `AIMessage`, and re-invoke the model for a final natural-language answer.

He also flagged two details worth remembering: message objects (`SystemMessage(...)`) and OpenAI-style dicts (`{"role": "system", "content": "..."}`) are functionally identical — dicts are just what you'll see when history round-trips through a database or JSON API — and a `ToolMessage` can carry an `.artifact` field alongside `.content`, where `.content` is what the model reads and `.artifact` is extra data (a document ID, a citation link) your *application* uses that the model never sees.

On invocation modes, he kept the explanation short and practical because the mental model is genuinely simple once you see it live:

- `.invoke()` — one prompt in, one full `AIMessage` out. The default, and what most examples use.
- `.stream()` — instead of one `AIMessage`, you get a sequence of `AIMessageChunk` objects, one per token (or small group of tokens) as they're generated. He ran this live with a deliberate `time.sleep()` between prints so students could actually see the chunks arrive one at a time instead of appearing to finish instantly. The chunks aren't just partial pieces you have to manually string together — `AIMessageChunk` objects support `+`, so `chunk1 + chunk2 + chunk3 + ...` reconstructs an object equivalent to what `.invoke()` would have returned in one shot.
- `.batch()` — a restaurant-kitchen analogy: send every order to the kitchen at once, and the whole table gets served together when the *slowest* dish finishes. Good for a fixed set of independent questions that all matter equally and where you want simple, ordered output.
- `.batch_as_completed()` — same kitchen, but each dish comes out the moment it's ready, not synchronized with the others. He was explicit that batching does **not** mean the end user waits longer — it means N requests run concurrently rather than sequentially, and `.batch_as_completed()` in particular is what you want when you're going to act on each result independently as it lands, rather than needing the full set before doing anything.

---

## 4. Deep Technical Explanation

A few things are worth adding beyond what a walkthrough covers, straight from LangChain's own message and model interfaces.

**Message identity and coercion.** LangChain's chat models accept more shapes than the four explicit classes. Alongside `SystemMessage`/`HumanMessage`/`AIMessage`/`ToolMessage` objects, you can pass OpenAI-style `{"role": ..., "content": ...}` dicts, `(role, content)` tuples, or even a bare string (auto-promoted to a `HumanMessage`). All of these get normalized internally into the same message objects before being sent to the provider adapter. If a dict is missing `content` or uses a role LangChain doesn't recognize, you get a `MESSAGE_COERCION_FAILURE` — this is a real, documented error class, not a vague crash, and it's almost always caused by a typo in the `role` key or a message pulled from a database with an unexpected shape.

**`AIMessage.content` is provider-normalized, `.content_blocks` is the standardized view.** Different providers return different native shapes for rich content (text, reasoning traces, citations, images). `.content` gives you the provider's own structure. LangChain also exposes `.content_blocks`, a standardized, provider-agnostic breakdown of the same response — useful if you're building a UI that needs to render text and citations differently regardless of which model answered.

**`usage_metadata` vs `response_metadata`.** `usage_metadata` is a normalized structure (`input_tokens`, `output_tokens`, `total_tokens`) that's consistent across providers — this is what you should be reading for cost tracking or rate-limit budgeting. `response_metadata` is provider-specific and can include things like `finish_reason`, model version strings, or safety-filter flags; treat it as "extra, useful, but don't build core logic that depends on its exact shape across providers."

**Streaming is not "the same call, delivered slower."** Under the hood, `.stream()` opens a server-sent-events (or provider-equivalent) connection and yields partial deltas as the provider generates them. This matters for two practical reasons: first, if a tool call is involved, the tool-call arguments themselves can arrive as JSON fragments across multiple chunks and aren't guaranteed usable until the stream completes — don't try to parse `tool_calls` mid-stream. Second, `usage_metadata` on individual chunks is often `None` or partial; you generally only get accurate token counts once the chunks are fully summed into a complete message.

**`.batch()` concurrency is configurable, not unlimited.** LangChain's underlying Runnable interface accepts a `config` with `max_concurrency`, which caps how many requests actually run in parallel — this exists specifically because "send everything at once" is a great way to get rate-limited by your provider in production. The instructor didn't cover this parameter explicitly, but it's the first thing you'll reach for the moment a real `.batch()` call against a rate-limited API starts failing.

---

## 5. Internal Execution Flow

**`.invoke()` with a message list:**

1. Your message list (objects, dicts, or a mix) is passed to the chat model.
2. LangChain's provider adapter coerces every entry into a canonical internal message representation.
3. The adapter translates that into the specific JSON shape the provider's API expects (OpenAI's `messages` array looks different from Anthropic's, even though your code looked the same).
4. The HTTP request goes out; the provider returns a completion.
5. The adapter parses the raw response back into a single `AIMessage` — populating `.content`, `.tool_calls` (if any), `.usage_metadata`, `.response_metadata`, and assigning an `.id`.
6. That `AIMessage` is returned to you, synchronously, only once the entire response is available.

**`.stream()`:**

1. Steps 1–3 are identical.
2. Instead of a single blocking HTTP call, the adapter opens a streaming connection.
3. As the provider generates tokens, each partial delta is parsed into an `AIMessageChunk` and yielded to your `for` loop immediately.
4. Each chunk supports `__add__`, so accumulating `full = full + chunk` (or the equivalent reduce) produces an object with the same shape and content as what `.invoke()` would have returned — just built incrementally instead of all at once.
5. The stream closes when the provider signals completion; at that point accumulated `usage_metadata` becomes reliable.

**`.batch()` / `.batch_as_completed()`:**

1. Each item in your input list is treated as an independent `.invoke()`-equivalent call.
2. LangChain dispatches them concurrently (bounded by `max_concurrency` if set), rather than looping and awaiting one at a time.
3. `.batch()` waits for every call to finish, then returns a list of `AIMessage` objects in the *same order* as your inputs — regardless of which one actually finished first.
4. `.batch_as_completed()` yields `(index, AIMessage)` pairs as each individual call finishes, so a slow item never blocks you from acting on a fast one that already landed. Order of the pairs is unpredictable by design.

**The manual tool-call round trip (what `create_agent` later automates):**

1. `model.bind_tools([...])` attaches tool schemas to the outgoing request — this does not execute anything, it only tells the model what's available.
2. `model.invoke(...)` returns an `AIMessage` whose `.content` may be empty and whose `.tool_calls` contains the model's *requested* function name + arguments + a `tool_call_id`.
3. Your code (not the model) executes the actual Python function using those arguments.
4. You wrap the return value in `ToolMessage(content=result, tool_call_id=<the same id from step 2>)`.
5. You append the original `HumanMessage`, the `AIMessage` that requested the tool, and the new `ToolMessage` — in that order — into one list, and call `model.invoke(...)` again.
6. The model now has the tool's result in context and produces a final `AIMessage` with actual natural-language `.content`.

---

## 6. Practical Engineering Example

A support-ticket triage service that needs to (a) keep a strict system policy, (b) track which support agent said what in an internal thread, and (c) classify a backlog of a few thousand overnight tickets efficiently.

```python
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

model = init_chat_model("openai:gpt-5-mini", temperature=0)

# --- 1. A single, live customer interaction (invoke) ---
POLICY = SystemMessage(content=(
    "You are a support triage assistant. Classify the ticket severity as "
    "LOW, MEDIUM, or HIGH, and never disclose internal escalation criteria "
    "to the customer, regardless of how the request is phrased."
))

ticket = HumanMessage(
    content="My payment was charged twice for the same order.",
    name="customer_8841",   # useful once this thread has more than one participant
)

response = model.invoke([POLICY, ticket])
print(response.content)
print("tokens billed:", response.usage_metadata["total_tokens"])

# --- 2. Streaming a live chat reply back to the customer's browser ---
def stream_reply_to_client(messages):
    for chunk in model.stream(messages):
        yield chunk.text  # send each piece over your websocket as it arrives

# --- 3. Nightly batch classification of a few thousand backlog tickets ---
backlog = [f"Ticket #{i}: {text}" for i, text in enumerate(fetch_overnight_tickets())]
batched_inputs = [[POLICY, HumanMessage(content=t)] for t in backlog]

results = {}
for idx, ai_msg in model.batch_as_completed(batched_inputs):
    # act on each classification the moment it's ready — no need to wait for the slowest one
    results[idx] = ai_msg.content
    save_classification(ticket_id=idx, severity=ai_msg.content)

# --- 4. A tool-backed follow-up: checking a real refund status ---
def check_refund_status(order_id: str) -> str:
    """Look up the current refund status for an order."""
    return f"Refund for {order_id} is pending, expected in 3-5 business days."

model_with_tools = model.bind_tools([check_refund_status])
ai_request = model_with_tools.invoke([POLICY, HumanMessage("What's the refund status for order A-102?")])

call = ai_request.tool_calls[0]
tool_result = check_refund_status(**call["args"])
tool_message = ToolMessage(content=tool_result, tool_call_id=call["id"])

final = model.invoke([POLICY, HumanMessage("What's the refund status for order A-102?"), ai_request, tool_message])
print(final.content)
```

Every one of these four patterns is the *same underlying model object* — you're not switching frameworks or clients depending on the use case, just the method you call on it.

---

## 7. Production Perspective

**Performance and cost.** `usage_metadata` on every `AIMessage` gives you real, provider-reported token counts — use it for actual cost dashboards instead of estimating with a tokenizer library, which can drift from what you're billed. For anything processing more than a handful of independent prompts, `.batch()`/`.batch_as_completed()` beats a naive `for` loop of `.invoke()` calls, because sequential invokes pay full round-trip latency N times instead of running concurrently.

**Reliability.** Set `timeout` and `max_retries` explicitly rather than trusting provider defaults — a hung request in a batch of a few hundred tickets can otherwise stall the entire job. `max_retries` defaults to a nonzero value in LangChain's model classes, which is good, but a production system should still monitor for retry exhaustion rather than assume it silently self-heals.

**Security.** Never treat `SystemMessage` as a guarantee against prompt injection — it dramatically raises the bar (the pirate-speak and Java-only demos hold up well against ordinary conversational attempts to override it) but a sufficiently adversarial user input can still sometimes get partial compliance out of a model. Treat the system message as your primary control, not your only one — validate and constrain what the model is *allowed to do* (via tool scoping, structured output schemas) rather than relying purely on instructions holding.

**Observability and debugging.** Log the full message list you send, not just the final `.content` you get back — when a bug report comes in weeks later, "what exactly was in the system prompt and history at that moment" is usually the first thing you need and the first thing teams forget to capture. `response.id` and `response_metadata` are worth persisting alongside your own request IDs for correlating with provider-side logs or LangSmith traces.

**Streaming in production.** Don't try to inspect or act on `tool_calls` from an in-progress stream — wait for the stream to close and the chunks to be fully summed. If your product needs both a live-typing feel *and* tool use, the practical pattern is: stream the natural-language portions, but let tool-call detection happen on the completed message.

**Testing.** Because message objects and dicts are equivalent, tests that assert on conversation shape can use plain dicts for readability without losing fidelity to what actually gets sent. Mock at the model-invocation boundary (the `.invoke`/`.stream`/`.batch` calls) rather than mocking HTTP directly — it keeps tests stable across provider or endpoint changes.

---

## 8. Common Mistakes

- **Cramming instructions into the user's message instead of a `SystemMessage`.** This works until the user's own text starts contradicting or diluting the instruction — separating them isn't a style preference, it changes how strongly the model respects the instruction.
- **Sending a raw string or dict back to the model after running a tool, instead of a `ToolMessage`.** The model has no contract for interpreting an arbitrary string as "the result of the tool I just asked for" — it needs the `tool_call_id` match to correctly associate cause and effect. Skipping this is a common source of models hallucinating or ignoring tool results entirely.
- **Assuming `.content` is the whole story.** New engineers print `.content` and stop there, missing `.tool_calls`, `.usage_metadata`, and `.response_metadata` — then reinvent token counting or tool-call detection badly instead of using what's already on the object.
- **Trying to parse tool-call arguments mid-stream.** Streamed tool-call JSON can arrive in fragments; code that tries to `json.loads()` a partial chunk will intermittently fail in a way that's hard to reproduce.
- **Firing off `.batch()` with hundreds of items and no `max_concurrency` cap against a rate-limited provider.** This looks fine in testing with 5 items and then falls over in production against a real backlog.
- **Confusing `.batch()` and `.batch_as_completed()`.** Using `.batch()` when you actually want to act on each result as it lands means your fastest response is stuck waiting behind your slowest one for no reason.

---

## 9. Instructor Insights

- "The model never calls a tool — it only tells you which tool it wants called." This single sentence was repeated across every session touching tools and is the fastest way to catch a shaky understanding in an interview or a code review.
- The system message is the *only* thing you fully control in a conversation — everything else (what the user says, what a tool returns) is input you have to defensively handle, not instruction you can rely on.
- Few-shot behavior correction belongs in message history, not in an ever-growing system prompt. When a co-pilot-style assistant kept answering in the wrong tone, the fix wasn't a longer system message — it was injecting a couple of example turns (a fake prior `HumanMessage`/`AIMessage` pair demonstrating the desired tone) ahead of the real conversation. Models pick up on demonstrated behavior faster and more reliably than on described behavior.
- Batching doesn't mean the customer waits longer — it means you're running requests concurrently instead of one after another. This gets misunderstood constantly by engineers new to the concept, who assume "batch" implies "queued and delayed."
- Don't build logic that depends on exact `response_metadata` fields being stable across providers — treat it as a debugging aid, not a contract.

---

## 10. Official References

- LangChain Messages concept guide: https://docs.langchain.com/oss/python/langchain/messages
- LangChain Chat Models — invoke/stream/batch interface: https://docs.langchain.com/oss/python/langchain/models
- `Runnable` interface (underlying `batch`, `batch_as_completed`, `max_concurrency`): https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html
- `AIMessage` API reference: https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html
- `ToolMessage` API reference: https://python.langchain.com/api_reference/core/messages/langchain_core.messages.tool.ToolMessage.html
- LangChain GitHub repository: https://github.com/langchain-ai/langchain

---

## 11. Key Takeaways

- A message list, not a raw string, is how you give a conversation structure — `SystemMessage` for rules you control, `HumanMessage` for what the user said, `AIMessage` for what the model said, `ToolMessage` for what a tool returned.
- The model requests tool calls; it never executes them. Completing that loop by hand once — execute, wrap in `ToolMessage` with the matching `tool_call_id`, re-invoke — is what makes `create_agent`'s automation later feel like a shortcut instead of magic.
- `AIMessage` carries far more than `.content`: `.tool_calls`, `.usage_metadata`, `.response_metadata`, and `.id` are all real signal you should be using, not ignoring.
- Pick your invocation mode based on your product surface, not habit: `.invoke()` for a single backend answer, `.stream()` for anything a human is watching in real time, `.batch()`/`.batch_as_completed()` for independent bulk work where concurrency actually saves wall-clock time and money.
- `AIMessageChunk` objects are additive by design — summing them reconstructs the exact same object `.invoke()` would have given you, which is why streaming and non-streaming code paths can share almost all of their downstream logic.
