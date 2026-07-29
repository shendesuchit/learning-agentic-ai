# ToolRuntime: Giving Tools Access to State, Context, and Memory

*Module: learning-agentic-ai · Level: Beginner · Language: Python · Framework: LangChain*

---

## 1. Engineering Problem

You've got a `suggest_movie` tool for Cinebot. It works fine in isolation — pass it a genre, it recommends something. But the actual product requirement is: a customer mentions once, early in the conversation, that they love sci-fi, and every recommendation after that — this session, and ideally the next time they come back — should just know that, without them repeating it.

Your first instinct might be to add a `user_preferences: dict` parameter to the tool and have the model pass it in every call. That doesn't work, and it's worth understanding precisely why: the model only knows what's in the conversation it can see. It can't hand you a persistent user record it never had access to in the first place, and even if you stuffed it into the system prompt, you'd be trusting the model to faithfully carry, and never garble, a piece of data it has no real reason to treat carefully. You need the tool itself to reach outside the conversation — into a real store, into per-invocation configuration, into the running conversation's own state — using access the *model never has to know about or manage*.

That's the gap `ToolRuntime` closes.

---

## 2. Why This Concept Exists

Every argument a tool declares becomes something the model has to see, understand, and correctly supply — that's the whole point of a tool's schema, covered in the Tools Fundamentals module. But that same mechanism becomes a liability the moment a tool needs something that isn't really the model's business to manage: a user ID pulled from the authenticated session, a feature flag, a reference to a persistent memory store, the current thread's execution metadata for logging. None of that should be a parameter the model fills in — you don't want the model guessing at a user ID, and you don't want to trust it to always remember to pass one correctly on every call.

`ToolRuntime` exists to give a tool a second channel of information, entirely separate from the model-visible arguments: things your application supplies at execution time, invisible to the model, but fully available inside the tool function itself. It's the mechanism that makes tools capable of being *stateful* and *context-aware* without turning that state into something the model has to carry around in its own reasoning.

---

## 3. How the Instructor Taught It

The instructor built directly on the "reserved argument names" gotcha from the Tools Fundamentals unit — you can't name a plain parameter `config` or `runtime`, because LangChain resolves those specially. `ToolRuntime` is the *correct* version of that idea: a properly typed parameter (`from langchain.tools import ToolRuntime`) that LangChain recognizes and automatically injects at execution time, distinct from an ordinary string parameter the model would need to supply.

His mirror analogy for this was a good one and worth keeping: **a model only sees its own reflection.** It only knows about the arguments explicitly declared in a tool's schema — nothing about what the tool function does internally with additional runtime access is visible to it, the same way you only see your own reflection in a mirror and nothing behind you. This is exactly why `ToolRuntime` doesn't compromise the "the model only knows what's in its schema" guarantee from earlier in the tools unit — it's not a backdoor for the model to smuggle extra data through, it's a channel the model isn't even aware exists.

He walked through the pieces available on a `runtime` object one at a time, each with a specific, distinct purpose:

- **`runtime.state`** — short-term memory: the running conversation's message history and any custom fields your agent's state schema defines. This is what a tool reaches into if it needs to look at what's already happened in *this* conversation.
- **`runtime.context`** — immutable, per-invocation configuration. Things set once when the agent run starts and that don't change mid-conversation — a user's tier, a request's originating locale, whatever your application decided at the start of this specific run.
- **`runtime.store`** — long-term, persistent memory that survives *across* conversations, not just within one. He demonstrated this directly with a `save_favorite_genre` tool: a customer mentions they like sci-fi, the tool writes that into `runtime.store`, and a later `suggest_movie` tool (potentially in a completely separate session) can read it back out. This was explicitly built on `InMemoryStore` for the demo, with the caveat, stated clearly, that a real production system needs something that actually persists beyond a single process's memory — the in-memory version is for learning the mechanism, not for shipping.
- **`runtime.stream_writer`** — a way for a tool to emit live progress updates while it's still executing, rather than only returning a final result once it's done. Useful for a long-running tool where the user benefits from seeing "still working on this" rather than a silent wait.
- **`runtime.execution_info`** — metadata about the current execution itself: thread ID, run ID, attempt count. He framed this specifically as a debugging and retry-tracking tool — when something goes wrong in production, this is what lets you correlate a specific tool execution back to a specific run.
- **`runtime.server_info`** — only populated when the agent is actually running on a LangGraph server; `None` when running locally. He mentioned this mainly so students wouldn't be confused seeing it come back empty during local development and assume something was broken.

He tied all of this back to a concrete motivating scenario that also became the setup for the following unit's "too many tools" discussion: a `book_vip_lounge` tool that should only be relevant to VIP-tier customers. Without a mechanism like `runtime.context` carrying the user's tier, either every user sees the tool (and the model can be tricked or simply confused into calling it for a non-VIP customer, which he demonstrated live going wrong), or you have to hardcode assumptions into the tool itself with no clean way to know who's actually asking. `ToolRuntime` is what lets a tool actually behave differently based on who's really calling it, using information that came from your application, not from anything the model had to correctly infer or pass along.

He was also explicit about the boundary of what `ToolRuntime` is *for*: it is not the mechanism for deciding which tools a model even gets to see in the first place (dynamically loading or gating tool visibility per user) — that's a distinct, not-yet-covered problem, addressed by middleware. `ToolRuntime` is about giving an *already-available* tool the context it needs to execute correctly, not about deciding whether that tool should be offered at all.

---

## 4. Deep Technical Explanation

A few things worth making explicit beyond the live walkthrough.

**How the injection actually happens.** When you declare a tool function with a parameter typed as `ToolRuntime`, LangChain's tool-calling machinery recognizes that type at schema-generation time and *excludes it* from the JSON schema sent to the model — this is precisely why it doesn't show up as something the model needs to supply. At execution time (inside `create_agent`'s loop, or anywhere else LangChain is driving tool execution with runtime context available), that parameter gets populated automatically with the current run's actual runtime object before your function body runs.

**`state` vs. `context` vs. `store`, more precisely.** These three are easy to blur together, but they answer different questions:
- `state` answers "what has happened *in this conversation so far*" — it's mutable within a single run and typically includes the message history plus whatever custom fields your agent's state schema adds.
- `context` answers "what was true when this run started, and shouldn't change mid-run" — closer to a request-scoped configuration object than to conversation data. It's set once, at invocation time, and tools read it, they don't write it.
- `store` answers "what should persist beyond this single conversation entirely" — the only one of the three explicitly designed to outlive a single run, which is what makes it the right place for genuine user memory (preferences, history across sessions) rather than anything conversation-scoped.

**`InMemoryStore` as a real, if limited, implementation.** It's not just a stub for demonstration — it's a legitimate `BaseStore` implementation usable in development, single-process deployments, or tests. The instructor's caveat about production readiness is accurate: it doesn't survive a process restart and doesn't share state across multiple server instances, which is exactly the gap a production deployment needs to fill with a persistent backend (Redis, Postgres, or another `BaseStore`-compatible implementation) — the interface (`.put()`, `.get()`, namespaced keys) stays the same regardless of which backend is behind it, which is the actual point of the abstraction.

**`stream_writer` and custom streaming.** This ties into LangGraph's broader custom-streaming support — a tool can call `runtime.stream_writer(...)` to push an arbitrary payload into the stream of updates a client is consuming, separate from the model's own token-by-token output. This is what lets a UI show "checking inventory..." while a slow tool is still running, rather than the UI going quiet until the tool returns.

**`execution_info` fields, precisely.** This typically surfaces identifiers tied to the underlying LangGraph run — a thread ID (identifying a persistent conversation across multiple invocations, relevant once you're using checkpointing), a run ID (identifying this specific invocation), and retry/attempt count (relevant when a tool call is being retried after a validation failure or transient error, tying back to the same retry mechanism used in structured output). None of this is meant for end users; it's operational metadata for your own logging and debugging.

---

## 5. Internal Execution Flow

**Declaring a runtime-aware tool:**

1. You define a tool function with an ordinary set of model-visible parameters, plus one additional parameter typed as `ToolRuntime`.
2. When LangChain generates the tool's schema (for `bind_tools`, or for `create_agent`), it inspects parameter types, recognizes the `ToolRuntime`-typed one, and excludes it from what's sent to the model — the model's schema only ever contains the ordinary parameters.

**A tool call involving runtime access, end to end:**

1. The model requests the tool exactly as normal, supplying only the ordinary, schema-visible arguments — it has no awareness that a runtime object will also be involved.
2. When `create_agent`'s execution loop actually runs the tool, it constructs (or has available) the current run's runtime object — populated with the live `state`, the run's `context`, a handle to the configured `store`, a `stream_writer` bound to this run, and the current `execution_info`.
3. That runtime object is passed into your function as the `ToolRuntime`-typed argument, alongside the model-supplied ordinary arguments.
4. Your function body executes with both sources of information available: what the model explicitly asked for, and what your application already knew about this run.
5. If the tool writes to `runtime.store`, that write is committed to whatever backend the store is configured with — from that point forward, any tool (in this run or a future one) reading the same namespace/key sees the updated value.
6. The tool's return value is wrapped into a `ToolMessage`, exactly as with any other tool — the runtime access doesn't change anything about how the *result* flows back to the model; it only changes what the tool had available while producing that result.

---

## 6. Practical Engineering Example

A customer-support agent that needs to (a) remember a customer's stated preference across sessions, (b) restrict an escalation tool to a specific support tier using per-run context, and (c) emit progress updates while checking a slow backend system.

```python
from langchain.tools import ToolRuntime, tool
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

@tool
def save_customer_preference(preference: str, runtime: ToolRuntime) -> str:
    """Save a stated customer preference (e.g. preferred contact method) for future sessions."""
    user_id = runtime.context.get("user_id")
    runtime.store.put(("preferences", user_id), "contact_method", {"value": preference})
    return f"Noted -- will use {preference} as the preferred contact method going forward."

@tool
def get_customer_preference(runtime: ToolRuntime) -> str:
    """Look up a previously saved customer preference for this user."""
    user_id = runtime.context.get("user_id")
    result = runtime.store.get(("preferences", user_id), "contact_method")
    if result is None:
        return "No preference on file yet."
    return f"Preferred contact method on file: {result.value['value']}"

@tool
def escalate_to_senior_support(issue: str, runtime: ToolRuntime) -> str:
    """Escalate an issue to senior support. Only available for premium-tier customers."""
    tier = runtime.context.get("customer_tier")
    if tier != "premium":
        return "Escalation to senior support isn't available on the current plan."
    runtime.stream_writer({"status": f"Escalating: {issue}"})
    ticket_id = create_escalation_ticket(issue, thread_id=runtime.execution_info.thread_id)
    return f"Escalated. Ticket ID: {ticket_id}"

agent = create_agent(
    model="openai:gpt-5-mini",
    tools=[save_customer_preference, get_customer_preference, escalate_to_senior_support],
    store=store,
)

# context is supplied per invocation -- this is what makes tier-gating actually trustworthy,
# because it comes from your application's session/auth layer, not from anything the model said.
result = agent.invoke(
    {"messages": [{"role": "user", "content": "My billing keeps failing, please escalate this."}]},
    context={"user_id": "cust_9981", "customer_tier": "premium"},
)
print(result["messages"][-1].content)
```

Notice `escalate_to_senior_support` never asks the model to supply the customer's tier as an argument — that would mean trusting the model to know and honestly report something it has no real way to verify. The tier comes from `runtime.context`, set by your own authenticated request handling, completely outside the model's control.

---

## 7. Production Perspective

**Reliability and trust boundaries.** Anything security- or authorization-relevant — tier gating, permission checks, user identity — belongs in `runtime.context`, never in a model-supplied argument. A model-supplied argument is, functionally, user-influenceable input; `runtime.context` is set by your own trusted application code before the model ever sees the conversation.

**Scalability of the store.** `InMemoryStore` is correct for development and tests, and actively wrong for a multi-instance production deployment — state written on one server instance won't be visible from a request served by another, and a restart wipes everything. Swap in a persistent `BaseStore` implementation before this reaches real users; the tool code itself doesn't need to change, only the store you construct and pass in.

**Observability and debugging.** `runtime.execution_info` (thread ID, run ID, attempt count) is exactly the correlation data you want flowing into your logs from inside tool execution — when a customer reports something went wrong, being able to pull every tool call tied to their specific thread ID, across every attempt, is the difference between a five-minute investigation and an hour of guessing.

**Testing.** Tools that depend on `ToolRuntime` are still directly unit-testable — construct a runtime object (or a test double with the same interface) with known `state`/`context`/`store` values and call the tool function directly, without needing a live model or a full agent run, to verify the tool's logic in isolation.

**Design boundary worth respecting.** `ToolRuntime` gives an available tool the context it needs to execute correctly — it is not the mechanism for deciding *whether* a tool should be visible to a given user in the first place. Conflating the two leads to a tool that's technically available to everyone but silently no-ops or refuses for most of them, which is a worse experience (and a worse debugging story) than the tool simply not being offered. Visibility gating is a middleware concern; runtime access is an execution-time concern.

---

## 8. Common Mistakes

- **Asking the model to supply something that should come from `context` or `store`.** User IDs, tiers, and permissions passed as ordinary tool arguments are trusting the model to correctly track and honestly report something it has no real authority over.
- **Shipping `InMemoryStore` to production without realizing it doesn't persist or share across instances.** Works perfectly in every local demo, then silently loses data the moment there's more than one server process or a restart.
- **Writing to `runtime.state` expecting it to persist beyond the current run.** State is conversation-scoped; if something needs to survive across sessions, it belongs in `store`, not `state`.
- **Using `ToolRuntime` to try to control which tools a model can see.** That's a different problem (tool visibility/gating), not something `ToolRuntime` itself solves — a tool with runtime access is still fully visible to the model; the runtime just informs what it does once called.
- **Forgetting `server_info` will be `None` locally and treating that as a bug.** It's only populated when actually running on a LangGraph server — expected, not broken, during local development.

---

## 9. Instructor Insights

- The mirror analogy — "a model only sees its own reflection," meaning only the arguments in its declared schema — is worth keeping as the mental check any time you're deciding whether something belongs as a tool argument or as `ToolRuntime` access instead. If the model has no legitimate way to know or verify it, it shouldn't be an argument the model supplies.
- The VIP-lounge tool-visibility failure was demonstrated deliberately as a live mistake, not a hypothetical — a tool being *technically available* to a user it shouldn't apply to is a real, reproducible failure mode, and it's exactly the kind of thing that motivates middleware later, not something `ToolRuntime` alone resolves.
- `InMemoryStore` is explicitly a learning tool, not a production recommendation — treat any demo using it as "here's the interface," not "here's what to deploy."
- `runtime.execution_info` is the kind of field that seems unnecessary until the first time you're debugging a production incident and desperately want to know which specific run and attempt produced a given tool call — worth wiring into logging from day one rather than adding it reactively after an incident.

---

## 10. Official References

- LangChain Tools concept guide (runtime context section): https://docs.langchain.com/oss/python/langchain/tools
- LangGraph persistence and stores (`BaseStore`, `InMemoryStore`): https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph streaming (custom stream writer): https://docs.langchain.com/oss/python/langgraph/streaming
- `create_agent` context and state configuration: https://docs.langchain.com/oss/python/langchain/agents
- LangChain GitHub repository: https://github.com/langchain-ai/langchain

---

## 11. Key Takeaways

- `ToolRuntime` gives a tool a second, model-invisible channel of information — `state` for what's happened in this conversation, `context` for immutable per-run configuration, `store` for memory that persists across conversations entirely.
- The model never sees or supplies anything through `ToolRuntime` — LangChain excludes it from the tool's schema automatically, which is exactly why it's the right place for anything security- or identity-relevant that a model shouldn't be trusted to carry.
- `store` is the only one of the three built to outlive a single run — use it for genuine cross-session memory, and swap `InMemoryStore` for a real persistent backend before production, since the interface doesn't change but the guarantees do.
- `ToolRuntime` answers "what does an available tool need to execute correctly" — it does not answer "which tools should this user even see," which is a separate, middleware-level concern.
- `execution_info` is cheap to log and expensive to regret not having — wire thread ID, run ID, and attempt count into your observability from the start rather than after the first hard-to-reproduce production bug.
