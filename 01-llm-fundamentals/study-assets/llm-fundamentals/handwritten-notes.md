# Handwritten Notes — LLM Fundamentals

Use this as a compact notebook page. Copy it by hand rather than trying to memorise every sentence.

---

## 1. The core picture

```text
User question
     ↓
Application chooses context
     ↓
LLM sees one finite request
     ↓
Application stores the useful result
```

**LLM ≠ complete application**

The LLM gives an answer from the current context. The application owns data, security, history, policies, and live connections.

---

## 2. Tokens

- Token = model-specific text chunk
- Not equal to word / character
- Input tokens = what we send
- Output tokens = what model generates
- Tokens affect: capacity + often price + latency

**Golden line:** measure with the real tokenizer / API usage, not a fixed rule of thumb.

---

## 3. Statelessness

```text
Call 1: “My name is Dhyey” → answer
Call 2: “What is my name?” → no reliable memory
```

Model does not retain per-user chat state across isolated calls.

But the **application can store it**.

---

## 4. Three things not to mix up

| Stored history | Model context | Memory |
| --- | --- | --- |
| Everything app saved | What model receives now | Strategy for retaining/retrieving useful info |

Stored ≠ sent. Sent ≠ remembered forever.

---

## 5. Context window

```text
Total capacity
 = instructions
 + selected history
 + documents/tool results
 + new question
 + output reserve
```

The model only works with what fits **now**.

---

## 6. Long-chat policy

Do not blindly send everything.

- Keep recent turns for flow
- Summarise old narrative
- Retrieve relevant facts
- Keep known fields as structured state
- Evaluate quality, cost, latency, and privacy

---

## 7. Knowledge cutoff

Training knowledge is not a live feed.

For today’s price / latest policy / private order status → application needs an authorised source, then gives evidence to the model.

**History answers:** “What did we say?”  
**Live source answers:** “What is true now?”
