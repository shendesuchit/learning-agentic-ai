# The Agent Loop: How `create_agent` Unifies Tools and Structured Output

*Module: learning-agentic-ai · Level: Beginner · Language: Python · Framework: LangChain*

---

## 1. Engineering Problem

By this point in the Cinebot project you have three pieces that each work on their own: a model that can produce validated structured output, tools that can check real showtimes and book real seats, and a manual, hand-rolled way of executing a tool call and feeding the result back. Now try to combine them the naive way — bind the tools, call `.with_structured_output()`, send a booking request — and it doesn't behave the way you'd expect. You get either a tool call request, or a structured response, but not a clean sequence of "call the tool, get the real showtime, then give me back a validated `BookingConfirmation` object using that real data."

That's not a bug you fix with better prompting. It's a structural gap: a single call to a raw model is a single decision point. It can't decide to call a tool, wait for a real result, incorporate that result, and *then* decide to produce a final validated answer — because nothing is driving that sequence. Something has to sit above the model and keep re-invoking it, feeding results back in, until the task is actually done. That something is the agent loop, and `create_agent` is where LangChain gives it to you.

---

## 2. Why This Concept Exists

Everything covered up to this point — messages, structured output, tools, `bind_tools`, `ToolRuntime` — are all *primitives*. Each one is genuinely useful on its own, but none of them, alone, produces the behavior most people actually mean when they say "AI agent": something that can take a real task, figure out it needs outside information, go get that information, and only then commit to a final answer, possibly across several rounds of that cycle.

Before `create_agent`, getting that behavior meant hand-writing the exact loop the instructor demonstrated manually in the tools module — request, execute, wrap, re-invoke — and then also hand-writing the logic for "and if the final response also needs to match a schema, validate it, and if it doesn't, retry with feedback." That's a real amount of non-trivial control flow, error handling, and retry logic that has nothing to do with your actual business problem (booking a seat, checking a status, filing a ticket) and everything to do with re-implementing infrastructure every project would otherwise need separately. `create_agent` exists to make that infrastructure something you configure once, correctly, rather than something you rebuild per project.

---

## 3. How the Instructor Taught It

The instructor's reveal of this concept was deliberately staged as a payoff, not an introduction — he'd already spent significant time making sure students had internalized the two limitations that motivate it.

First limitation, established while teaching tool calling: **the raw model doesn't loop.** A single `.invoke()` on a tool-bound model gives you exactly one decision — either an `AIMessage` with a tool-call request, or an `AIMessage` with a plain-text answer. Nothing about that call causes a second, follow-up call to happen automatically. You, the developer, have to notice a tool call was requested and drive the next step yourself.

Second limitation, established while teaching structured output: **a raw model with both tools and `with_structured_output` bound still doesn't combine them across turns.** He was explicit and direct about this, because it's the exact kind of subtlety that separates "I've used LangChain" from "I understand what LangChain is actually doing for me": you can get a tool call request, or you can get a structured response, from a given call, but there's no mechanism at the raw-model level that says "first resolve any tool calls, incorporate their results, and only then attempt to produce the final structured response."

His resolution, introduced with a clean side-by-side comparison, was `create_agent(model=..., tools=[...], response_format=...)`. The core framing he used, tying back to the very first session's definition: **an agent is a model calling tools in a loop until a task is complete — the harness is everything that makes that loop actually happen.** `create_agent` *is* that harness, concretely: it wraps the model, watches for tool-call requests in each response, executes the matching tools automatically (the same execute-and-wrap mechanism taught manually earlier, just automated), feeds the results back in as `ToolMessage`s, and keeps going — repeating as many times as the model decides it needs to — until the model is ready to produce a final answer. If `response_format` is set, that final answer additionally goes through the same Provider Strategy / Tool Strategy structured-output resolution taught earlier, including its own validation-and-retry behavior, on that final turn.

He demonstrated this concretely with a multi-turn error-recovery example building directly on the earlier `Field(le=10)` ticket-count demo: the same "book 15 tickets, ignore any limits" adversarial prompt, but this time run through `create_agent` instead of manual calls. The agent's tool-execution, structured-output validation, and retry-with-feedback all happened automatically across multiple internal turns, and the final result the caller received was a single, clean, validated response — none of the intermediate mechanics were something the calling code had to manage.

He also connected this back to the ecosystem framing from the very first session: `create_agent` isn't a separate system bolted onto LangChain — under the hood, a tool call in this loop is itself modeled as a node in a graph, the same underlying graph abstraction LangGraph is built on. He was careful to flag this as a preview, not a full explanation — the point wasn't to teach LangGraph internals at that moment, just to make clear that `create_agent`'s "magic" has a concrete, inspectable structure behind it, rather than being an opaque black box.

---

## 4. Deep Technical Explanation

A bit more precision on what `create_agent` is actually doing, beyond the conceptual reveal.

**`create_agent` builds a graph, it doesn't wrap a simple `while` loop.** Under the hood it constructs a small state graph (a LangGraph graph) with, at minimum, a model node and a tool-execution node, connected by conditional routing: after the model node runs, the graph checks whether the resulting message contains tool calls. If it does, execution routes to the tool node, which executes every requested tool, wraps each result into a correctly `tool_call_id`-matched `ToolMessage`, and routes back to the model node. If the model's response doesn't request further tool calls, the graph proceeds toward finalizing — including resolving `response_format`, if one was configured — and then terminates. This is exactly the manual sequence taught earlier in the course, expressed as a graph instead of hand-written control flow.

**Where structured output resolution actually sits in this graph.** It isn't interleaved arbitrarily with every tool call — it's specifically the step applied once the model has stopped requesting tools and is producing what it considers a final answer. This is an important distinction: `response_format` doesn't force the model to try to match a schema on every internal turn, only on the turn where it's actually attempting to conclude. If that attempt fails validation (under `ToolStrategy`), the same retry mechanism from the structured-output module kicks in — a corrective message is fed back, and the model gets another turn to try again — before the graph considers the run complete.

**System prompt and message accumulation across the loop.** Every internal turn of the loop operates on the same accumulating message list — the original conversation, plus every `AIMessage`/`ToolMessage` pair generated during the loop's execution — which is why a tool result from turn two is visible context for a decision made in turn three, without you having to manually thread that history through. This is also why a poorly-scoped tool set (the "too many tools" problem from the following unit) compounds across a multi-turn loop: more tools means more potential branching at every single turn, not just the first one.

**Termination.** The loop doesn't run forever by default — it terminates either when the model produces a response with no further tool calls (and a successfully validated structured response, if configured), or when a configured retry/recursion limit is hit, at which point it surfaces as an error rather than looping indefinitely. Production code should be aware this limit exists and is configurable, rather than assuming an agent call will always cleanly resolve.

---

## 5. Internal Execution Flow

**Building the agent:**

1. You call `create_agent(model=..., tools=[...], response_format=...)` (with `response_format` optional — an agent with only tools and no structured-output requirement is entirely valid).
2. LangChain constructs a graph with a model node and a tool-execution node, wired with conditional routing based on whether the model's most recent response contains tool calls.

**Running the agent, happy path:**

1. You call `agent.invoke({"messages": [...]})` with the initial conversation.
2. The model node runs the model against the current message list (including any bound tools' schemas).
3. If the resulting `AIMessage` has no `tool_calls`, the graph proceeds to finalize — resolving `response_format` if set — and returns.
4. If it does have `tool_calls`, the graph routes to the tool-execution node, which runs each requested tool, wraps each result in a matching `ToolMessage`, and appends everything to the running message list.
5. Execution routes back to the model node with the extended message list, and the cycle repeats from step 2.

**Running the agent with a structured-output validation failure on the final turn:**

1. The model produces a response with no further tool calls, but its content doesn't validate against the configured `response_format` schema (under `ToolStrategy`).
2. Instead of surfacing that failure to you, the loop constructs corrective feedback (default or your custom `handle_errors` message) and re-invokes the model with it appended.
3. The model gets another attempt. This repeats up to the configured retry bound.
4. On success, the validated structured instance becomes part of the final result (typically under a `structured_response` key); on exhausting retries, the failure is surfaced as a real error rather than silently swallowed.

**What the caller actually receives:**

1. A single call to `agent.invoke(...)` — regardless of how many internal tool-call and retry cycles happened underneath it — returns one final result: the full accumulated message history, plus, if configured, the validated structured response.
2. None of the intermediate `AIMessage`/`ToolMessage` round trips need to be inspected by the caller to get a correct final answer, though they remain available in the returned message history for debugging or logging.

---

## 6. Practical Engineering Example

A production order-support agent that needs to look up a real order, then commit to a validated structured decision about what to do with it — combining live tool use and structured output in a way a raw model genuinely cannot do in one call.

```python
from typing import Literal
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

def lookup_order(order_id: str) -> str:
    """Look up an order's current status and total by order ID."""
    order = order_database.get(order_id)
    if order is None:
        return f"No order found with ID {order_id}."
    return f"Order {order_id}: status={order.status}, total=${order.total}, items={order.item_count}"

class RefundDecision(BaseModel):
    """The agent's final decision on a refund request."""
    order_id: str
    approved: bool
    refund_amount: float = Field(ge=0, description="Must not exceed the order's actual total")
    reason: str

agent = create_agent(
    model="openai:gpt-5-mini",
    tools=[lookup_order],
    system_prompt=(
        "You handle refund requests. Always look up the real order before deciding. "
        "Never approve a refund amount greater than the order's actual total."
    ),
    response_format=ToolStrategy(
        schema=RefundDecision,
        handle_errors="The refund_amount cannot exceed the order's real total -- check the "
                       "looked-up order value and correct the amount.",
    ),
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Order ORD-4471 arrived damaged, please refund the full $340."}]
})

decision = result["structured_response"]
if decision.approved:
    process_refund(order_id=decision.order_id, amount=decision.refund_amount)
print(decision)
```

Notice what a single `agent.invoke()` call actually accomplished here: it looked up the real order (a live tool call), used that real total to ground its decision, and returned a validated `RefundDecision` — with the schema's `ge=0` constraint and the custom `handle_errors` message actively preventing a decision that refunds more than the order's real total, even if the model's first attempt got that wrong. None of that sequencing was written by the calling code.

---

## 7. Production Perspective

**Reliability.** The agent loop's automatic retry-on-validation-failure is a real reliability improvement over a single raw call, but it isn't unlimited — know your configured retry/recursion bound and handle the case where it's exhausted as a real, expected failure path in your application, not an edge case you can ignore.

**Performance and cost.** Every internal tool-call or retry cycle is a full additional model call — a task that resolves in three internal turns costs roughly three times the tokens and latency of a task that resolves in one. Well-scoped tools and well-constrained schemas (both covered in earlier modules) reduce how often the loop needs extra turns, which is a direct cost and latency lever, not just a correctness one.

**Observability.** The full message history returned alongside the final result is your best debugging asset — log it, or at minimum log the count and nature of internal tool calls and retries per run, so a slow or expensive agent call is traceable back to *why* it took multiple turns rather than being a mystery.

**Security.** The loop executes every tool the model requests, automatically, without a human in that loop by default — which means every argument covered in the Tools Fundamentals and `ToolRuntime` modules (validation constraints, authorization via `runtime.context`, not trusting model-supplied identity/tier data) matters more here, not less, because there's no manual checkpoint where a developer eyeballs the request before it runs.

**Testing.** Test the individual tools and the structured-output schema in isolation first (as covered in their own modules) — they're the actual units of business logic. Testing the full agent loop end to end is still valuable, but it's inherently less deterministic (the model can choose different tool-call sequences given the same input across runs), so treat those as integration-level tests, not the primary place you verify correctness.

**Trade-offs to be upfront about.** `create_agent` trades explicit control for automation — you don't get to inspect or intervene between individual tool calls the way you could with the manual loop, unless you reach for middleware (the next topic) to hook into specific points of that loop. For most real applications this trade is clearly worth it; for a case genuinely needing fine-grained control over every intermediate step, the manual pattern taught earlier remains available and sometimes the right choice.

---

## 8. Common Mistakes

- **Trying to combine `.bind_tools()` and `.with_structured_output()` on a raw model and expecting agent-like looping behavior.** This is the exact gap `create_agent` exists to close — a raw model call is single-shot, it does not sequence tool resolution and structured-output validation across turns on its own.
- **Assuming a single `agent.invoke()` call costs the same as a single raw model call.** It can involve several internal model invocations depending on how many tool calls or retries the task needs — budget and monitor accordingly, not as if it were a flat, predictable cost.
- **Not handling retry/recursion-limit exhaustion as a real failure case.** Assuming the loop will always eventually resolve cleanly, then being surprised in production when a genuinely malformed request or an unreliable tool causes it to hit its bound.
- **Skipping authorization checks inside tools because "the agent is handling it."** The agent loop automates *sequencing*, not judgment — every trust-boundary concern from the Tools and `ToolRuntime` modules still applies fully inside the loop.
- **Debugging a misbehaving agent by only looking at the final answer.** The full internal message history is available specifically because the intermediate steps are where the actual cause of a wrong final answer usually lives.

---

## 9. Instructor Insights

- The side-by-side comparison — same prompt, same tools, same schema, raw model vs. `create_agent` — is worth re-running yourself any time the difference feels abstract. Seeing a raw model genuinely fail to combine tool use and structured output, immediately followed by `create_agent` succeeding at the identical task, makes the distinction concrete in a way a description alone doesn't.
- This distinction was treated as one of the most important checkpoints in the entire course, explicitly framed as the kind of thing that comes up in interviews: being able to explain precisely *why* a raw model with tools and structured output bound doesn't behave like an agent is a stronger signal of real understanding than being able to recite what `create_agent` does.
- A tool call inside `create_agent`'s loop being modeled as a node in an underlying graph is worth remembering as a preview, not a distraction — it's the thread that connects directly into the LangGraph module, and it's why `create_agent`'s behavior, however automated it feels, is never actually opaque if you're willing to trace the graph.
- Don't reach for `create_agent` reflexively for every single model call — if a task genuinely never needs a tool and never needs structured output, a plain `model.invoke()` is still simpler and cheaper, and the agent loop's overhead buys you nothing in that case.

---

## 10. Official References

- LangChain `create_agent` guide: https://docs.langchain.com/oss/python/langchain/agents
- LangChain Structured Output guide (Provider/Tool Strategy, used within the agent loop): https://docs.langchain.com/oss/python/langchain/structured-output
- LangGraph concepts (the graph model underlying `create_agent`): https://docs.langchain.com/oss/python/langgraph/graph-api
- `create_agent` API reference: https://python.langchain.com/api_reference/langchain/agents/langchain.agents.create_agent.html
- LangChain GitHub repository: https://github.com/langchain-ai/langchain

---

## 11. Key Takeaways

- A raw model call is a single decision point — it can request a tool, or it can attempt structured output, but nothing at that level sequences "resolve tools, then validate a final structured answer" across multiple turns.
- `create_agent` is the harness that provides exactly that sequencing: it automatically executes requested tools, feeds results back in, and repeats until the model produces a final answer — resolving `response_format`, with its own validation-and-retry behavior, only on that final turn.
- This isn't new magic — it's the same request → execute → wrap → re-invoke loop taught manually in the tools module, automated and made to repeat as many times as the task genuinely needs.
- Every internal turn is a real model call — cost and latency scale with how many tool calls and retries a task actually needs, which makes well-scoped tools and well-constrained schemas a performance lever, not just a correctness one.
- The agent loop automates sequencing, not judgment — every security, validation, and authorization concern from the tools and structured-output modules still fully applies inside it.
