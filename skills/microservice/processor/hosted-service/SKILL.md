---
name: hosted-service
description: >
  IHostedService with ServiceBusSessionProcessor and paired DLQ processor pattern.
  Covers lifecycle management, exact session processor configuration,
  dead letter sub-processor, graceful shutdown, and error handling.
  Trigger: hosted service, processor, lifecycle, session processor, DLQ.
metadata:
  category: microservice/processor
  agent: processor-architect
---

# Hosted Service — ServiceBusSessionProcessor Lifecycle

## Core Principles

- Each listener implements `IHostedService` directly (not BackgroundService)
- Constructor creates BOTH a `ServiceBusSessionProcessor` AND a paired `ServiceBusProcessor` for the dead letter sub-queue
- `AutoCompleteMessages = false` -- always complete/abandon explicitly
- Each ServiceBus client is a typed singleton wrapper around `ServiceBusClient`
- `StartAsync` starts both processors; `StopAsync` closes both
- Error handling via `ProcessErrorAsync` callback with `LogCritical`

## Key Patterns

### IHostedService Listener with Paired DLQ Processor

```csharp
namespace {Company}.{Domain}.Processor.Infra.ServiceBus.Listeners;

public class OrderListener : IHostedService
{
    private readonly ILogger<OrderListener> _logger;
    private readonly IServiceProvider _provider;
    private readonly ServiceBusSessionProcessor _processor;
    private readonly ServiceBusProcessor _deadLetterProcessor;

    public OrderListener(
        IServiceProvider serviceProvider,
        ILogger<OrderListener> logger,
        IOptions<ServiceBusOptions> options,
        OrderServiceBus orderServiceBus)
    {
        var serviceBusOptions = options.Value;

        _logger = logger;
        _provider = serviceProvider;

        // Main session processor for ordered event processing
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

        // Paired DLQ processor for reprocessing dead-lettered messages
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

    private async Task Processor_ProcessMessageAsync(ProcessSessionMessageEventArgs arg)
    {
        Task<bool> isHandledTask = HandleSubject(arg.Message.Subject, arg.Message);

        var isHandled = await isHandledTask;

        if (isHandled)
            await arg.CompleteMessageAsync(arg.Message);
        else
            await arg.AbandonMessageAsync(arg.Message);
    }

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

    private async Task DeadLetterProcessor_ProcessMessageAsync(ProcessMessageEventArgs arg)
    {
        // DLQ handler uses the SAME routing logic as the main processor
        Task<bool> isHandledTask = HandleSubject(arg.Message.Subject, arg.Message);

        var isHandled = await isHandledTask;

        if (isHandled)
            await arg.CompleteMessageAsync(arg.Message);
        else
            await arg.AbandonMessageAsync(arg.Message);
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

    // Subject routing and HandleAsync defined in event-routing skill
    private Task<bool> HandleSubject(string subject, ServiceBusReceivedMessage message)
    {
        // See event-routing SKILL for full pattern
        return subject switch
        {
            EventType.OrderCreated => HandleAsync<OrderCreatedData>(message),
            EventType.OrderUpdated => HandleAsync<OrderUpdatedData>(message),
            _ => Task.FromResult(true) // Complete unknown events
        };
    }

    private async Task<bool> HandleAsync<T>(ServiceBusReceivedMessage message) { /* see event-routing */ return true; }

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

### Typed ServiceBusClient Wrapper

```csharp
namespace {Company}.{Domain}.Processor.Infra.ServiceBus.Clients;

// Each external Service Bus namespace gets a typed wrapper
public class OrderServiceBus(string connectionString)
{
    public ServiceBusClient Client { get; } = new ServiceBusClient(connectionString);
}
```

### ServiceBusOptions

```csharp
namespace {Company}.{Domain}.Processor.Infra.ServiceBus;

public class ServiceBusOptions
{
    public const string Options = "ServiceBus";

    [Required]
    public required string OrderCommandTopic { get; init; }
    [Required]
    public required string Subscription { get; init; }
    public int BatchSize { get; init; } = 50;
    public int MaxConcurrentSessions { get; init; } = 100;
}
```

### Registration

```csharp
// In ServiceBusRegistrationExtensions.cs
services.AddSingleton(provider =>
{
    var options = provider.GetRequiredService<IOptions<ConnectionStringsOption>>();
    return new OrderServiceBus(options.Value.OrderServiceBus);
});

services.AddHostedService<OrderListener>();
services.AddHostedService<ProductListener>();
```

## Exact Session Processor Configuration

| Option                       | Value  | Purpose                                       |
|------------------------------|--------|-----------------------------------------------|
| PrefetchCount                | 1      | Conservative prefetch for reliability          |
| MaxConcurrentCallsPerSession | 1      | Strict ordering within each session            |
| MaxConcurrentSessions        | 1000   | High parallelism across different aggregates   |
| AutoCompleteMessages         | false  | Explicit complete/abandon for error control    |
| SessionIdleTimeout           | 1 min  | Release session lock after idle period         |
| MaxAutoLockRenewalDuration   | 5 min  | Renew lock for long-running handlers           |

## Exact DLQ Processor Configuration

| Option              | Value              | Purpose                            |
|---------------------|--------------------|------------------------------------|
| PrefetchCount       | 1                  | Process one DLQ message at a time  |
| AutoCompleteMessages| false              | Explicit complete/abandon          |
| MaxConcurrentCalls  | 1                  | Serial DLQ processing              |
| SubQueue            | SubQueue.DeadLetter| Target the dead letter sub-queue   |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Creating processor in StartAsync | Create in constructor, start in StartAsync |
| Missing DLQ processor | Always pair main processor with DLQ processor |
| AutoCompleteMessages = true | Set false for explicit control |
| Using StopProcessingAsync | Use CloseAsync in StopAsync |
| Missing error handler | Always wire ProcessErrorAsync with LogCritical |

## Detect Existing Patterns

```bash
# Find IHostedService implementations
grep -r ": IHostedService" --include="*.cs" src/

# Find ServiceBusSessionProcessor usage
grep -r "ServiceBusSessionProcessor" --include="*.cs" src/

# Find SubQueue.DeadLetter usage
grep -r "SubQueue.DeadLetter" --include="*.cs" src/

# Find AddHostedService registrations
grep -r "AddHostedService" --include="*.cs" src/
```

## Adding to Existing Project

1. **Create typed ServiceBus client wrapper** in `Infra/ServiceBus/Clients/`
2. **Add connection string** to `ConnectionStringsOption`
3. **Add topic/subscription names** to `ServiceBusOptions`
4. **Create listener class** implementing `IHostedService` with paired DLQ processor
5. **Register singleton client** and `AddHostedService<T>()` in DI extension
6. **Match exact configuration values**: PrefetchCount=1, MaxConcurrentSessions=1000, etc.
