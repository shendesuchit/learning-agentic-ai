# Tools — Fundamentals: `@tool`, Docstrings, and `args_schema`

*Module: learning-agentic-ai · Level: Beginner · Language: Python · Framework: LangChain*

---

## 1. Engineering Problem

Cinebot can now think in guaranteed shapes — structured output solved that. Ask it "book me 2 tickets for Inception tonight" and it reliably hands back a clean `BookingRequest` object with the right fields. But it still can't actually book anything. It has no way to check real showtimes against a real database, no way to reserve real seats, no way to touch anything outside its own context window. It can describe the right action perfectly and still be completely unable to take it.

Every non-trivial application you'll build with an LLM has this same gap. The model is good at language and reasoning; it has zero ability to query your database, call your payment API, or write to your filesystem. Something has to bridge "the model decided what should happen" and "the thing that's actually capable of making it happen" — and that something needs to be exposed to the model in a way it can understand and use correctly, without you hand-writing a parser for every possible way the model might phrase its intent.

That's what a tool is: a normal piece of Python functionality, described to the model precisely enough that the model can request it correctly.

---

## 2. Why This Concept Exists

Before a standard tool interface existed, every provider had its own bespoke way of describing "function calling" — different JSON schema conventions, different ways of registering a function's name and parameters, different response shapes for what the model sent back. If you wanted your booking function to work whether the underlying model was OpenAI, Anthropic, or something self-hosted, you were maintaining three separate integrations for the same Python function.

LangChain's `@tool` decorator exists to collapse that into one interface: write a normal Python function once, decorate it, and LangChain handles translating it into whatever schema format each provider's API actually expects. The engineering problem it solves isn't really "how do I call a function" — you already know how to do that — it's "how do I describe this function to a model, consistently, regardless of which model is on the other end, without writing that description by hand every time."

The reason the description matters as much as the function itself is worth sitting with. A model doesn't read your source code. It never sees your implementation. All it ever gets is the tool's name, its description, and its parameter schema — and it decides whether and how to call the tool based entirely on that description. A vague or missing description is functionally the same as a vague or missing API contract for a human developer trying to use your library without reading the source: they'll guess, and sometimes guess wrong.

---

## 3. How the Instructor Taught It

The instructor's framing, repeated multiple times across sessions and worth internalizing early: **tools are just glorified API calls, or glorified functions.** There's no special magic to a tool beyond a normal Python function wrapped so a model can understand and request it. He was deliberate about demystifying this early, because "tool" sounds like it should be more exotic than it is, and treating it as exotic gets in the way of just writing good functions.

He built the concept up in layers, using the ongoing Cinebot project as the vehicle throughout.

**The `@tool` decorator.** Take a plain function — `check_showtimes(movie_title: str) -> str`, `book_seats(...)` — and decorate it with `@tool` from `langchain_core.tools`. That's the entire mechanical step to make it usable by a model. Under the hood, LangChain reads the function's signature and turns it into something the model can be told about.

**The docstring is not documentation, it's the API contract the model reads.** This was one of his most emphasized points: whatever you write as the function's docstring becomes the tool's `description` field, and that description is what the model uses to decide *when* and *how* to call the tool. He was explicit that omitting a docstring isn't a style violation, it's a functional bug — without one, the tool has no meaningful description, and a model deciding whether "check showtimes" is the right tool for a user's question has nothing useful to go on. He showed this could be overridden explicitly too — `@tool("book_seats", description="...")` — for cases where you want the tool's public name or description to differ from the underlying function's name, for instance to avoid a naming collision with existing code, or to write a more model-friendly description than the function's own internal docstring would otherwise be.

**Type-hinted arguments become the parameter schema.** Every parameter on the decorated function, with its type hint, becomes part of what the model is told it needs to supply. `movie_title: str` tells the model "this tool needs a string called movie_title." He walked through `.args` on a decorated tool to show exactly what schema gets generated and sent to the model — a good habit for confirming your tool looks the way you expect before it's ever actually bound to a model.

**`args_schema` for stronger validation.** Plain type hints get you basic typing, but they don't get you real constraints — you can't express "seat count must be between 1 and 10" or "showtime must be one of these three formats" with a bare `int` or `str` annotation. For that, he introduced defining a Pydantic `BaseModel` describing the tool's inputs with real field constraints, and passing it to the decorator via `args_schema`. This gives you the same validation power over tool inputs that structured output gives you over the model's final answer — the model's tool call arguments get checked against real constraints, not just checked for the right Python type.

**Distinguishing tool sources.** He drew a three-way distinction that's easy to blur together: tools you write yourself (your `check_showtimes`, `book_seats`), inbuilt tools LangChain already ships (Tavily web search was his running example), and AI-native, provider-hosted tools — ChatGPT's own web search being the example — which run entirely on the provider's side and are explicitly outside your control as a developer; you can enable them, but you don't get to inspect or modify their implementation the way you do with your own or LangChain's inbuilt tools.

**Reserved argument names.** This was a specific, live-demonstrated gotcha: you cannot name a tool parameter `config` or `runtime`. LangChain reserves these names because it resolves them internally to inject execution context (covered properly under `ToolRuntime`) — if you try to use either as an ordinary parameter name, you don't get a clean syntax error, you get a runtime failure, which is a much more confusing thing to debug the first time you hit it. He deliberately triggered this live so students would recognize the error message if they ever saw it themselves rather than being stumped by it in isolation.

He also flagged, in passing, that MCP — Model Context Protocol — is, at the level this course cares about, essentially "a collection of tools, nothing else." Useful context for not over-mystifying MCP the first time it comes up, though he was clear this wasn't a deep dive into the protocol itself.

---

## 4. Deep Technical Explanation

A few things worth adding precision to, beyond what a live walkthrough covers.

**What `@tool` actually produces.** The decorator doesn't just wrap your function — it returns a `StructuredTool` (or `Tool`, depending on signature complexity) instance, an object with its own `.name`, `.description`, `.args_schema`, and a callable `.invoke()`/`.run()` interface, separate from your original Python function. This is why tools compose cleanly into lists you pass to `bind_tools()` or `create_agent(tools=[...])` — they're all instances of the same underlying LangChain abstraction regardless of whether they came from your code, a LangChain integration, or a third-party package.

**How the parameter schema is actually derived.** LangChain introspects your function's signature using Python's standard typing machinery, and where you haven't supplied an explicit `args_schema`, it auto-generates a Pydantic model behind the scenes from your type hints and default values. This is worth knowing because it means "not using `args_schema`" doesn't mean "no schema" — you always have one, it's just implicitly generated versus explicitly authored. `args_schema` doesn't turn on validation that was otherwise absent; it lets you author a *richer* one, with field-level constraints and better per-field descriptions than bare type hints can express.

**Docstring parsing specifics.** LangChain generally treats the full docstring as the tool description by default, but a well-formed docstring following a standard convention (Google-style or NumPy-style, with an `Args:` section) allows LangChain to also derive per-parameter descriptions automatically, rather than requiring you to duplicate that information into an explicit `args_schema`. In practice this means a genuinely well-documented function often needs no `args_schema` at all to produce a good tool description — reach for `args_schema` specifically when you need validation constraints, not just better documentation.

**Sync and async.** LangChain's tool interface supports both a sync function and an async (`async def`) version under the hood — if you decorate an `async def` function, the resulting tool exposes an async-invokable interface, which matters once you're running an agent inside an async web framework and don't want a blocking tool call stalling your event loop. This wasn't covered live in the transcripts, but it's a direct extension of the same `@tool` mechanism and worth knowing exists.

**Where "reserved names" actually comes from.** `config` and `runtime` aren't arbitrarily reserved — they correspond to injectable context LangChain's execution layer resolves automatically when a tool is invoked as part of an agent run (thread/run metadata, state, store access, and so on). Naming an ordinary parameter the same thing creates an ambiguity LangChain resolves in favor of the injected value, not your intended parameter, which is exactly why it manifests as a confusing runtime behavior rather than an import-time error.

---

## 5. Internal Execution Flow

**Defining a tool:**

1. You write a normal Python function with type-hinted parameters and a clear docstring.
2. You decorate it with `@tool` (optionally passing a name/description override, or an `args_schema`).
3. LangChain introspects the function signature and docstring, producing (or accepting your explicit) a Pydantic schema representing the tool's inputs.
4. The decorator returns a tool object — `.name`, `.description`, `.args_schema` all populated — wrapping your original function as the thing that actually executes when the tool is invoked.

**Registering it with a model:**

1. You pass a list of tool objects to `model.bind_tools([...])` or `create_agent(tools=[...])`.
2. Each tool's `.name`, `.description`, and JSON-Schema-converted `.args_schema` are serialized into the request sent to the provider, in whatever shape that specific provider's function-calling API expects.
3. The model now "knows" the tool exists, purely from that description — it has no access to your function's implementation.

**A single tool-call round trip:**

1. The model, given a user message and the available tool descriptions, decides a tool is relevant and produces a tool call: a name plus arguments it believes satisfy that tool's schema.
2. This arrives on the response as an `AIMessage.tool_calls` entry — a request, not an execution.
3. Something has to actually run the underlying function with those arguments — either you do this manually (as shown in the messages module) or `create_agent`'s loop does it automatically.
4. If `args_schema` (explicit or auto-derived) constraints aren't satisfied by the model's arguments, validation fails before your function body ever runs — the failure is caught and can be fed back to the model as corrective context, the same retry mechanism used for structured output validation.
5. On success, your function executes normally, and its return value gets wrapped into a `ToolMessage` and appended to the conversation, closing the loop.

---

## 6. Practical Engineering Example

A real internal tool for an engineering-support bot that needs to look up deployment status — with a validated schema, an overridden name to avoid clashing with an existing internal function, and a clear docstring the model can actually reason about.

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal

class DeploymentLookupInput(BaseModel):
    """Input schema for checking a service's deployment status."""
    service_name: str = Field(description="The exact internal service name, e.g. 'billing-api'")
    environment: Literal["staging", "production"] = Field(
        description="Which environment to check. Defaults to production if unspecified."
    )

# The underlying function might already be named `get_deployment_status` elsewhere in
# your codebase for a different purpose -- override the tool's public name to avoid
# any collision or ambiguity for the model.
@tool("check_service_deployment", args_schema=DeploymentLookupInput)
def check_deployment(service_name: str, environment: str) -> str:
    """Check whether a given internal service is currently deployed and healthy
    in the specified environment. Use this whenever an engineer asks about the
    live status of a service, not for historical deployment logs."""
    status = deployment_registry.lookup(service_name, environment)
    if status is None:
        return f"No deployment record found for {service_name} in {environment}."
    return f"{service_name} in {environment}: {status.state}, last deployed {status.deployed_at}."

print(check_deployment.name)          # check_service_deployment
print(check_deployment.description)   # the full docstring above
print(check_deployment.args)          # the generated/attached parameter schema

# Wiring it into an agent alongside other tools
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-5-mini",
    tools=[check_deployment],
    system_prompt="You help engineers check the status of internal services.",
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Is billing-api healthy in prod right now?"}]
})
print(result["messages"][-1].content)
```

Notice the docstring is written the way you'd write a good comment for a teammate deciding whether to call this function — not marketing copy, just precise conditions for when it applies. That's exactly the audience it's for; the model is the "teammate" reading it.

---

## 7. Production Perspective

**Reliability.** A tool's description is effectively an API contract with a non-deterministic caller. Vague descriptions produce a model that sometimes picks the right tool, sometimes doesn't, and the failure mode is silent — the model just calls the wrong thing confidently. Treat tool docstrings with the same rigor you'd apply to a public API's documentation, because in a real sense, that's exactly what it is.

**Scalability and tool-set design.** Every tool you register costs context — its full schema gets sent with every request that model sees, whether or not it's relevant to the current turn. A handful of well-described tools is far more reliable than a large, loosely curated set, both for cost and for the model's ability to pick correctly. If you find yourself past 5–7 tools on one agent, that's usually a design signal to split into a more focused sub-agent rather than growing one agent's tool list indefinitely (a theme the instructor returns to explicitly in the agent-scaling module).

**Security.** A tool is a real capability, not a suggestion — if you expose `book_seats` or `issue_refund` as a tool, the model calling it is functionally equivalent to your code calling it, minus human review in the loop. Validate arguments with `args_schema` constraints as a first line of defense (amount limits, allowed categories), but don't treat schema validation as your only safety boundary — apply the same authorization and business-rule checks you'd apply to any other untrusted caller of that function, because that's effectively what a model is.

**Maintainability.** Keeping the tool's public name and description close to the function definition (rather than overriding them somewhere far away in configuration) keeps the "contract" and the "implementation" from drifting apart over time — a classic docs-vs-code rot problem, just with a model as the reader instead of a human.

**Debugging.** `.args` on a tool object is your fastest sanity check when a model is calling a tool with unexpected arguments — print it before assuming the model is "confused"; often the schema being sent doesn't say what you think it says, especially with auto-derived schemas from ambiguous type hints.

**Testing.** Because a decorated tool remains directly callable (`check_deployment.invoke({...})` or the underlying function itself), you can and should unit test the tool's actual logic completely independently of any model — the model-facing description and the function's correctness are two separate concerns, test them separately.

---

## 8. Common Mistakes

- **Skipping the docstring, or writing something generic like `"""Does the lookup."""`.** The model has nothing else to go on; this is the single most common cause of a tool being picked incorrectly or ignored entirely when it should have been used.
- **Naming a parameter `config` or `runtime`.** Produces a confusing runtime error instead of an obvious one — worth recognizing this specific gotcha the first time it happens instead of losing time to it.
- **Relying on bare type hints when you actually need constraints.** `seats: int` doesn't stop the model from requesting 500 seats; if there's a real-world bound, express it via `args_schema` with a Pydantic `Field`, not a comment or a docstring aside hoping the model respects it.
- **Assuming the model executes the tool.** Same checkpoint as the messages module: the model only ever requests a tool call. Somewhere — your code, or `create_agent`'s loop — has to actually run it.
- **Registering too many tools on one agent "just in case."** Every tool is context overhead and a chance for the model to pick wrong; unused, loosely relevant tools hurt more than they help.
- **Treating provider-hosted, AI-native tools the same as your own.** You can't inspect or modify what ChatGPT's own web search actually does internally — don't build logic that assumes behavior you can't verify or control.

---

## 9. Instructor Insights

- "Tools are just glorified functions" is worth repeating to yourself any time a tool feels more complicated than it should — the complexity almost always lives in the description quality and the schema, not in some hidden mechanism.
- Always inspect `.args` on a tool before wiring it into an agent — it's the fastest way to catch a schema that doesn't say what you think it says, before a model ever gets confused by it.
- The `config`/`runtime` reserved-name error is common enough, and confusing enough the first time, that it's worth deliberately triggering once yourself so you recognize it instantly later rather than debugging it cold in a real project.
- MCP, at a practical level, is "a collection of tools, nothing else" — useful for not over-mystifying it the first time a project brings it up, though it deserves its own deeper treatment beyond that framing.
- Overriding a tool's name/description via the decorator's arguments isn't a rare escape hatch — reach for it any time your function's actual name would collide with existing code, or when the function's internal docstring isn't written with a model-reader in mind.

---

## 10. Official References

- LangChain Tools concept guide: https://docs.langchain.com/oss/python/langchain/tools
- `@tool` decorator API reference: https://python.langchain.com/api_reference/core/tools/langchain_core.tools.convert.tool.html
- `StructuredTool` API reference: https://python.langchain.com/api_reference/core/tools/langchain_core.tools.structured.StructuredTool.html
- LangChain `create_agent` and tool binding: https://docs.langchain.com/oss/python/langchain/agents
- Pydantic `Field` and `BaseModel`: https://docs.pydantic.dev/latest/concepts/models/
- LangChain GitHub repository: https://github.com/langchain-ai/langchain

---

## 11. Key Takeaways

- A tool is a normal Python function plus a description precise enough for a model — which never sees your implementation — to decide correctly when and how to call it.
- The docstring is not documentation for humans, it's the contract the model actually reads. Treat it with the same rigor as a public API description, because functionally, that's what it is.
- Type hints give you a basic auto-generated schema for free; `args_schema` with Pydantic gives you real constraints (`Field(ge=..., le=...)`, `Literal`) when "the right type" isn't enough to guarantee "the right value."
- The model only ever requests a tool call — it never executes anything. That execution step is either your code doing it manually, or `create_agent`'s loop doing it for you.
- `config` and `runtime` are reserved parameter names — using them yourself produces a confusing runtime failure, not a clean error, because LangChain resolves them to injected execution context.
- More tools isn't automatically better. Every tool costs context and adds a chance for misselection — a small, well-described, well-scoped tool set beats a large loosely curated one, both for reliability and for cost.
