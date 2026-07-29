# Tool Calling Mechanics: `bind_tools` vs. Execution

*Module: learning-agentic-ai · Level: Beginner · Language: Python · Framework: LangChain*

---

## 1. Engineering Problem

You've written a `book_seats` tool, decorated it, given it a good docstring and a validated schema. You call `model.bind_tools([book_seats])`, send it "book 2 tickets for Inception," and the model comes back... and nothing happened. No booking. `response.content` is empty. You didn't get an error, you didn't get a booking confirmation, you got what looks like a broken response.

It isn't broken. This is the single most common point of confusion for engineers new to tool calling, and it's worth getting precisely right early, because it's also one of the fastest ways to expose a shaky understanding in a code review or an interview: **binding a tool to a model does not execute anything.** It tells the model the tool exists. The model's job, and the only thing it's actually capable of, is deciding whether to *request* that tool be called, and with what arguments. Someone still has to actually run it.

---

## 2. Why This Concept Exists

The split between "model requests a tool" and "something executes the tool" isn't an arbitrary API design choice — it reflects a real, unavoidable boundary. A language model is a text-in, text-out (or, more precisely, tokens-in, tokens-out) system. It has no access to your database, your filesystem, your payment processor, or any side effect in the real world. It cannot execute Python. The only thing it can do is produce output — and "output" for a tool-aware model is a structured description of a function call it would like made on its behalf.

Given that boundary, `bind_tools` exists to solve a narrower problem than "make the model do things": it solves "tell the model what's available, in a format it can reliably request from." Execution has to live somewhere else, because it fundamentally requires code that runs outside the model — your process, with real access to the systems the tool touches. Understanding this split isn't just trivia; it explains why `create_agent` exists at all (it's the thing that automates the execution half) and why a raw model with tools bound to it will always feel "incomplete" on its own.

---

## 3. How the Instructor Taught It

The instructor's core line on this, repeated across multiple sessions specifically because it's the concept most likely to be misunderstood: **"the model can never call a tool, it can only tell you which tool to call."** He treated this as close to a checkpoint question for the whole tools unit — if you can't explain this cleanly, you don't yet understand tool calling, no matter how much code you've copied.

He demonstrated the mechanics directly, with a `get_weather` tool, before ever introducing `create_agent`, specifically so the automation that comes later wouldn't feel like a black box.

**Step one: binding.** `model.bind_tools([get_weather])` — nothing executes here. All this does is attach the tool's schema (name, description, parameters) to every subsequent request made through that bound model object, so the provider's API knows what's on offer.

**Step two: invoking a bound model.** Call `.invoke()` on the bound model with a prompt that plausibly needs the tool — "what's the weather in Paris?" He had students actually print the response and look at it closely, because the result is instructive precisely because it looks broken if you don't know what you're looking at: `response.content` comes back empty (or near-empty), and `response.tool_calls` comes back populated with the tool's name, the arguments the model wants to pass, and a `tool_call_id`. He was insistent that students internalize this is a *request*, not a completed action — nothing has run yet.

**Step three: manual execution.** Take the tool call off `response.tool_calls[0]`, actually invoke the underlying Python function yourself with those arguments (`get_weather(**tool_call["args"])`), and get a real result back.

**Step four: closing the loop.** Wrap that real result in a `ToolMessage`, matching the exact `tool_call_id` from the model's request — not appending it as a plain string, which he called out explicitly as a common and easy mistake — and build a new message list: the original `HumanMessage`, the `AIMessage` that requested the tool (with its `tool_calls` still attached), and the new `ToolMessage`. Send that whole list back through `model.invoke(...)`. Only *now* does the model produce a natural-language final answer, because only now does it actually have the tool's result in its context.

He reused this same walkthrough later (in the tools deep-dive session) specifically to set up the contrast with `create_agent`: everything from step three onward — executing the actual function, wrapping the result correctly, re-invoking — is exactly what `create_agent`'s internal loop automates for you. He was explicit that seeing the manual version once is what makes the automated version feel like "a shortcut for real work," rather than magic you can't reason about when something goes wrong inside it.

A second point he reinforced later, in the `ToolRuntime` discussion: the model only ever sees the arguments it's told about through the tool's declared schema — it has no visibility into anything else your tool function might access at execution time (state, config, a persistent store). That's a different mechanism (`ToolRuntime`, covered separately), but it depends on this same underlying fact — the model requests, your code executes, and your code can have access to things the model's request never mentions.

---

## 4. Deep Technical Explanation

A bit more precision on what's actually happening in each of those steps, beyond what a live demo covers.

**What `bind_tools` actually attaches.** Calling `model.bind_tools([...])` doesn't mutate the original model object — it returns a new `Runnable` wrapping the original model, with the tool schemas attached as part of its invocation configuration. This is why it's common to see `model_with_tools = model.bind_tools([...])` as a separate variable rather than reassigning `model` — the two are genuinely different objects, and the original unbound model is still usable elsewhere without tools attached, which is often exactly what you want (e.g., a final response-formatting call that shouldn't have tool access at all).

**What an `AIMessage.tool_calls` entry actually contains.** Each entry is a dictionary with (at minimum) `name` (the tool's registered name — respecting any override you gave `@tool`), `args` (a dict of arguments the model believes satisfy the tool's schema), and `id` (a unique identifier for this specific call, generated by the provider, used to correlate the eventual `ToolMessage` back to this exact request). A single `AIMessage` can contain multiple `tool_calls` if the model decides it needs more than one tool invoked to answer the current turn — this is a real, common case (checking weather in two cities in one request, for instance), and your execution logic needs to handle a list, not assume exactly one call.

**Why the `tool_call_id` match matters mechanically, not just stylistically.** Providers track tool-call state on their end using that id. If you send back a `ToolMessage` with a mismatched or missing `tool_call_id`, most providers will reject the request outright with a validation error, rather than silently accepting it — this is a stricter contract than it might appear from the outside, and it's exactly why hand-rolling this step correctly the first time matters.

**Where `create_agent` actually sits relative to this.** `create_agent` builds a graph (a LangGraph graph, under the hood) where a tool-call request from the model routes to a node that executes the matching registered tool automatically, wraps the result into a correctly-`tool_call_id`-matched `ToolMessage`, appends it to the running message state, and loops back to the model — repeating until the model produces a response that doesn't request further tool calls (or, if `response_format` is set, until a valid structured response is produced). Nothing about this is a different mechanism from the manual version; it's the exact same request → execute → wrap → re-invoke sequence, just driven automatically instead of by your own code.

**`tool_choice`, a related knob not always covered in an intro pass.** Beyond simply binding tools, LangChain's `bind_tools` accepts a `tool_choice` parameter on providers that support it — forcing the model to call a specific tool, forcing it to call *some* tool rather than answering in plain text, or leaving the decision entirely up to the model (the default). This is worth knowing for cases where "the model might just ignore my tool and answer in prose" is actually a problem for your use case — a strict data-extraction pipeline, for instance, where you never want a free-text fallback.

---

## 5. Internal Execution Flow

**Binding tools to a model:**

1. You call `model.bind_tools([tool_a, tool_b, ...])`.
2. Each tool object's `.name`, `.description`, and JSON-Schema-converted `.args_schema` get attached as part of the bound model's invocation configuration.
3. A new, wrapped model-like object is returned — the original `model` is untouched.

**A single invocation against the bound model:**

1. You call `.invoke()` (or `.stream()`/`.batch()`) with a message list.
2. The bound model's configuration — including all attached tool schemas — is sent to the provider alongside your messages.
3. The provider's model evaluates whether any available tool is relevant to producing a good response.
4. **If no tool is needed:** you get back a normal `AIMessage` with populated `.content` and an empty `.tool_calls` list — behaves exactly like an unbound model.
5. **If a tool is needed:** you get back an `AIMessage` with `.tool_calls` populated (name, args, id per call) and `.content` typically empty or minimal — this is a request, not a completed action, and nothing outside the provider's own inference process has happened yet.

**Manual execution and loop closure (what you do by hand, or what `create_agent` automates):**

1. Read each entry out of `response.tool_calls`.
2. For each one, look up the matching Python tool by `name` and call it with `**entry["args"]`.
3. Wrap each real return value in `ToolMessage(content=result, tool_call_id=entry["id"])`.
4. Build a new message list: the prior history, plus the `AIMessage` that made the request (with its `tool_calls` intact), plus each new `ToolMessage`, in order.
5. Re-invoke the model with this extended list. The model now has the tool's actual result in context and can produce a grounded natural-language (or, combined with structured output, schema-validated) final response.
6. If the model decides it needs to call another tool based on what it just saw, this entire cycle repeats — which is precisely the "loop" in "an agent is a model calling tools in a loop until a task is complete."

---

## 6. Practical Engineering Example

An internal ops assistant that checks a real deployment pipeline's status — showing the manual mechanics explicitly, since seeing this once by hand is exactly the point before you ever hand it to `create_agent`.

```python
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

@tool
def get_pipeline_status(pipeline_name: str) -> str:
    """Check the current run status of a CI/CD pipeline by name."""
    return f"{pipeline_name}: last run succeeded 12 minutes ago, currently idle."

model = init_chat_model("openai:gpt-5-mini", temperature=0)
model_with_tools = model.bind_tools([get_pipeline_status])

question = HumanMessage("Is the billing-api pipeline currently healthy?")
ai_request = model_with_tools.invoke([question])

# At this point, nothing has actually run.
print(ai_request.content)      # likely empty
print(ai_request.tool_calls)   # [{'name': 'get_pipeline_status', 'args': {'pipeline_name': 'billing-api'}, 'id': '...'}]

# Manually execute every requested tool call -- a model can request more than one.
tool_messages = []
for call in ai_request.tool_calls:
    if call["name"] == "get_pipeline_status":
        result = get_pipeline_status.invoke(call["args"])
    else:
        result = f"Unknown tool requested: {call['name']}"
    tool_messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

# Close the loop: prior history + the request + the results, then re-invoke.
final = model.invoke([question, ai_request, *tool_messages])
print(final.content)
# "Yes, billing-api is healthy -- its last run succeeded 12 minutes ago and it's currently idle."

# The exact same behavior, automated:
from langchain.agents import create_agent
agent = create_agent(model=model, tools=[get_pipeline_status])
result = agent.invoke({"messages": [question]})
print(result["messages"][-1].content)
```

Running both the manual version and the `create_agent` version side by side, on the same tool, is a genuinely good way to confirm you understand what the agent is actually doing for you — it's not doing anything you couldn't write yourself, it's just doing it reliably, every time, without you re-implementing the loop in every project.

---

## 7. Production Perspective

**Reliability.** Never send a raw string or the bare tool return value back to the model in place of a proper `ToolMessage` — providers validate the `tool_call_id` correlation, and even where they don't strictly enforce it, an ungrounded string loses the structural signal that tells the model "this is specifically the answer to the tool call you just made," which increases the odds of a confused or hallucinated follow-up.

**Handling multiple simultaneous tool calls.** Production tool-execution code should always iterate `response.tool_calls` as a list, never assume a single entry — a model asking for two independent lookups in one turn is common and expected behavior once you have more than a trivial tool set, and code written assuming exactly one call will silently drop the second request.

**Error handling during execution.** If your tool function raises during manual execution (a downstream API times out, a lookup fails), don't let the exception propagate uncaught — catch it and wrap the *error* as the `ToolMessage` content instead, so the model gets a chance to react sensibly ("that lookup failed, try a different approach" or "tell the user this isn't available right now") rather than your whole request pipeline crashing. `create_agent` and `ToolStrategy` both build on exactly this pattern for validation failures; the same principle applies to raw execution failures.

**Observability.** Log the full `tool_calls` payload from every `AIMessage`, not just the final answer — when a production agent does something unexpected, "what did it actually request, with what arguments" is almost always the first thing you need to see, and it's easy to reconstruct if you were already capturing it, painful if you weren't.

**Security.** Because a tool call is a request your code chooses to honor, you retain full control over what actually happens — this is a legitimate place to add authorization checks, argument sanitization, or rate limiting before executing, regardless of how confidently the model requested the call. Treat a model's tool-call request the same way you'd treat any other untrusted input reaching your business logic.

**Testing.** The manual request → execute → wrap → re-invoke sequence is straightforward to unit test in isolation: mock the bound model's `.invoke()` to return a fixed `AIMessage` with a known `tool_calls` payload, and assert your execution/wrapping logic produces the correct `ToolMessage`s — you don't need a live model call to verify this part of your pipeline is correct.

---

## 8. Common Mistakes

- **Assuming `bind_tools` executes anything.** The most common version of this mistake is treating an empty `.content` and populated `.tool_calls` as a bug rather than expected behavior for a tool-requesting response.
- **Sending back the raw return value instead of a `ToolMessage`.** Breaks the structural correlation between request and result that providers rely on, and increases the odds of the model losing track of what actually happened.
- **Mismatching, or omitting, `tool_call_id`.** This isn't a soft mistake — most providers will reject the request outright rather than silently accepting a `ToolMessage` that doesn't correlate to a real prior tool call.
- **Assuming exactly one tool call per `AIMessage`.** Real tool-aware conversations regularly produce multiple simultaneous requests; code that only reads `tool_calls[0]` silently drops the rest.
- **Reimplementing the manual loop indefinitely in every project instead of switching to `create_agent` once the mechanics are understood.** Useful once, for understanding — not something you want maintained by hand across a real codebase, where you'll also want retries, multi-turn looping, and structured-output resolution that `create_agent` already handles.
- **Letting a tool execution exception crash the whole request instead of feeding the failure back as a `ToolMessage`.** The model can often recover gracefully from "that failed" if you give it the chance; an uncaught exception gives it no chance at all.

---

## 9. Instructor Insights

- "The model can never call a tool, it can only tell you which tool to call" is worth being able to state cleanly and immediately — it's the fastest way to confirm (to yourself, a teammate, or an interviewer) that you actually understand tool calling rather than having copied working code.
- Seeing the manual round trip once, before ever touching `create_agent`, is a deliberate teaching choice, not a detour — it's what turns the automated loop from something you trust blindly into something you can actually debug when it misbehaves.
- Printing `response.tool_calls` right after a bound-model invoke, before doing anything else, is a habit worth keeping permanently — it's the fastest way to confirm what the model actually requested versus what you assumed it would request.
- The `ToolRuntime` mechanism (covered separately) exists specifically because the model's tool-call request only ever contains what's in the declared schema — anything your tool needs beyond that (session state, persistent memory, per-invocation config) has to reach it through a different channel, not through the model's request.

---

## 10. Official References

- LangChain Tool calling concept guide: https://docs.langchain.com/oss/python/langchain/tools
- `bind_tools` API reference (on chat model base class): https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.chat_models.BaseChatModel.html#langchain_core.language_models.chat_models.BaseChatModel.bind_tools
- `AIMessage.tool_calls` structure: https://python.langchain.com/api_reference/core/messages/langchain_core.messages.ai.AIMessage.html
- `ToolMessage` API reference: https://python.langchain.com/api_reference/core/messages/langchain_core.messages.tool.ToolMessage.html
- `create_agent` (automated tool-execution loop): https://docs.langchain.com/oss/python/langchain/agents
- LangChain GitHub repository: https://github.com/langchain-ai/langchain

---

## 11. Key Takeaways

- `bind_tools` only informs the model what's available — it never executes anything. An `AIMessage` with populated `tool_calls` and empty `content` is a request, not a completed action, and that's expected, not broken.
- Closing the loop by hand is always the same four steps: read the request, execute the real function, wrap the result in a `ToolMessage` with the matching `tool_call_id`, re-invoke with the extended history.
- `tool_call_id` correlation is a hard contract most providers enforce, not a style suggestion — get it wrong and the request can be rejected outright.
- A model can request multiple tool calls in one `AIMessage`. Production code has to iterate the full list, not assume a single entry.
- `create_agent` doesn't introduce a new mechanism — it automates exactly the manual sequence above, on a loop, until the model is done. Understanding the manual version is what makes the automated version debuggable instead of magical.
