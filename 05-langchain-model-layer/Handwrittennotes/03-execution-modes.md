# Calling modes

```text
invoke()              one complete answer
stream()              visible increments for a waiting user
batch()               many independent calls
batch_as_completed()  finished requests early — not tokens
```

Streaming reduces perceived waiting. Batching improves throughput only when work is independent and quota allows concurrency.
