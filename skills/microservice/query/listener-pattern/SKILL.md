---
name: listener-pattern
description: >
  Service Bus session-based listener as IHostedService. Uses ServiceBusSessionProcessor
  with specific config, paired dead-letter processor, subject-based routing via switch
  expression, typed HandleAsync<T> deserialization, and LogContext enrichment.
  Trigger: service bus listener, session processor, event routing, hosted service.
metadata:
  category: microservice/query
  agent: query-architect
  when-to-use: "When creating or modifying Service Bus session-based listener services"
---

# Listener Pattern — ServiceBusSessionProcessor + DLQ Processor

## Core Principles

- Listener is an `IHostedService` with constructor-initialized processors
- **ServiceBusSessionProcessor** for ordered per-aggregate processing
- **Paired ServiceBusProcessor** for dead letter queue (DLQ) reprocessing
- Subject-based routing via switch expression to typed `HandleAsync<T>` methods
- Typed deserialization: `JsonConvert.DeserializeObject<Event<T>>(json)`
- MediatR dispatch via scoped `IServiceProvider` for each message
- Return `true` from handler = `CompleteMessageAsync`, `false` = `AbandonMessageAsync`
- Serilog `LogContext.Push` with `PropertyEnricher` for structured logging

## Key Patterns

### Full Listener Implementation

```csharp
namespace {Company}.{Domain}.Query.Infra.Services.ServiceBus.Listeners;

public class OrdersListener : IHostedService
{
    private readonly ILogger<OrdersListener> _logger;
    private readonly DomainServiceBus _serviceBusClient;
    private readonly IServiceProvider _serviceProvider;
    private readonly ServiceBusSessionProcessor _processor;
    private readonly ServiceBusProcessor _deadLetterProcessor;

    public OrdersListener(
        IServiceProvider serviceProvider,
        ILogger<OrdersListener> logger,
        IOptions<ServiceBusOptions> serviceBusOptions,
        DomainServiceBus serviceBusClient)
    {
        _serviceProvider = serviceProvider;
        _logger = logger;
        _serviceBusClient = serviceBusClient;

        // Session processor configuration
        var options = new ServiceBusSessionProcessorOptions
        {
            AutoCompleteMessages = false,
            PrefetchCount = 1,
            MaxConcurrentCallsPerSession = 1,
            MaxConcurrentSessions = 1000,
            ReceiveMode = ServiceBusReceiveMode.PeekLock
        };

        _processor = _serviceBusClient.Client.CreateSessionProcessor(
            serviceBusOptions.Value.Topic,
            serviceBusOptions.Value.Subscription,
            options);

        _processor.ProcessMessageAsync += Processor_ProcessMessageAsync;
        _processor.ProcessErrorAsync += Processor_ProcessErrorAsync;

        // Dead letter queue processor
        _deadLetterProcessor = _serviceBusClient.Client.CreateProcessor(
            serviceBusOptions.Value.Topic,
            serviceBusOptions.Value.Subscription,
            new ServiceBusProcessorOptions()
            {
                PrefetchCount = 1,
                AutoCompleteMessages = false,
                MaxConcurrentCalls = 1,
                SubQueue = SubQueue.DeadLetter
            });

        _deadLetterProcessor.ProcessMessageAsync +=
            DeadLetterProcessor_ProcessMessageAsync;
        _deadLetterProcessor.ProcessErrorAsync +=
            DeadLetterProcessor_ProcessErrorAsync;
    }

    // --- Main message processing ---

    private async Task Processor_ProcessMessageAsync(
        ProcessSessionMessageEventArgs arg)
    {
        Task<bool> isHandledTask =
            HandleSubject(arg.Message.Subject, arg.Message);

        var isHandled = await isHandledTask;

        if (isHandled)
        {
            await arg.CompleteMessageAsync(arg.Message);
        }
        else
        {
            await arg.AbandonMessageAsync(arg.Message);
        }
    }

    private Task Processor_ProcessErrorAsync(ProcessErrorEventArgs arg)
    {
        _logger.LogCritical(arg.Exception,
            "OrdersListener => _processor => " +
            "Processor_ProcessErrorAsync " +
            "Message handler encountered an exception," +
            " Error Source:{ErrorSource}," +
            " Entity Path:{EntityPath}",
            arg.ErrorSource.ToString(),
            arg.EntityPath);

        return Task.CompletedTask;
    }

    // --- Dead letter processing (same routing) ---

    private async Task DeadLetterProcessor_ProcessMessageAsync(
        ProcessMessageEventArgs arg)
    {
        Task<bool> isHandledTask =
            HandleSubject(arg.Message.Subject, arg.Message);

        var isHandled = await isHandledTask;

        if (isHandled)
            await arg.CompleteMessageAsync(arg.Message);
        else
            await arg.AbandonMessageAsync(arg.Message);
    }

    private Task DeadLetterProcessor_ProcessErrorAsync(
        ProcessErrorEventArgs arg)
    {
        _logger.LogCritical(arg.Exception,
            "DeadLetter Message handler encountered an exception," +
            " Error Source:{ErrorSource}," +
            " Entity Path:{EntityPath}",
            arg.ErrorSource.ToString(),
            arg.EntityPath);

        return Task.CompletedTask;
    }

    // --- Subject-based routing with LogContext ---

    private Task<bool> HandleSubject(
        string subject, ServiceBusReceivedMessage message)
    {
        var eventType = new PropertyEnricher(
            name: "EventType", message.Subject);
        var sessionId = new PropertyEnricher(
            name: "SessionId", message.SessionId);
        var messageId = new PropertyEnricher(
            name: "MessageId", message.MessageId);

        using (LogContext.Push(eventType, sessionId, messageId))
        {
            return subject switch
            {
                EventType.OrderCreated =>
                    HandleAsync<OrderCreatedData>(message),
                EventType.OrderUpdated =>
                    HandleAsync<OrderUpdatedData>(message),
                EventType.OrderStatusChanged =>
                    HandleAsync<OrderStatusChangedData>(message),
                EventType.OrderItemAdded =>
                    HandleAsync<OrderItemAddedData>(message),
                // Skip known but unhandled event types
                EventType.OrderViewed => Task.FromResult(true),
                // Unknown events — return false
                _ => Task.FromResult(false)
            };
        }
    }

    // --- Typed deserialization + MediatR dispatch ---

    private async Task<bool> HandleAsync<T>(
        ServiceBusReceivedMessage message)
    {
        var json = Encoding.UTF8.GetString(message.Body);

        var body = JsonConvert.DeserializeObject<Event<T>>(json)
            ?? throw new InvalidOperationException(
                "Message body was serialized to null");

        using var scope = _serviceProvider.CreateScope();

        var mediator = scope.ServiceProvider
            .GetRequiredService<IMediator>();

        return await SendAsync(mediator, body);
    }

    private async Task<bool> SendAsync<T>(
        IMediator mediator, Event<T> @event)
    {
        var result = await mediator.Send(@event);

        if (!result)
            _logger.LogWarning(
                "Event Not Handling With Aggregate : {id}, " +
                "Type : {type} and sequence : {sequence}",
                @event.AggregateId,
                @event.Type,
                @event.Sequence);

        return result;
    }

    // --- Lifecycle ---

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
}
```

### ServiceBus Client Wrapper

```csharp
namespace {Company}.{Domain}.Query.Infra.Services.ServiceBus.Clients;

public class DomainServiceBus(ServiceBusOptions serviceBusOptions)
{
    public ServiceBusClient Client { get; set; } =
        new ServiceBusClient(serviceBusOptions.ConnectionString);
}
```

### ServiceBus Options

```csharp
namespace {Company}.{Domain}.Query.Infra.Services.ServiceBus;

public class ServiceBusOptions
{
    public const string ServiceBus = "ServiceBus";

    [Required]
    public required string ConnectionString { get; init; }

    [Required]
    public required string Topic { get; init; }

    [Required]
    public required string Subscription { get; init; }
}
```

### EventType Constants

```csharp
namespace {Company}.{Domain}.Query.Infra.Constants;

public class EventType
{
    public const string OrderCreated = "OrderCreated";
    public const string OrderUpdated = "OrderUpdated";
    public const string OrderStatusChanged = "OrderStatusChanged";
    public const string OrderItemAdded = "OrderItemAdded";
    public const string OrderViewed = "OrderViewed";
}
```

### Registration

```csharp
// In ServiceBusRegistrationExtensions
public static void UseServiceBus(
    this IServiceCollection services,
    IConfiguration configuration)
{
    services.AddOptions<ServiceBusOptions>()
        .Bind(configuration.GetSection(ServiceBusOptions.ServiceBus))
        .ValidateDataAnnotations()
        .ValidateOnStart();

    services.AddSingleton(provider =>
    {
        var options = provider
            .GetRequiredService<IOptions<ServiceBusOptions>>();
        return new DomainServiceBus(options.Value);
    });

    services.AddHostedService<OrdersListener>();
}
```

## Session Processor Configuration

| Setting | Value | Why |
|---|---|---|
| `AutoCompleteMessages` | `false` | Explicit Complete/Abandon based on handler result |
| `PrefetchCount` | `1` | Process one message at a time per session |
| `MaxConcurrentCallsPerSession` | `1` | Strict ordering within each aggregate session |
| `MaxConcurrentSessions` | `1000` | High parallelism across different aggregates |
| `ReceiveMode` | `PeekLock` | Message stays locked until Complete/Abandon |

## DLQ Processor Configuration

| Setting | Value | Why |
|---|---|---|
| `PrefetchCount` | `1` | Conservative for dead letters |
| `AutoCompleteMessages` | `false` | Explicit Complete/Abandon |
| `MaxConcurrentCalls` | `1` | Sequential DLQ processing |
| `SubQueue` | `SubQueue.DeadLetter` | Read from dead letter sub-queue |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| `AutoCompleteMessages = true` | Always `false` — explicit Complete/Abandon |
| EventDeserializer separate class | Inline switch + typed `HandleAsync<T>` |
| `StopProcessingAsync` in StopAsync | Use `CloseAsync` in StopAsync |
| `await` on StartProcessingAsync | Fire-and-forget: `_processor.StartProcessingAsync(ct);` |
| `BackgroundService` for DLQ | Paired `ServiceBusProcessor` in same listener |
| Missing LogContext enrichment | Push EventType, SessionId, MessageId via PropertyEnricher |

## Detect Existing Patterns

```bash
# Find ServiceBusSessionProcessor usage
grep -r "ServiceBusSessionProcessor\|CreateSessionProcessor" --include="*.cs" Infra/

# Find IHostedService listeners
grep -r "IHostedService" --include="*.cs" Infra/Services/ServiceBus/

# Find subject routing
grep -r "subject switch" --include="*.cs" Infra/Services/ServiceBus/

# Find dead letter processor
grep -r "SubQueue.DeadLetter" --include="*.cs" Infra/
```

## Adding to Existing Project

1. **Match the exact processor options** shown above (PrefetchCount=1, etc.)
2. **Add new event types** to the `HandleSubject` switch expression
3. **Add EventType constant** for each new event in the constants class
4. **DLQ processor** reuses the same `HandleSubject` routing logic
5. **Register** via `services.AddHostedService<YourListener>()`
6. **Serilog enrichment** — push EventType, SessionId, MessageId for each message
