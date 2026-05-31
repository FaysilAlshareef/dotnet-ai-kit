---
name: server-sent-events
description: "Builds streaming Minimal API endpoints with TypedResults.ServerSentEvents() and SseItem<T>, pushing a one-way event stream to clients over the text/event-stream protocol. Use when streaming incremental updates (notifications, token-by-token AI output, live metrics) to a browser EventSource. Do NOT use for bidirectional or hub-style realtime (use signalr-realtime) or for standard request/response endpoints (use minimal-api-patterns)."
metadata:
  category: "api"
  agent: "api-designer"
---
# Server-Sent Events (SSE)

SSE is a one-way, long-lived HTTP stream (`text/event-stream`) — ideal for server push where the client only listens. On .NET 10, `TypedResults.ServerSentEvents()` returns an `IAsyncEnumerable<SseItem<T>>` and the framework handles framing, content type, and flushing.

## Conventions
- Return `TypedResults.ServerSentEvents(stream)` where `stream` is an `IAsyncEnumerable<SseItem<T>>` (or `IAsyncEnumerable<T>`); the runtime serializes each item and writes the `data:` frame.
- Always accept and honour the endpoint `CancellationToken` — it fires when the client disconnects, so the producer loop must stop and release resources.
- Set `SseItem<T>.EventType` to tag event kinds the client can filter on with `addEventListener("type", ...)`; set `EventId` for resumable streams (clients send `Last-Event-ID`).
- Use `[EnumeratorCancellation]` on the `CancellationToken` parameter of any `async IAsyncEnumerable` producer so cancellation propagates.
- Keep payloads small and frequent; for heartbeats, periodically yield a comment/keep-alive item so proxies don't drop idle connections.
- SSE is server→client only. If the client must also send messages, use a WebSocket/SignalR hub instead.

## Example
```csharp
app.MapGet("/orders/{id:guid}/events", (Guid id, CancellationToken ct) =>
    TypedResults.ServerSentEvents(StreamStatus(id, ct), eventType: "order-status"));

static async IAsyncEnumerable<SseItem<OrderStatusDto>> StreamStatus(
    Guid id, [EnumeratorCancellation] CancellationToken ct)
{
    var seq = 0;
    while (!ct.IsCancellationRequested)
    {
        var status = await ReadCurrentStatusAsync(id, ct);
        yield return new SseItem<OrderStatusDto>(status)
        {
            EventId = (++seq).ToString(),   // enables client resume
        };
        await Task.Delay(TimeSpan.FromSeconds(2), ct);
    }
}
```
```js
// Browser client
const es = new EventSource("/orders/123/events");
es.addEventListener("order-status", e => console.log(JSON.parse(e.data)));
```

## Anti-Patterns
- Ignoring the `CancellationToken`, leaking a producer loop after the client disconnects.
- Using SSE for two-way communication (it cannot carry client→server messages).
- Returning a buffered list instead of streaming an `IAsyncEnumerable` (defeats the point).
- Omitting `EventId` when clients need to resume after a dropped connection.

## References
- https://learn.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis/responses#server-sent-events
