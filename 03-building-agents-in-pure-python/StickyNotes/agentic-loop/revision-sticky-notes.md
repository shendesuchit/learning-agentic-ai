# Agentic Loop — Revision Sticky Notes

> **Schema:** What can this tool do, and what input does it need?

> **Registry:** Which tools is this application actually willing to execute?

> **Selection:** The model requests a call. It does not execute one.

> **Execution:** Validate tool name and arguments before any side effect.

> **Observation:** Append the tool result with the matching `tool_call_id`.

> **Re-invoke:** The model needs the observation before it can answer properly.

> **Stop:** Final answer, error state, approval boundary, or exhausted budget.
