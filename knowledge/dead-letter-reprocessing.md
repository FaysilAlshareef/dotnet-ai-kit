# Dead Letter Queue Reprocessing

Paired DLQ processor pattern for automatic dead letter reprocessing in processor microservices. Every listener has a paired `ServiceBusProcessor` targeting `SubQueue.DeadLetter` that runs alongside the main `ServiceBusSessionProcessor`.

---

## Overview

The production pattern is NOT a separate DLQ monitoring service. Instead, each listener class creates a paired DLQ processor in its constructor that automatically reprocesses dead-lettered messages using the same routing logic as the main processor.

```
┌───────────────────────────┐
│      OrderListener        │
│  (IHostedService)         │
│                           │
│  ┌─────────────────────┐  │
│  │ ServiceBusSess ionP  │  │  Main processor
│  │ rocessor             │──│──> ProcessMessageAsync(ProcessSessionMessageEventArgs)
│  │ (session-enabled)    │  │       -> HandleSubject() -> HandleAsync<T>()
│  └─────────────────────┘  │       -> CompleteMessage / AbandonMessage
│                           │
│  ┌─────────────────────┐  │
│  │ ServiceBusProcessor  │  │  DLQ processor (paired)
│  │ (SubQueue.DeadLetter)│──│──> ProcessMessageAsync(ProcessMessageEventArgs)
│  │ (no sessions)        │  │       -> HandleSubject() -> HandleAsync<T>()
│  └─────────────────────┘  │       -> CompleteMessage / AbandonMessage
│                           │
└───────────────────────────┘
```

---

## Paired Processor Pattern

### Constructor: Create Both Processors

```csharp
public class OrderListener : IHostedService
{
    private readonly ServiceBusSessionProcessor _processor;
    private readonly ServiceBusProcessor _deadLetterProcessor;

    public OrderListener(
        IServiceProvider serviceProvider,
        ILogger<OrderListener> logger,
        IOptions<ServiceBusOptions> options,
        OrderServiceBus orderServiceBus)
    {
        var serviceBusOptions = options.Value;

        // Main session processor
        _processor = orderServiceBus.Client.CreateSessionProcessor(
            serviceBusOptions.OrderCommandTopic,
            serviceBusOptions.Subscription,
            new ServiceBusSessionProcessorOptions()
            {
                PrefetchCount = 1,
                MaxConcurrentCallsPerSession = 1,
                MaxConcurrentSessions = 1000,
                AutoCompleteMessages = false,
                SessionIdleTimeout = TimeSpan.FromMinutes(1),
                MaxAutoLockRenewalDuration = TimeSpan.FromMinutes(5),
            });

        _processor.ProcessMessageAsync += Processor_ProcessMessageAsync;
        _processor.ProcessErrorAsync += Processor_ProcessErrorAsync;

        // Paired DLQ processor
        _deadLetterProcessor = orderServiceBus.Client.CreateProcessor(
            serviceBusOptions.OrderCommandTopic,
            serviceBusOptions.Subscription,
            new ServiceBusProcessorOptions()
            {
                PrefetchCount = 1,
                AutoCompleteMessages = false,
                MaxConcurrentCalls = 1,
                SubQueue = SubQueue.DeadLetter,
            });

        _deadLetterProcessor.ProcessMessageAsync += DeadLetterProcessor_ProcessMessageAsync;
        _deadLetterProcessor.ProcessErrorAsync += DeadLetterProcessor_ProcessErrorAsync;
    }
}
```

### Key difference: `CreateProcessor` vs `CreateSessionProcessor`

- Main processor: `CreateSessionProcessor()` -- uses `ServiceBusSessionProcessorOptions`, handler receives `ProcessSessionMessageEventArgs`
- DLQ processor: `CreateProcessor()` -- uses `ServiceBusProcessorOptions` with `SubQueue = SubQueue.DeadLetter`, handler receives `ProcessMessageEventArgs`
- DLQ processor does NOT use sessions -- it processes individual dead-lettered messages

---

## DLQ Handler: Same Routing Logic

### For IHostedService Listeners (Topic-Based)

The DLQ handler calls the same `HandleSubject()` method as the main processor:

```csharp
// Main processor handler
private async Task Processor_ProcessMessageAsync(ProcessSessionMessageEventArgs arg)
{
    Task<bool> isHandledTask = HandleSubject(arg.Message.Subject, arg.Message);
    var isHandled = await isHandledTask;

    if (isHandled)
        await arg.CompleteMessageAsync(arg.Message);
    else
        await arg.AbandonMessageAsync(arg.Message);
}

// DLQ processor handler -- same routing, different EventArgs type
private async Task DeadLetterProcessor_ProcessMessageAsync(ProcessMessageEventArgs arg)
{
    Task<bool> isHandledTask = HandleSubject(arg.Message.Subject, arg.Message);
    var isHandled = await isHandledTask;

    if (isHandled)
        await arg.CompleteMessageAsync(arg.Message);
    else
        await arg.AbandonMessageAsync(arg.Message);
}
```

Both handlers share `HandleSubject()` because it takes `ServiceBusReceivedMessage` (the base type), which is available from both `ProcessSessionMessageEventArgs.Message` and `ProcessMessageEventArgs.Message`.

### For BackgroundService Listeners (Queue-Based Batch)

The DLQ handler processes messages individually (not as a batch):

```csharp
private async Task DeadLetterProcessor_ProcessMessageAsync(ProcessMessageEventArgs arg)
{
    // Skip non-matching subjects
    if (arg.Message.Subject != EventType.AccountItemChanged)
    {
        await arg.CompleteMessageAsync(arg.Message);
        return;
    }

    var json = Encoding.UTF8.GetString(arg.Message.Body);
    var body = JsonConvert.DeserializeObject<ItemChanged>(json);

    if (body == null || body.Quantity < 1)
    {
        await arg.CompleteMessageAsync(arg.Message);
        return;
    }

    // Process individually (not batched) via MediatR
    using var scope = _provider.CreateScope();
    var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();

    var success = await mediator.Send(new ItemChanged
    {
        AccountId = body.AccountId,
        SourceId = body.SourceId,
        SourceType = body.SourceType,
        Quantity = body.Quantity
    }, arg.CancellationToken);

    if (success)
        await arg.CompleteMessageAsync(arg.Message);
    else
        await arg.AbandonMessageAsync(arg.Message);
}
```

---

## CompleteMessage / AbandonMessage Semantics

| Action | When | Effect |
|--------|------|--------|
| `CompleteMessageAsync` | Handler returns `true` | Message removed from queue permanently |
| `AbandonMessageAsync` | Handler returns `false` | Message returned to queue for retry (delivery count increments) |
| (Automatic DLQ) | MaxDeliveryCount exceeded | Service Bus moves message to DLQ automatically |

### In the DLQ context:

- **CompleteMessage on DLQ**: Removes the dead-lettered message permanently (reprocessing succeeded or message should be discarded)
- **AbandonMessage on DLQ**: Returns message to DLQ for another attempt (delivery count increments; will eventually be permanently dead-lettered again)

---

## Error Handlers

```csharp
private Task Processor_ProcessErrorAsync(ProcessErrorEventArgs arg)
{
    _logger.LogCritical(arg.Exception,
        "OrderListener => Processor_ProcessErrorAsync " +
        "Message handler encountered an exception," +
        " Error Source:{ErrorSource}," +
        " Entity Path:{EntityPath}",
        arg.ErrorSource.ToString(),
        arg.EntityPath);

    return Task.CompletedTask;
}

private Task DeadLetterProcessor_ProcessErrorAsync(ProcessErrorEventArgs arg)
{
    _logger.LogCritical(arg.Exception,
        "DeadLetter Message handler encountered an exception," +
        " Error Source:{ErrorSource}," +
        " Entity Path:{EntityPath}",
        arg.ErrorSource.ToString(),
        arg.EntityPath);

    return Task.CompletedTask;
}
```

---

## Lifecycle: Start and Stop Both Processors

### IHostedService Listeners

```csharp
public Task StartAsync(CancellationToken cancellationToken)
{
    _processor.StartProcessingAsync(cancellationToken);
    _deadLetterProcessor.StartProcessingAsync(cancellationToken);

    return Task.CompletedTask;
}

public Task StopAsync(CancellationToken cancellationToken)
{
    _processor.CloseAsync(cancellationToken);
    _deadLetterProcessor.CloseAsync(cancellationToken);

    return Task.CompletedTask;
}
```

### BackgroundService Listeners

```csharp
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    // Start DLQ processor first
    await _deadLetterProcessor.StartProcessingAsync(stoppingToken);

    // Then run the main processing loop
    var semaphore = new SemaphoreSlim(_maxConcurrentSessions);
    while (!stoppingToken.IsCancellationRequested)
    {
        // ... AcceptNextSessionAsync pattern
    }
}

public override async Task StopAsync(CancellationToken cancellationToken)
{
    await _deadLetterProcessor.CloseAsync(cancellationToken);
    await base.StopAsync(cancellationToken);
}
```

---

## DLQ Processor Configuration

For topic/subscription-based listeners:

```csharp
_deadLetterProcessor = serviceBus.Client.CreateProcessor(
    serviceBusOptions.TopicName,
    serviceBusOptions.Subscription,
    new ServiceBusProcessorOptions()
    {
        PrefetchCount = 1,
        AutoCompleteMessages = false,
        MaxConcurrentCalls = 1,
        SubQueue = SubQueue.DeadLetter,
    });
```

For queue-based listeners:

```csharp
_deadLetterProcessor = _serviceBusClient.CreateProcessor(
    _queueName,
    new ServiceBusProcessorOptions()
    {
        PrefetchCount = 1,
        AutoCompleteMessages = false,
        MaxConcurrentCalls = 1,
        SubQueue = SubQueue.DeadLetter,
    });
```

Note: Queue-based `CreateProcessor` takes only the queue name (no subscription parameter).

---

## When Messages Enter the DLQ

1. **MaxDeliveryCount exceeded** -- Message was abandoned too many times by the main processor
2. **TTL expired** -- Message exceeded its time-to-live
3. **Session errors** -- Session processor encountered unrecoverable errors

The paired DLQ processor automatically picks up these messages and attempts to reprocess them using the same handler logic. If the underlying issue (e.g., downstream service outage) has been resolved, the message will be successfully processed and completed.

---

## Related Documents

- `knowledge/service-bus-patterns.md` -- Service Bus configuration and session processor setup
- `skills/microservice/processor/hosted-service/SKILL.md` -- IHostedService listener with paired DLQ
- `skills/microservice/processor/batch-processing/SKILL.md` -- BackgroundService batch with DLQ
