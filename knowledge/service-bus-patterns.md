# Azure Service Bus Patterns

Patterns for Azure Service Bus in processor microservices. Covers typed ServiceBusClient wrappers, ServiceBusSessionProcessor configuration, paired DLQ processors, subject-based event routing, batch processing with BackgroundService, and message publishing.

---

## Architecture: Typed ServiceBusClient Wrappers

Each external Service Bus namespace is wrapped in a typed singleton class. Multiple listeners may share the same client wrapper if they connect to the same namespace.

```csharp
namespace {Company}.{Domain}.Processor.Infra.ServiceBus.Clients;

// One typed wrapper per Service Bus namespace connection
public class OrderServiceBus(string connectionString)
{
    public ServiceBusClient Client { get; } = new ServiceBusClient(connectionString);
}

public class ProductServiceBus(string connectionString)
{
    public ServiceBusClient Client { get; } = new ServiceBusClient(connectionString);
}

public class ItemQueueListenerServiceBus(string connectionString)
{
    public ServiceBusClient Client { get; } = new ServiceBusClient(connectionString);
}
```

### Connection String Options

```csharp
namespace {Company}.{Domain}.Processor.Infra.ServiceBus;

public class ConnectionStringsOption
{
    public const string Options = "ConnectionStrings";

    [Required]
    public required string OrderServiceBus { get; init; }
    [Required]
    public required string ProductServiceBus { get; init; }
    [Required]
    public required string ItemQueueListenerServiceBus { get; init; }
    [Required]
    public required string ItemQueueSenderServiceBus { get; init; }
}
```

### Registration

```csharp
public static class ServiceBusRegistrationExtensions
{
    public static IServiceCollection RegisterServiceBus(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<ConnectionStringsOption>()
            .Bind(configuration.GetSection(ConnectionStringsOption.Options))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddOptions<ServiceBusOptions>()
            .Bind(configuration.GetSection(ServiceBusOptions.Options))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        // Typed client singletons
        services.AddSingleton(provider =>
        {
            var options = provider.GetRequiredService<IOptions<ConnectionStringsOption>>();
            return new OrderServiceBus(options.Value.OrderServiceBus);
        });

        services.AddSingleton(provider =>
        {
            var options = provider.GetRequiredService<IOptions<ConnectionStringsOption>>();
            return new ProductServiceBus(options.Value.ProductServiceBus);
        });

        // Listeners
        services.AddHostedService<OrderListener>();
        services.AddHostedService<ProductListener>();
        services.AddHostedService<AccountListener>();
        services.AddHostedService<ItemQueueListener>();

        // Publishers and services
        services.AddSingleton<IServiceBusPublisher, ServiceBusPublisher>();
        services.AddSingleton<IRetryCallerService, RetryCallerService>();

        return services;
    }
}
```

---

## ServiceBusSessionProcessor Configuration

Every IHostedService listener creates a `ServiceBusSessionProcessor` in the constructor with these exact options:

```csharp
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
```

### Configuration Values Reference

| Option                       | Value  | Purpose                                       |
|------------------------------|--------|-----------------------------------------------|
| PrefetchCount                | 1      | Conservative prefetch for reliability          |
| MaxConcurrentCallsPerSession | 1      | Strict ordering within each session/aggregate  |
| MaxConcurrentSessions        | 1000   | High parallelism across different aggregates   |
| AutoCompleteMessages         | false  | Explicit complete/abandon for error control    |
| SessionIdleTimeout           | 1 min  | Release session lock after idle period         |
| MaxAutoLockRenewalDuration   | 5 min  | Renew lock for long-running handlers           |

---

## Paired DLQ Processor Pattern

Every listener creates a paired `ServiceBusProcessor` targeting the dead letter sub-queue. This runs alongside the main session processor.

```csharp
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
```

### DLQ Processor Configuration

| Option              | Value              | Purpose                            |
|---------------------|--------------------|------------------------------------|
| PrefetchCount       | 1                  | Process one DLQ message at a time  |
| AutoCompleteMessages| false              | Explicit complete/abandon          |
| MaxConcurrentCalls  | 1                  | Serial DLQ processing              |
| SubQueue            | SubQueue.DeadLetter| Target the dead letter sub-queue   |

### DLQ Handler

The DLQ handler reuses the **same routing logic** as the main processor:

```csharp
private async Task DeadLetterProcessor_ProcessMessageAsync(ProcessMessageEventArgs arg)
{
    // Note: ProcessMessageEventArgs (not ProcessSessionMessageEventArgs)
    Task<bool> isHandledTask = HandleSubject(arg.Message.Subject, arg.Message);

    var isHandled = await isHandledTask;

    if (isHandled)
        await arg.CompleteMessageAsync(arg.Message);
    else
        await arg.AbandonMessageAsync(arg.Message);
}
```

---

## Subject-Based Event Routing

Each listener has an inline `HandleSubject` switch that routes by `message.Subject`:

```csharp
private Task<bool> HandleSubject(string subject, ServiceBusReceivedMessage message)
{
    return subject switch
    {
        EventType.OrderCreated => HandleAsync<OrderCreatedData>(message),
        EventType.OrderUpdated => HandleAsync<OrderUpdatedData>(message),
        _ => Task.FromResult(true) // Complete unknown events
    };
}
```

### HandleAsync Method

```csharp
private async Task<bool> HandleAsync<T>(ServiceBusReceivedMessage message)
{
    var eventType = new PropertyEnricher(name: "EventType", message.Subject);
    var sessionId = new PropertyEnricher(name: "SessionId", message.SessionId);
    var messageId = new PropertyEnricher(name: "MessageId", message.MessageId);

    using (LogContext.Push(eventType, sessionId, messageId))
    {
        var json = Encoding.UTF8.GetString(message.Body);

        var body = JsonConvert.DeserializeObject<Event<T>>(json)
            ?? throw new InvalidOperationException("Message body was serialized to null");

        using var scope = _provider.CreateScope();
        var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();

        return await SendAsync(mediator, body);
    }
}
```

### Event Type Constants

Separate constants classes per source domain:

```csharp
public class EventType
{
    public const string OrderCreated = "OrderCreated";
    public const string OrderUpdated = "OrderUpdated";
    public const string AccountItemChanged = "AccountItemChanged";
}

public static class AccountEventType
{
    public const string AccountConfirmed = "AccountConfirmed";
    public const string AccountUpdated = "AccountUpdated";
    public const string SubscriptionCreated = "SubscriptionCreated";
    public const string SubscriptionRemoved = "SubscriptionRemoved";
}
```

---

## Batch Processing with BackgroundService

Batch processing uses `BackgroundService` (not IHostedService), `SemaphoreSlim` for concurrency, and manual session acceptance:

```csharp
public class ItemQueueListener : BackgroundService
{
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
                catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error accepting session");
                }
                finally
                {
                    semaphore.Release();
                }
            }, stoppingToken);
        }
    }
}
```

### AcceptNextSessionAsync + ReceiveMessagesAsync

```csharp
receiver = await _serviceBusClient.AcceptNextSessionAsync(
    _queueName,
    new ServiceBusSessionReceiverOptions
    {
        PrefetchCount = _batchSize,
        ReceiveMode = ServiceBusReceiveMode.PeekLock
    },
    stoppingToken);

var messages = await receiver.ReceiveMessagesAsync(
    maxMessages: _batchSize,
    maxWaitTime: TimeSpan.FromSeconds(5),
    cancellationToken: stoppingToken);
```

### Deduplication

```csharp
// Deduplicate by SourceId -- keep first occurrence
items = items
    .GroupBy(i => i.SourceId)
    .Select(g => g.First())
    .ToList();
```

### Batch vs Individual

- **Main processor**: collects items into `BatchItemChanged` request, sends to MediatR
- **DLQ processor**: processes messages individually (not batched)

---

## Message Publishing

### Publishing to Service Bus Queue

```csharp
public class ServiceBusPublisher : IServiceBusPublisher
{
    private readonly ServiceBusSender _sender;

    public ServiceBusPublisher(
        SenderServiceBus senderServiceBus,
        IOptions<ServiceBusOptions> options)
    {
        _sender = senderServiceBus.Client.CreateSender(options.Value.QueueName);
    }

    private async Task SendMessageAsync(CreateTransactionEvent command)
    {
        var messageBody = JsonConvert.SerializeObject(command, new JsonSerializerSettings
        {
            NullValueHandling = NullValueHandling.Ignore
        });

        var message = new ServiceBusMessage(Encoding.UTF8.GetBytes(messageBody))
        {
            CorrelationId = command.ReferenceId,
            MessageId = command.ReferenceId,
            PartitionKey = command.ReferenceId,
            SessionId = command.ReferenceId,
            Subject = "CreateTransaction",
            ContentType = "application/json"
        };

        await _sender.SendMessageAsync(message);
    }
}
```

---

## Message Properties

| Property       | Value                         | Purpose                                 |
|----------------|-------------------------------|-----------------------------------------|
| Subject        | EventType string              | Route to correct handler via switch      |
| SessionId      | AggregateId or AccountId      | Ordered processing per aggregate         |
| MessageId      | Unique event/source ID        | Deduplication                           |
| PartitionKey   | Same as SessionId             | Partition affinity                       |
| CorrelationId  | Reference/Account ID          | Request tracing across services          |
| ContentType    | application/json              | Serialization format                     |
| ApplicationProperties | Additional metadata    | Custom key-value pairs for routing       |

---

## ServiceBusOptions

```csharp
public class ServiceBusOptions
{
    public const string Options = "ServiceBus";

    [Required]
    public required string OrderCommandTopic { get; init; }
    [Required]
    public required string ProductCommandTopic { get; init; }
    [Required]
    public required string AccountsTopic { get; init; }
    [Required]
    public required string Subscription { get; init; }
    [Required]
    public required string ItemQueue { get; init; }

    public int ItemQueueBatchSize { get; init; } = 50;
    public int ItemQueueMaxConcurrentSessions { get; init; } = 100;
}
```

---

## Related Documents

- `knowledge/dead-letter-reprocessing.md` -- Paired DLQ processor details
- `knowledge/event-sourcing-flow.md` -- Complete event sourcing flow
- `knowledge/outbox-pattern.md` -- Outbox publishing details
- `skills/microservice/processor/hosted-service/SKILL.md` -- IHostedService listener pattern
- `skills/microservice/processor/event-routing/SKILL.md` -- Subject-based routing details
- `skills/microservice/processor/batch-processing/SKILL.md` -- Batch processing details
