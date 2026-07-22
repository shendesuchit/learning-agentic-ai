# Sticky Notes — LangChain Fundamentals

> 🟨 **Framework ≠ model**  
> LangChain is the harness. The selected LLM provides language capability.

> 🟩 **`create_agent()` hides repetition, not concepts**  
> You still need to understand the model → tool → model loop.

> 🟦 **A provider key is not a LangChain key**  
> Your chosen integration decides whether credentials are needed and which environment variable it reads.

> 🟧 **Portability is partial**  
> Same interface does not mean identical tool calling, limits, cost, latency, or output quality.

> 🟪 **Memory is a design choice**  
> Persisted conversation requires explicit storage/checkpointing and a stable thread ID.

> 🟥 **LangSmith is not an agent runtime**  
> Use it for tracing, testing, evaluation, and operational visibility.

> 🟫 **Choose the layer by control requirements**  
> Standard loop → LangChain. Explicit paths/approval/durability → consider LangGraph.
