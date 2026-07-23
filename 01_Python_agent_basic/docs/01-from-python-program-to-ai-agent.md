# 1. From a Python Program to an AI Agent

## The problem

A normal Python program follows decisions written by the developer:

```python
if user_wants_weather:
    get_weather(city)
```

This is useful, but the developer must predict every wording and route. A user may write
“Should I carry an umbrella in Pune?” without using the word `weather`.

An agent introduces a model as a decision-making component. The model reads the request and
decides whether the program should answer directly or perform an action.

## A simple mental model

Imagine a hotel receptionist:

- The **model** understands what the guest wants.
- The **tool list** describes services the hotel provides.
- The **Python functions** actually perform those services.
- The **agent loop** carries information between them.

The receptionist does not personally cook food. In the same way, a model does not execute
`get_weather()`. It requests the action; Python executes it.

## Model, chatbot, and agent

| System | Can understand language? | Keeps supplied messages? | Can take coded actions? |
|---|---:|---:|---:|
| Model call | Yes | Only within the request | No |
| Chatbot application | Yes | Usually | Not necessarily |
| Tool-calling agent | Yes | Usually | Yes |

An agent is not simply “a smarter chatbot.” It is an application architecture that connects
model decisions to executable capabilities.

## Connection to this project

Open [`main.py`](../main.py) and find these four pieces:

1. `get_weather()` — the action
2. `TOOL_SCHEMAS` — the action description
3. `DemoModel` or `OpenAICompatibleModel` — the decision maker
4. `run_agent()` — the coordinator

Next: [Understanding tools](02-understanding-tools.md).

