# Sticky Notes — LLM Fundamentals

> 🟨 **Token:** a tokenizer-specific chunk, not a word.

> 🟩 **Stateless:** the model starts each inference without your private chat diary.

> 🟦 **Stored history is not context:** data affects an answer only after the application selects and supplies it.

> 🟪 **Context window:** finite working space for this request, including the desired answer.

> 🟧 **Context management:** select what is necessary, trusted, authorised, and relevant.

> 🟨 **Freshness:** conversation continuity does not make a model aware of today’s events.

> 🟩 **Web App vs API:** a product manages an experience; an API lets your software own the decisions.

## 30-second interview answer

“An LLM call is stateless: it only uses the context assembled for that request. A chatbot appears to remember because the application persists state and selects useful messages, summaries, or facts to include. That context is bounded in tokens, so engineers must manage it for reliability, cost, and relevance. Current or private information needs an authorised external source; it does not come automatically from conversation history.”
