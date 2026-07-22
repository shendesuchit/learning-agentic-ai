# Visualization Diagrams

The chapter diagrams are deliberately embedded beside the idea they explain. This page gathers the three diagrams that are most useful when revising the module.

## 1. Stored history is not model context

```mermaid
flowchart TD
    H["All stored messages"] --> S["Selection policy"]
    F["Trusted facts / summary"] --> S
    N["New question"] --> S
    S --> C["One request context"]
    C --> M["Model response"]
```

## 2. Context is a budget

```mermaid
flowchart TB
    T["Finite total capacity"] --> I["Instructions"]
    T --> H["History"]
    T --> D["Documents / tool results"]
    T --> Q["New question"]
    T --> O["Answer reserve"]
```

## 3. Freshness needs a source

```mermaid
flowchart LR
    U["User asks for current data"] --> A["Application"]
    A --> X["Authorised live source"]
    X --> A
    A --> L["LLM receives evidence"]
```

For the full teaching flow, start with the [module README](../../01-llm-fundamentals/README.md).
