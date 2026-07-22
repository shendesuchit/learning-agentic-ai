# Why a Smart Model Still Cannot Act

An LLM can explain a concept, draft an email, or classify text. Yet asking it, “What is the current weather in Pune?” exposes a boundary: a model has no built-in access to a live weather service.

That is not a flaw. A model is a component that generates an output from the context supplied for one request. The surrounding application decides what context it gets and what happens next.

## The progression

| System | What the application adds | What it can do |
|---|---|---|
| LLM call | A prompt | Generate an answer from the supplied context |
| Chatbot | Conversation history | Respond with short-term conversational continuity |
| Agent | History, tools, and a control loop | Request approved external actions and use their results |

A chatbot is not automatically a persistent agent. A Python list called `history` vanishes when the process stops unless the application saves it somewhere. Likewise, an LLM given a tool schema has only learned that a capability exists; it has not gained permission or ability to execute code.

## The four parts of a beginner-friendly agent

1. **Brain** — the model that returns text or a structured request.
2. **Memory** — the state the application selects and sends back to the model.
3. **Tools** — approved Python functions or external APIs that do work outside the model.
4. **Harness** — the application logic that coordinates all three and enforces rules.

Consider a capable consultant in a locked office. They can analyse the information on their desk, but cannot query payroll, look up today’s weather, or send money. The agent harness is the controlled operations desk around that consultant.

## A more precise definition

An agent is **not** simply “an LLM that reasons.” It is an application that repeatedly:

1. builds a model request from its current state;
2. accepts either a direct answer or an action request;
3. validates and executes only allowed actions;
4. supplies the result back as evidence; and
5. stops under explicit limits.

This definition matters because it places security, cost, retries, and execution authority in the correct layer: the application, not the model.

## What comes next

The phrase “LLM as the brain” is useful, but it can hide a critical fact: a brain does not execute Python. The next chapter makes the model–application boundary explicit.

**Source basis:** S1, S3. See the [source map](references/source-map.md).
