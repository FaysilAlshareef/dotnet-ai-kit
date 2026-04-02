---
alwaysApply: true
description: "Architecture profile for processor projects — hard constraints"
---

# Architecture Profile: Processor (Event Consumer)

## HARD CONSTRAINTS

### Hosted Service Lifecycle
- MUST implement `IHostedService` directly for session-based listeners — NEVER `BackgroundService`
- MUST use `BackgroundService` for batch processing with `AcceptNextSessionAsync` — NEVER `IHostedService`
- MUST create processors in the constructor — NEVER in `StartAsync`
- `StartAsync` MUST start both main and DLQ processors — NEVER skip DLQ
- `StopAsync` MUST use `CloseAsync` — NEVER `StopProcessingAsync`
- MUST always pair a `ServiceBusSessionProcessor` with a `ServiceBusProcessor` for DLQ

### Session Processor Configuration
- MUST set `AutoCompleteMessages = false` — NEVER auto-complete messages
- MUST set `PrefetchCount = 1` for reliable processing
- MUST set `MaxConcurrentCallsPerSession = 1` for strict per-aggregate ordering
- MUST set `MaxConcurrentSessions = 1000` for cross-aggregate parallelism
- MUST set `ReceiveMode = ServiceBusReceiveMode.PeekLock`
- DLQ processor MUST set `SubQueue = SubQueue.DeadLetter` and `MaxConcurrentCalls = 1`

### Event Routing
- ALWAYS use inline `HandleSubject` switch expression — NEVER create separate EventRouter class
- ALWAYS use typed `HandleAsync<TEventData>` for deserialization — NEVER generic deserialization
- MUST return `Task.FromResult(true)` for unknown event subjects — NEVER retry unknown events
- ALWAYS use `Encoding.UTF8.GetString(message.Body)` — NEVER `message.Body.ToString()`
- ALWAYS use `Newtonsoft.Json` (`JsonConvert.DeserializeObject`) — NEVER System.Text.Json
- MUST create DI scope per message and resolve `IMediator` from scope — NEVER reuse mediator

```csharp
// ANTI-PATTERN: separate EventRouter class
var router = new EventRouter(); // WRONG
router.Route(message); // WRONG — inline in listener

// CORRECT: inline switch in listener
return subject switch
{
    EventType.OrderCreated => HandleAsync<OrderCreatedData>(message),
    _ => Task.FromResult(true)
};
```

### Serilog Enrichment
- MUST push `PropertyEnricher` for EventType, SessionId, MessageId on every message
- ALWAYS use `LogContext.Push(enrichers)` with `using` — NEVER `LogContext.PushProperty`
- MUST use `LogCritical` for `ProcessErrorAsync` callbacks — NEVER lower severity

### gRPC Client Usage
- MUST use `AddGrpcClient<T>` with `(provider, configure)` callback — NEVER resolve URLs at registration time
- MUST use `ExternalServicesOptions` with `[Required, Url]` for all service URLs — NEVER hardcode
- MUST treat `RpcException` with `StatusCode.AlreadyExists` as idempotent success (return `true`)
- MUST use custom `RetryCallerService` with while loop for retries — NEVER Polly
- MUST re-throw unhandled exceptions to let listener abandon the message — NEVER swallow

### Batch Processing
- MUST use `SemaphoreSlim` to limit concurrent session processing — NEVER unbounded concurrency
- MUST deduplicate by `GroupBy(SourceId).Select(g => g.First())` before batch processing
- MUST complete all messages on success, abandon all on failure — NEVER partial completion
- DLQ handler MUST process messages individually — NEVER as batch
- MUST handle `ServiceBusException` with `ServiceTimeout` reason as normal (no sessions available)
- MUST dispose `ServiceBusSessionReceiver` in finally block

## Testing Requirements

- MUST test idempotent handling of `StatusCode.AlreadyExists` from gRPC calls
- MUST test batch deduplication by SourceId
- MUST test DLQ processing path separately from main processor path
- MUST test handler return values: `true` for complete, `false` for abandon

## Data Access

- ALWAYS create DI scope per message for `IUnitOfWork` resolution
- Typed ServiceBus client wrappers MUST be registered as singletons
- `RetryCallerService` MUST be registered as singleton
- ALWAYS use `IOptions<T>` pattern for configuration — NEVER read configuration directly
