# Messages & Invocation Modes

*Module: learning-agentic-ai · Level: Beginner · Language: Python · Framework: LangChain*

---

## 1. The Problem We're Actually Trying to Solve

Let's start with a story, because that's how I'd open this in class.

Imagine you're building a customer-support bot. Three simple requirements:

- It should always answer in a certain tone.
- It should never leak internal pricing logic to a customer.
- It should remember what the customer said two messages ago.

Sounds easy, right? Now try to build that using nothing but a single string handed to the model:

```python
model.invoke("You are a support agent, never discuss pricing. User: what's my refund status?")
```

- This works — for exactly one call. The moment you need a *second* turn, you're stuck manually gluing strings together, guessing where your instructions end and the customer's question begins, and hoping the model doesn't confuse the two.
- There's no structural way to tell the model "this part is a permanent rule," "this part is what the customer typed," or "this part is what a tool just returned." It's all one undifferentiated wall of text — like handing someone a letter with no punctuation and no paragraph breaks and asking them to figure out which sentences were orders and which were questions.
- Then a second, completely different problem shows up the moment your bot starts calling tools — checking an order database, looking up a refund policy. Now you need a reliable back-and-forth: fetch history → call the model → get a tool request → run the tool → get the final answer. And you need this to happen at whatever speed your product actually demands. A dashboard chewing through three thousand tickets overnight can't afford to process them one at a time. A live chat widget can't afford to leave a customer staring at a blank screen for four seconds.

**Messages** solve the first problem — giving structure to a conversation.
**Invocation modes** (`invoke`, `stream`, `batch`) solve the second — giving you control over speed and throughput.

Keep that split in your head as we go: *messages are about structure, invocation modes are about delivery.*

---

## 2. Why Any of This Exists in the First Place

Here's some useful history, because understanding *why* a tool exists usually makes it stick better than memorizing what it does.

- Before message objects existed, a "prompt" really was just a plain string. Every AI provider had its own private convention for stuffing conversation history and instructions into that string. Switch from OpenAI to Anthropic, and you'd end up rewriting your entire prompt-formatting logic from scratch.
- There was no standard way to say "this text is from the system," "this is from the user," or "this came from a tool." A model reading raw concatenated text had zero structural signal for what to trust versus what to simply answer.

That's precisely the gap LangChain's message types were built to close — they give a conversation *shape*.

- A `SystemMessage` isn't just "text that happens to contain instructions." It's a distinct object that every provider's adapter is built to treat as non-negotiable configuration — something the user can't simply talk the model out of.
- A `HumanMessage` is a different animal from an `AIMessage`, which is different again from a `ToolMessage`. That separation is exactly what allows a long, multi-turn, multi-tool conversation to be reliably reconstructed and replayed later — no matter which provider is actually answering it.

Now, why do we need *three* different invocation modes instead of just one flexible one? Because "get a response from a model" isn't really one problem — it's three different problems wearing the same trench coat, depending on where in your product this call happens:

- A backend job that needs one answer and doesn't care how long it takes → `.invoke()`
- A chat UI where a real person is watching the screen, and every second of silence feels broken → `.stream()`
- A batch pipeline chewing through thousands of independent prompts, where total time and cost matter far more than any single response → `.batch()` / `.batch_as_completed()`

If you tried to cram all three needs into one API, you'd end up with a bad compromise everywhere: simple calls paying for streaming infrastructure they don't need, or batch jobs paying for round trips they shouldn't have to pay for. So LangChain keeps them as three separate, purpose-built methods sitting on the exact same model object. Same tool, different gears.

---

## 3. Breaking Down the Four Message Types (the way I'd teach it on a whiteboard)

Here's the analogy worth remembering above everything else in this section:

> **A raw prompt string is a note slid under a door — there's no way to tell instructions apart from questions.** A message *list* stamps every piece of the conversation with who "said" it, so neither the model nor your own code ever has to guess.

Let's walk through the four message types in the order that makes the most pedagogical sense — each one exists to fix a specific weakness in the one before it.

### `SystemMessage` — the rule-setter only you control

- This is the *one* message type that you, the developer, fully own. The end user never gets to write it or edit it directly.
- Think of it as the constitution of the conversation — every other message operates underneath it, but it doesn't answer to them.
- A nice way to see this in action: set a system message telling the model to answer *only* in Java, refuse anything else, and be blunt about enforcing that. Then, playing the role of the "user," try to argue the model out of that rule mid-conversation. It holds. That's the whole point.
- The takeaway: a `HumanMessage` can *ask* the model to break a rule, but it can never *force* the model to — the model still decides whether to comply, and the system message is what tips that decision your way.
- Flip side worth remembering: if you ask ChatGPT to reveal its own system prompt, it typically refuses. That's not an accident — a well-designed system message is meant to be invisible to the end user *by design*, not because nobody thought to ask.

### `HumanMessage` — whatever the actual person said

- This is whatever the end user typed, spoke, or uploaded.
- Here's a detail most beginner tutorials skip entirely: a `HumanMessage` isn't just `content`. It can also carry `name` and `id` metadata.
- In a single-user toy chatbot, you'll genuinely never touch these fields — there's only one voice in the room, so labeling it feels pointless.
- But the moment you're building something with *multiple* humans in one thread — a Slack bot in a group channel, a support tool where several agents are typing into the same conversation — `name` becomes essential. It's how you label *who* actually said a given line. And `id` is how you tie a message back to your own database record, so you can trace it later.
- This is genuinely one of those details that separates "I followed a tutorial once" from "I built something that survives contact with a real, messy, multi-user product."

### `AIMessage` — the model's response, and *all* of it

- This is the model's reply — but here's the trap: most people stop at `.content` and think that's the whole object. It isn't. `.content` is only the visible reply text.
- The full `AIMessage` object also carries:
  - `.tool_calls` — any tool requests the model wants made (we'll get to this properly in the tools module)
  - `.id` — a unique identifier for this specific response
  - `.usage_metadata` — the *real* input/output token counts, i.e., exactly what you get billed for
  - `.response_metadata` — provider-specific extras, like finish reason or model version
- A great classroom demo for making this feel real: run the same prompt repeatedly, once with `temperature` near 0 and once near 1, and watch how the output changes. Low temperature keeps picking the most probable next token every time, so answers stay nearly identical run after run. High temperature lets the model wander into less probable — but still plausible — next tokens, so the same prompt produces noticeably different answers each time.
- This single demo makes something click that's easy to just "know" abstractly but not really *feel*: `AIMessage.content` isn't deterministic, even before you've touched tools or structured output. The randomness is baked into how the model samples its next word, not something that only shows up once your system gets complicated.

### `ToolMessage` — the answer that goes *back* to the model

- This one is where I'd slow down the most, because it's also where new engineers trip most often — and it's worth repeating like a mantra:

  > **The model never executes a tool. It only requests one.**

- Concretely: `AIMessage.tool_calls` is a *request*, nothing more. Your own code (or later, `create_agent`, once you've earned the automation) is what actually runs the underlying function.
- The result then has to come back to the model wrapped in a `ToolMessage` — and critically, that `ToolMessage` needs to carry the *exact* `tool_call_id` from the original request. Not just tacked on as a plain string. If you skip that ID match, the model has no way to connect "here's a result" back to "here's the request I made" — it's like getting an answer to a question you never asked.
- The reason it's worth doing this by hand *once*, before ever touching `create_agent`, is purely pedagogical: if you never see the manual version, the automated version will feel like magic. And "magic" is a bad place to be standing when something breaks in production and you need to debug it.
- The manual loop, step by step:
  1. Pull the tool call off the `AIMessage`.
  2. Execute the actual Python function yourself, using the arguments the model provided.
  3. Wrap the return value: `ToolMessage(content=result, tool_call_id=call["id"])`.
  4. Append it to your message list, right alongside the original `AIMessage`.
  5. Re-invoke the model so it can turn that raw result into a natural-language answer.

### Two small but genuinely useful footnotes

- Message objects like `SystemMessage(...)` and OpenAI-style dicts like `{"role": "system", "content": "..."}` are functionally interchangeable. You'll mostly see the dict form when conversation history has round-tripped through a database or a JSON API — don't be thrown by it.
- A `ToolMessage` can also carry an `.artifact` field alongside `.content`. The distinction matters: `.content` is what the *model* reads, while `.artifact` is extra data — say, a document ID or a citation link — that your *application* uses but the model never actually sees.

---

## 4. Invocation Modes — the Short, Practical Version

The good news here: once you see these three side by side, the mental model is genuinely simple.

- **`.invoke()`** — one prompt goes in, one full `AIMessage` comes out. This is the default, and the one you'll see in almost every basic example.
- **`.stream()`** — instead of one complete `AIMessage`, you get a *sequence* of `AIMessageChunk` objects, arriving roughly one per token (or a small handful of tokens) as they're generated.
  - A nice way to actually *see* this instead of just hearing about it: add a small `time.sleep()` between each printed chunk. Watching the words trickle in one at a time — instead of the whole answer just appearing instantly — makes the concept concrete in a way no explanation quite manages.
  - These chunks aren't just fragments you have to manually glue back together. `AIMessageChunk` objects support the `+` operator, so `chunk1 + chunk2 + chunk3 + ...` reconstructs an object equivalent to whatever `.invoke()` would have handed you in one shot. Streaming and non-streaming aren't really two different worlds — they converge back into the same object.
- **`.batch()`** — picture a restaurant kitchen. Every order goes to the kitchen at once, and the whole table gets served together, only when the *slowest* dish is finally ready. This is great when you've got a fixed set of independent questions that all matter equally, and you want simple, predictably-ordered output back.
- **`.batch_as_completed()`** — same kitchen, but each dish comes out to the table the moment *it's* ready, no waiting for the others to catch up.
  - Worth being explicit about, because it's a common point of confusion: batching does **not** mean the end user waits *longer*. It means N requests run concurrently instead of one after another. `.batch_as_completed()` specifically is what you reach for when you plan to act on each result independently as it lands, rather than needing the entire set to complete before doing anything useful.

---

## 5. A Bit Deeper Under the Hood

A few extra things worth knowing, straight from how LangChain's message and model interfaces actually behave — not just the surface-level walkthrough.

- **Message shapes get "coerced" into a common format.** You're not locked into the four explicit classes. You can pass OpenAI-style `{"role": ..., "content": ...}` dicts, `(role, content)` tuples, or even a bare string — which quietly gets promoted into a `HumanMessage` on your behalf. All of these get normalized internally into the same canonical message objects before anything is sent to the provider. If a dict is missing `content`, or uses a role LangChain doesn't recognize, you'll get a `MESSAGE_COERCION_FAILURE`. This is a real, documented error — not a mystery crash — and it's almost always caused by a typo in the `role` key, or a message pulled out of a database with an unexpected shape.
- **`.content` vs `.content_blocks`.** Different providers structure rich content (text, reasoning traces, citations, images) differently under the hood. `.content` reflects the provider's own native structure. `.content_blocks` is LangChain's standardized, provider-agnostic view of the same response — genuinely useful if you're building a UI that needs to render text and citations consistently, regardless of which model happens to be answering that day.
- **`usage_metadata` vs `response_metadata`.** `usage_metadata` is normalized and consistent across every provider (`input_tokens`, `output_tokens`, `total_tokens`) — this is what you should actually be reading for cost tracking or rate-limit budgeting. `response_metadata` is provider-specific and can include things like `finish_reason` or a model version string. Treat it as helpful color commentary, not something to build core logic around.
- **Streaming is not just "the same call, delivered slower."** Under the hood, `.stream()` opens a persistent connection (server-sent events, or the provider's equivalent) and yields partial deltas as they're generated. Two practical consequences follow:
  - If a tool call is involved, its arguments can arrive as *fragments* of JSON spread across multiple chunks. They aren't guaranteed to be valid, parseable JSON until the stream finishes — so don't try to `json.loads()` a tool call mid-stream.
  - `usage_metadata` on individual chunks is often `None` or incomplete. You typically only get accurate token counts once all the chunks have been fully summed into one complete message.
- **`.batch()` concurrency is configurable, not unlimited.** LangChain's underlying `Runnable` interface accepts a `config` with `max_concurrency`, which caps how many requests actually run in parallel. This exists for a very practical reason: firing everything at once is a great way to get rate-limited by your provider the first time you run this against real traffic.

---

## 6. What Actually Happens, Step by Step

It helps to trace through the internal flow once, slowly, so none of this feels like a black box later.

**`.invoke()` with a message list:**

1. Your message list — objects, dicts, or a mix of both — is handed to the chat model.
2. LangChain's provider adapter coerces every entry into a single, canonical internal message representation.
3. That gets translated into whatever specific JSON shape the provider's API actually expects. (OpenAI's `messages` array and Anthropic's equivalent look genuinely different under the hood, even though your own code looked identical either way.)
4. The HTTP request goes out, and the provider sends back a completion.
5. The adapter parses that raw response into a single `AIMessage`, filling in `.content`, `.tool_calls` (if any were requested), `.usage_metadata`, `.response_metadata`, and assigning it an `.id`.
6. That finished `AIMessage` is handed back to you — synchronously, and only once the entire response is ready.

**`.stream()`:**

1. Steps 1–3 are identical to `.invoke()`.
2. Instead of one blocking HTTP call, the adapter opens a streaming connection instead.
3. As the provider generates tokens, each partial delta is parsed into an `AIMessageChunk` and handed straight to your `for` loop, immediately.
4. Each chunk supports `__add__`, so accumulating them (`full = full + chunk`, or the equivalent reduce) builds an object with the same shape and content as what `.invoke()` would have given you — just assembled piece by piece instead of all at once.
5. The stream closes once the provider signals it's done, and only *then* does the accumulated `usage_metadata` become reliable.

**`.batch()` / `.batch_as_completed()`:**

1. Every item in your input list is treated as its own independent `.invoke()`-equivalent call.
2. LangChain dispatches all of them concurrently — bounded by `max_concurrency` if you've set it — instead of looping through them one at a time.
3. `.batch()` waits for *every* call to finish, then returns a list of `AIMessage` objects in the *same order* as your original inputs, regardless of which one actually finished first.
4. `.batch_as_completed()` instead yields `(index, AIMessage)` pairs the moment each individual call finishes, so a slow item never blocks you from acting on a fast one that's already landed. The order these pairs arrive in is unpredictable by design — that's the trade you're making for speed.

**The manual tool-call round trip (what `create_agent` will later do for you):**

1. `model.bind_tools([...])` attaches tool schemas to the outgoing request. This doesn't *execute* anything — it just tells the model what tools are available to ask for.
2. `model.invoke(...)` comes back with an `AIMessage` whose `.content` might be empty, and whose `.tool_calls` field contains the model's *requested* function name, its arguments, and a `tool_call_id`.
3. Your code — not the model — actually runs the underlying Python function using those arguments.
4. You wrap the function's return value: `ToolMessage(content=result, tool_call_id=<the same id from step 2>)`.
5. You append the original `HumanMessage`, the `AIMessage` that requested the tool, and this new `ToolMessage` — in that exact order — into one list, and call `model.invoke(...)` again.
6. Now the model has the tool's actual result sitting in its context, and it produces a final `AIMessage` with real, natural-language `.content`.

---

## 7. Putting It All Together — A Worked Example

Let's ground all of this in one connected scenario: a support-ticket triage service that needs to (a) enforce a strict system policy, (b) track which support agent said what inside an internal thread, and (c) classify a backlog of a few thousand overnight tickets, efficiently.

Notice as you read this that all four patterns below are running on the *exact same* `model` object — you're not switching frameworks or clients depending on the situation, just choosing a different method to call on it.

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

Let's walk through *why* each block looks the way it does — this is the part that's easy to skim past, but it's where the real learning happens:

- **Block 1** is the simplest possible use case: one customer, one message, one answer. Notice `POLICY` never changes across the whole file — it's reused everywhere, exactly because a `SystemMessage` is meant to be a stable rule, not something you re-write per call. And `.invoke()` is used here specifically because this is a one-shot backend-style exchange — nobody's staring at a loading spinner, and there's nothing to batch.
- **Block 2** switches to `.stream()` the moment a real human is watching a screen. The generator pattern (`yield chunk.text`) is what lets you push each small piece of text out over a websocket the instant it exists, instead of making the customer wait for the entire reply to finish generating before they see a single word.
- **Block 3** is where `.batch_as_completed()` earns its keep. With a few thousand tickets, you genuinely do *not* want to wait for the single slowest ticket to classify before you can save any results. Notice how the loop saves each classification the moment it arrives — that's the entire point of "as completed" over plain `.batch()`.
- **Block 4** is the manual tool round trip from Section 6, made concrete. Trace the `tool_call_id`: it's generated by the model in `ai_request.tool_calls[0]["id"]`, and it reappears, unchanged, in `tool_message`. That's the thread that lets the model connect its own request to your answer. If you ever see a model hallucinating tool results or acting confused after a tool call, this ID match is usually the first thing worth checking.

---

## 8. From the Trenches — Production Advice

This is the stuff that doesn't show up in a tutorial, but will absolutely show up in your first few months running this for real.

- **On performance and cost.** Use `usage_metadata` on every `AIMessage` for your actual cost dashboards — it's real, provider-reported token counts, not an estimate from some tokenizer library that can quietly drift from what you're actually billed. And once you're processing more than a handful of independent prompts, `.batch()` / `.batch_as_completed()` will consistently beat a plain `for` loop of `.invoke()` calls, because sequential invokes pay full round-trip latency *N* separate times, instead of overlapping that latency through concurrency.
- **On reliability.** Set `timeout` and `max_retries` explicitly — don't just trust the provider's defaults. A single hung request buried inside a batch of a few hundred tickets can otherwise stall your entire job. `max_retries` does default to a sane nonzero value in LangChain's model classes, which helps, but a production system should still actively monitor for retry exhaustion rather than assuming things quietly self-heal in the background.
- **On security.** Never treat a `SystemMessage` as an ironclad guarantee against prompt injection. It dramatically raises the bar — the pirate-speak and Java-only demos genuinely hold up well against ordinary conversational attempts to override them — but a sufficiently adversarial input can sometimes still coax partial compliance out of a model. Treat the system message as your *primary* control, not your *only* one. Constrain what the model is actually *allowed to do* — through tool scoping, structured output schemas — rather than relying purely on instructions holding under pressure.
- **On observability and debugging.** Log the *full* message list you send, not just the final `.content` you got back. Weeks later, when a confusing bug report lands on your desk, "what exactly was in the system prompt and history at that moment" is almost always the first thing you need — and, frustratingly, the first thing teams forget to capture. It's worth persisting `response.id` and `response_metadata` alongside your own request IDs too, so you can correlate them with provider-side logs or LangSmith traces later.
- **On streaming in production.** Don't try to inspect or act on `tool_calls` from a stream that's still in progress — wait until the stream closes and the chunks have been fully summed. If your product needs both a live-typing feel *and* tool use, the practical pattern is to stream the natural-language portions, but let tool-call detection happen only once the message is complete.
- **On testing.** Because message objects and plain dicts are functionally equivalent, tests that assert on conversation shape can just use plain dicts for readability, without losing any fidelity to what's actually sent to the provider. And mock at the model-invocation boundary — the `.invoke` / `.stream` / `.batch` calls themselves — rather than mocking raw HTTP. It keeps your tests stable even when a provider or endpoint changes underneath you.

---

## 9. Mistakes I See Over and Over

If you only remember one section from this document to avoid getting burned, make it this one.

- **Cramming instructions into the user's message instead of a `SystemMessage`.** It seems to work at first — until the user's own text starts contradicting or diluting the instruction. This isn't a style preference; separating the two genuinely changes how strongly the model respects the instruction in the first place.
- **Sending a raw string or dict back after running a tool, instead of a proper `ToolMessage`.** The model has no contract for interpreting a bare string as "the result of the tool I just asked for." It needs that `tool_call_id` match to correctly connect cause and effect. Skip this, and you'll see models hallucinating tool results, or ignoring them entirely — and it'll look like a mysterious bug rather than the missing-ID problem it actually is.
- **Assuming `.content` is the whole story.** New engineers print `.content`, see a string, and stop looking. They then miss `.tool_calls`, `.usage_metadata`, and `.response_metadata` entirely — and end up reinventing token counting or tool-call detection badly, when the data was sitting right there on the object the whole time.
- **Trying to parse tool-call arguments mid-stream.** Streamed tool-call JSON can arrive in fragments. Code that tries to `json.loads()` a partial chunk will fail *intermittently* — which is exactly the kind of bug that's miserable to reproduce, because it depends on exactly where the chunk boundaries happened to fall.
- **Firing off `.batch()` with hundreds of items and no `max_concurrency` cap against a rate-limited provider.** This looks perfectly fine in testing with five items, and then falls over the first time it meets a real production backlog.
- **Confusing `.batch()` with `.batch_as_completed()`.** Using `.batch()` when you actually wanted to act on each result as it landed means your fastest response ends up stuck waiting behind your slowest one — for no good reason at all.

---

## 10. A Few Lines Worth Remembering

- *"The model never calls a tool — it only tells you which tool it wants called."* This sentence alone is often the fastest way to catch a shaky understanding, in an interview or in a code review.
- The system message is the *only* thing in a conversation you fully control. Everything else — what the user says, what a tool returns — is input you have to defensively handle, not instruction you get to simply rely on.
- Few-shot behavior correction belongs in your message history, not in an ever-growing system prompt. When an assistant kept answering in the wrong tone, the fix wasn't a longer system message — it was injecting a couple of example turns (a fake prior `HumanMessage`/`AIMessage` pair demonstrating the tone you actually wanted) ahead of the real conversation. Models tend to pick up on *demonstrated* behavior faster and more reliably than on *described* behavior.
- Batching doesn't mean the customer waits longer — it means you're running requests concurrently instead of one after another. This gets misunderstood constantly by engineers new to the idea, who assume "batch" automatically implies "queued and delayed."
- Don't build logic that depends on exact `response_metadata` fields staying stable across providers. Treat it as a helpful debugging aid — not a contract you can lean on.

---

## 11. Where to Go Deeper

- LangChain Messages concept guide: https://docs.langchain.com/oss/python/langchain/messages
- LangChain Chat Models — invoke/stream/batch interface: https://docs.langchain.com/oss/python/langchain/models
- `Runnable` interface (underlying `batch`, `batch_as_completed`, `max_concurrency`): https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html
- `AIMessage` API reference: https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html
- `ToolMessage` API reference: https://python.langchain.com/api_reference/core/messages/langchain_core.messages.tool.ToolMessage.html
- LangChain GitHub repository: https://github.com/langchain-ai/langchain

---

## 12. If You Take Away Nothing Else, Take Away This

- A message *list*, not a raw string, is how you give a conversation structure — `SystemMessage` for rules you control, `HumanMessage` for what the user said, `AIMessage` for what the model said, `ToolMessage` for what a tool returned.
- The model *requests* tool calls; it never executes them. Completing that loop by hand once — execute, wrap in `ToolMessage` with the matching `tool_call_id`, re-invoke — is exactly what makes `create_agent`'s automation feel like a shortcut later, instead of feeling like magic.
- `AIMessage` carries far more than `.content`. `.tool_calls`, `.usage_metadata`, `.response_metadata`, and `.id` are all real signal you should be actively using, not ignoring.
- Pick your invocation mode based on your product surface, not out of habit: `.invoke()` for a single backend answer, `.stream()` for anything a human is watching in real time, `.batch()` / `.batch_as_completed()` for independent bulk work where concurrency genuinely saves you wall-clock time and money.
- `AIMessageChunk` objects are additive by design — summing them reconstructs the exact same object `.invoke()` would have given you, which is exactly why your streaming and non-streaming code paths can share almost all of their downstream logic.
