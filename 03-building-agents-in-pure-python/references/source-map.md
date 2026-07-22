# Source Map: Agentic Loop

## Tool schema and structured arguments

| Source | Evidence carried into this repository |
| --- | --- |
| `12 July LangChain - 2(1).txt` | Weather tool schema, descriptions, named tools, structured arguments, Pydantic mentioned as a schema option. |
| `11 July LangChain - 1(1).txt` | Structured output and Pydantic as prerequisite context. |
| `06 - 12 July - Introduction to LangChain(1).md` | Framework-generated schemas through plain functions and `@tool`. |

## Tool selection and execution

| Source | Evidence carried into this repository |
| --- | --- |
| `12 July LangChain - 2(1).txt` | Model chooses a normal response or tool request; named-tool registry; JSON arguments; application executes the matching function. |
| `06 - 12 July - Introduction to LangChain(1).md` | Agent, rather than the user, performs the tool call. |

## Agentic loop

| Source | Evidence carried into this repository |
| --- | --- |
| `12 July LangChain - 2(1).txt` | `run_agent(messages, max_turns=4)`, append tool result, return final answer only when no tool calls remain. |
| `06 - 12 July - Introduction to LangChain(1).md` | End-to-end sequence: model → tool → appended result → model → final response. |

## Calling the model again

| Source | Evidence carried into this repository |
| --- | --- |
| `12 July LangChain - 2(1).txt` | Tool result must be appended and used after execution; result is associated with the original call ID. |
| `06 - 12 July - Introduction to LangChain(1).md` | LangChain message anatomy: HumanMessage → AIMessage tool call → ToolMessage → final AIMessage. |
| `07 - 18 July - LangChain - 1.md` | Later message/model context and tool-calling capability caveat. |

## Loop iteration and termination

| Source | Evidence carried into this repository |
| --- | --- |
| `12 July LangChain - 2(1).txt` | Multiple tool calls are possible; maximum turns prevents an unbounded loop; no final answer when the maximum is reached. |
| `06 - 12 July - Introduction to LangChain(1).md` | A bounded `max_turns` loop and the LangChain automation mapping. |

## Supporting sources

- `18 July Lanchain - 2 - Concepts.txt` supports the later framework context around model capabilities, messages, and tool calling.
- `Pasted markdown(4).md` provides the repository's narrative, source-traceability, and technical-correction standards.

## Engineering enrichment added deliberately

The source demonstrates the raw mechanism. The repository additionally introduces allow-lists, argument validation, controlled tool errors, call correlation, timeouts, approval boundaries, and cost/time budgets. These are direct safeguards for implementing the demonstrated mechanism safely; they are not presented as transcript claims.
