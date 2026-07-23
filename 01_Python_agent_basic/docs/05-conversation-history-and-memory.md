# 5. Conversation History and Memory

## Models are request-bound

The model sees only the information included in the current request. In this project, the
`messages` list provides that information.

At the beginning:

```text
system message
user message
```

After the model requests a tool:

```text
system message
user message
assistant tool-call message
```

After Python executes the tool:

```text
system message
user message
assistant tool-call message
tool result message
```

The final model call receives the entire sequence. That is how it knows both the original
question and the tool result.

## A precise use of the word “memory”

The local `messages` list is temporary conversation state. The model itself did not save the
conversation, and this program does not preserve it after the process ends.

This distinction matters:

> Sending earlier messages again creates conversational continuity; it does not make the
> underlying model stateful.

Study the [message-history visual](../visualizationDiagram/message-history-growth.md).

Next: [Complete code walkthrough](06-complete-code-walkthrough.md).

