# Binding ≠ execution

The model can request `get_weather(city="Pune")`. Your application must still allowlist the tool, validate `city`, enforce permissions, run it safely, and return a `ToolMessage` with the same call ID.
