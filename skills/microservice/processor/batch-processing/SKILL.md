---
name: batch-processing
description: >
  Batch event processing with BackgroundService, SemaphoreSlim concurrency control,
  AcceptNextSessionAsync, ReceiveMessagesAsync batching, deduplication by SourceId,
  and batch MediatR request. Separate from IHostedService session processor pattern.
  Trigger: batch processing, semaphore, deduplication, BackgroundService, queue listener.
metadata:
  category: microservice/processor
  agent: processor-architect
---

# Batch Processing — BackgroundService with Session Batching

## Core Principles

- Batch processing uses `BackgroundService` (NOT IHostedService with ServiceBusSessionProcessor)
- `SemaphoreSlim` controls maximum concurrent session processing
- `AcceptNextSessionAsync()` manually accepts sessions one at a time
- `ReceiveMessagesAsync(maxMessages: batchSize, maxWaitTime)` for batch receive
- Deduplication: `GroupBy(SourceId).Select(g => g.First())` to keep first occurrence
- Batch request object sent to `IMediator.Send()` for aggregated processing
- Complete all messages on success, abandon all on failure
- Paired DLQ processor still present for dead letter handling

## Key Patterns

### BackgroundService Batch Listener

```csharp
namespace {Company}.{Domain}.Processor.Infra.ServiceBus.Listeners;

public class ItemQueueListener : BackgroundService
{
    private readonly ILogger<ItemQueueListener> _logger;
    private readonly IServiceProvider _provider;
    private readonly ServiceBusClient _serviceBusClient;
    private readonly string _queueName;
    private readonly int _batchSize;
    private readonly int _maxConcurrentSessions;
    private readonly ServiceBusProcessor _deadLetterProcessor;

    public ItemQueueListener(
        IServiceProvider serviceProvider,
        ILogger<ItemQueueListener> logger,
        IOptions<ServiceBusOptions> options,
        ItemQueueListenerServiceBus itemServiceBus)
    {
        var serviceBusOptions = options.Value;
        _logger = logger;
        _provider = serviceProvider;
        _serviceBusClient = itemServiceBus.Client;
        _queueName = serviceBusOptions.ItemQueue;
        _batchSize = serviceBusOptions.ItemQueueBatchSize;
        _maxConcurrentSessions = serviceBusOptions.ItemQueueMaxConcurrentSessions;

        // Paired DLQ processor (same pattern as IHostedService listeners)
        _deadLetterProcessor = _serviceBusClient.CreateProcessor(
            _queueName,
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

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await _deadLetterProcessor.StartProcessingAsync(stoppingToken);

        var semaphore = new SemaphoreSlim(_maxConcurrentSessions);

        while (!stoppingToken.IsCancellationRequested)
        {
            await semaphore.WaitAsync(stoppingToken);

            _ = Task.Run(async () =>
            {
                try
                {
                    await AcceptAndProcessSessionAsync(stoppingToken);
                }
                catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
                {
                    // Expected during shutdown
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error accepting session from queue");
                }
                finally
                {
                    semaphore.Release();
                }
            }, stoppingToken);
        }
    }

    // ... (see below for session processing)

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        await _deadLetterProcessor.CloseAsync(cancellationToken);
        await base.StopAsync(cancellationToken);
    }
}
```

### AcceptNextSessionAsync Pattern

```csharp
private async Task AcceptAndProcessSessionAsync(CancellationToken stoppingToken)
{
    ServiceBusSessionReceiver? receiver = null;
    try
    {
        receiver = await _serviceBusClient.AcceptNextSessionAsync(
            _queueName,
            new ServiceBusSessionReceiverOptions
            {
                PrefetchCount = _batchSize,
                ReceiveMode = ServiceBusReceiveMode.PeekLock
            },
            stoppingToken);

        await ProcessSessionAsync(receiver, stoppingToken);
    }
    catch (ServiceBusException ex) when (ex.Reason == ServiceBusFailureReason.ServiceTimeout)
    {
        // No sessions available -- this is normal
    }
    finally
    {
        if (receiver != null)
            await receiver.DisposeAsync();
    }
}
```

### Session Processing with Deduplication and Batch Request

```csharp
private async Task ProcessSessionAsync(
    ServiceBusSessionReceiver receiver, CancellationToken stoppingToken)
{
    while (!stoppingToken.IsCancellationRequested)
    {
        var messages = await receiver.ReceiveMessagesAsync(
            maxMessages: _batchSize,
            maxWaitTime: TimeSpan.FromSeconds(5),
            cancellationToken: stoppingToken);

        if (messages == null || messages.Count == 0)
            break;

        var sessionId = receiver.SessionId;
        var sessionEnricher = new PropertyEnricher(name: "SessionId", sessionId);

        using (LogContext.Push(sessionEnricher))
        {
            try
            {
                // Filter: skip non-matching subjects, complete them
                var processableMessages = new List<ServiceBusReceivedMessage>();
                var items = new List<ItemChangedItem>();
                Guid? accountId = null;

                foreach (var message in messages)
                {
                    if (message.Subject != EventType.AccountItemChanged)
                    {
                        await receiver.CompleteMessageAsync(message, stoppingToken);
                        continue;
                    }

                    var json = Encoding.UTF8.GetString(message.Body);
                    var body = JsonConvert.DeserializeObject<ItemChanged>(json);

                    if (body == null || body.Quantity < 1)
                    {
                        await receiver.CompleteMessageAsync(message, stoppingToken);
                        continue;
                    }

                    accountId = body.AccountId;
                    items.Add(new ItemChangedItem
                    {
                        SourceId = body.SourceId,
                        SourceType = body.SourceType,
                        Quantity = body.Quantity
                    });
                    processableMessages.Add(message);
                }

                // Deduplicate by SourceId -- keep first occurrence
                items = items
                    .GroupBy(i => i.SourceId)
                    .Select(g => g.First())
                    .ToList();

                if (items.Count == 0 || accountId == null)
                    continue;

                // Create batch request and send via MediatR
                using var scope = _provider.CreateScope();
                var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();

                var batchRequest = new BatchItemChanged
                {
                    AccountId = accountId.Value,
                    Items = items
                };

                var success = await mediator.Send(batchRequest, stoppingToken);

                if (success)
                {
                    foreach (var message in processableMessages)
                        await receiver.CompleteMessageAsync(message, stoppingToken);
                }
                else
                {
                    foreach (var message in processableMessages)
                        await receiver.AbandonMessageAsync(message,
                            cancellationToken: stoppingToken);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex,
                    "Error processing batch for session {SessionId}", sessionId);

                // Abandon all messages in the batch on error
                foreach (var message in messages)
                {
                    try
                    {
                        await receiver.AbandonMessageAsync(message,
                            cancellationToken: stoppingToken);
                    }
                    catch (Exception abandonEx)
                    {
                        _logger.LogError(abandonEx,
                            "Error abandoning message {MessageId}", message.MessageId);
                    }
                }
            }
        }
    }
}
```

### Batch Request and Item Models

```csharp
namespace {Company}.{Domain}.Processor.Events.Outgoing;

public class BatchItemChanged : IRequest<bool>
{
    public required Guid AccountId { get; init; }
    public required List<ItemChangedItem> Items { get; init; }
}

public class ItemChangedItem
{
    public required Guid SourceId { get; init; }
    public required SourceType SourceType { get; init; }
    public required int Quantity { get; init; }
}
```

### DLQ Handler for Batch Listener (Individual Message Processing)

```csharp
private async Task DeadLetterProcessor_ProcessMessageAsync(ProcessMessageEventArgs arg)
{
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

    // DLQ processes messages individually (not as batch)
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

### Configuration Options

```csharp
public class ServiceBusOptions
{
    public const string Options = "ServiceBus";

    [Required]
    public required string ItemQueue { get; init; }
    public int ItemQueueBatchSize { get; init; } = 50;
    public int ItemQueueMaxConcurrentSessions { get; init; } = 100;
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Using ServiceBusSessionProcessor for batching | Use BackgroundService with AcceptNextSessionAsync |
| Unbounded concurrency | Use SemaphoreSlim to limit concurrent sessions |
| No deduplication | GroupBy SourceId, take first occurrence |
| Processing DLQ messages as batch | DLQ handler processes messages individually |
| Missing ServiceTimeout catch | Catch ServiceBusException with ServiceTimeout reason |
| Forgetting to dispose receiver | Use try/finally with DisposeAsync |

## Detect Existing Patterns

```bash
# Find BackgroundService with batch processing
grep -r ": BackgroundService" --include="*.cs" src/

# Find AcceptNextSessionAsync usage
grep -r "AcceptNextSessionAsync" --include="*.cs" src/

# Find ReceiveMessagesAsync batch calls
grep -r "ReceiveMessagesAsync" --include="*.cs" src/

# Find SemaphoreSlim usage
grep -r "SemaphoreSlim" --include="*.cs" src/
```

## Adding to Existing Project

1. **Use BackgroundService** (not IHostedService) for batch processing
2. **Configure batch size and max concurrent sessions** via ServiceBusOptions
3. **Implement AcceptNextSessionAsync** with SemaphoreSlim for concurrency control
4. **Add deduplication** by GroupBy SourceId before sending batch request
5. **Include paired DLQ processor** that processes messages individually
6. **Handle ServiceTimeout** exception as normal "no sessions available"
