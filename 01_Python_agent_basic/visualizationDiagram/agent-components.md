# Visual: Components of the Agent

```mermaid
flowchart TB
    U[User] --> L[Agent loop]
    L --> M[Chat model]
    M --> D{Response type}
    D -->|Text| L
    D -->|Tool request| R[Tool registry]
    R --> F[Python function]
    F --> L
    L --> U
```

| Component | Project location | Job |
|---|---|---|
| Model | `DemoModel` / `OpenAICompatibleModel` | Select an action or answer |
| Schema | `TOOL_SCHEMAS` | Describe available actions |
| Registry | `TOOL_REGISTRY` | Resolve approved function names |
| Tool | `get_weather()` | Perform the action |
| Loop | `run_agent()` | Move messages between components |

