---
name: outbox
description: "Implement reliable at-least-once event publishing with the transactional outbox pattern, committing events and OutboxMessages in one IUnitOfWork save and draining them to Service Bus via a singleton ServiceBusPublisher. Use when wiring CommitEventService, batch publishing, or fire-and-forget StartPublish. Do NOT use for the EF Core store schema (use event-store) or for consumer-side idempotent handling (use sequence-checking)."
metadata:
  category: "microservice/command"
  agent: "command-architect"
---
# Outbox Pattern -- Reliable Event Publishing

## Core Principles

- Events and outbox messages are saved via **IUnitOfWork** (single `SaveChangesAsync` call)
- `OutboxMessage` wraps an `Event` via foreign key (shared PK), NOT by serializing the event body
- `CommitEventService` orchestrates: AddRangeAsync events + outbox, SaveChangesAsync, then StartPublish
- `ServiceBusPublisher` is a **singleton** that uses `Task.Run` (fire-and-forget), `lock`, and scope creation
- Publisher reads outbox in batches of 200, publishes each message, removes each, then saves
- Guarantees **at-least-once delivery** -- consumers must be idempotent

## Key Patterns

### OutboxMessage Entity

```csharp
using {Company}.{Domain}.Commands.Domain.Events;

namespace {Company}.{Domain}.Commands.Domain.Entities;

public class OutboxMessage
{
    public static IEnumerable<OutboxMessage> ToManyMessages(IEnumerable<Event> events)
        => events.Select(e => new OutboxMessage(e));

    private OutboxMessage() { }

    public OutboxMessage(Event @event)
    {
        Event = @event;
    }

    public long Id { get; private set; }
    public Event? Event { get; private set; }
}
```

Key details:
- `Id` is `long` (matches Event.Id -- shared primary key via EF Core FK config)
- **No Body/Subject/SessionId columns** -- the OutboxMessage simply wraps the Event via navigation property
- `ToManyMessages` is a static factory method that creates one OutboxMessage per Event
- Private parameterless constructor for EF Core
- Public constructor takes an `Event` to set the navigation property

### ICommitEventService Interface

```csharp
using {Company}.{Domain}.Commands.Domain.Core;

namespace {Company}.{Domain}.Commands.Application.Contracts.Services.BaseServices;

public interface ICommitEventService
{
    Task CommitNewEventsAsync<T>(Aggregate<T> model);
}
```

### CommitEventService Implementation

```csharp
using {Company}.{Domain}.Commands.Application.Contracts.Repositories;
using {Company}.{Domain}.Commands.Application.Contracts.Services.BaseServices;
using {Company}.{Domain}.Commands.Application.Contracts.Services.ServiceBus;
using {Company}.{Domain}.Commands.Domain.Core;
using {Company}.{Domain}.Commands.Domain.Entities;
using {Company}.{Domain}.Commands.Domain.Events;

namespace {Company}.{Domain}.Commands.Infra.Services.BaseService;

public class CommitEventService(IUnitOfWork unitOfWork, IServiceBusPublisher serviceBusPublisher)
    : ICommitEventService
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;
    private readonly IServiceBusPublisher _serviceBusPublisher = serviceBusPublisher;

    public async Task CommitNewEventsAsync<T>(Aggregate<T> model)
    {
        var newEvents = model.GetUncommittedEvents();

        await SaveToDatabase(newEvents);

        model.MarkChangesAsCommitted();

        _serviceBusPublisher.StartPublish();
    }

    private async Task SaveToDatabase(
        IReadOnlyList<Event> newEvents,
        CancellationToken cancellationToken = default)
    {
        await _unitOfWork.Events.AddRangeAsync(newEvents);

        var messages = OutboxMessage.ToManyMessages(newEvents);

        await _unitOfWork.OutboxMessages.AddRangeAsync(messages);

        await _unitOfWork.SaveChangesAsync(cancellationToken);
    }
}
```

Key details:
- Takes `IUnitOfWork` and `IServiceBusPublisher` via primary constructor
- `CommitNewEventsAsync<T>` accepts the aggregate, gets uncommitted events, saves, marks committed, then signals publisher
- `SaveToDatabase`: adds events via `_unitOfWork.Events.AddRangeAsync`, creates outbox messages via `OutboxMessage.ToManyMessages`, adds them, then calls `SaveChangesAsync`
- **No explicit transaction** -- `SaveChangesAsync` is a single atomic operation (events + outbox messages saved together)
- `MarkChangesAsCommitted()` clears the uncommitted events list after successful save
- `StartPublish()` is fire-and-forget (non-blocking)

### IServiceBusPublisher Interface

```csharp
namespace {Company}.{Domain}.Commands.Application.Contracts.Services.ServiceBus;

public interface IServiceBusPublisher
{
    void StartPublish();
}
```

### ServiceBusPublisher Implementation

```csharp
using {Company}.{Domain}.Commands.Application.Contracts.Repositories;
using {Company}.{Domain}.Commands.Application.Contracts.Services.ServiceBus;
using {Company}.{Domain}.Commands.Domain.Entities;
using {Company}.{Domain}.Commands.Domain.Events;
using Azure.Messaging.ServiceBus;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System.Text;

namespace {Company}.{Domain}.Commands.Infra.Services.ServiceBus;

public class ServiceBusPublisher : IServiceBusPublisher
{
    private readonly IServiceProvider _serviceProvider;
    private readonly ServiceBusSender _sender;
    private readonly ILogger<ServiceBusPublisher> _logger;

    private readonly SemaphoreSlim publishGate = new(1, 1);

    public ServiceBusPublisher(
        IServiceProvider serviceProvider,
        IConfiguration configuration,
        ServiceBusClient serviceBusClient,
        ILogger<ServiceBusPublisher> logger)
    {
        _serviceProvider = serviceProvider;
        _sender = serviceBusClient.CreateSender(configuration["ServiceBus:Topic"]);
        _logger = logger;
    }

    public async Task StartPublishAsync(CancellationToken cancellationToken = default)
    {
        if (!await publishGate.WaitAsync(0, cancellationToken))
            return;

        try
        {
            await PublishNonPublishedMessagesAsync(cancellationToken);
        }
        finally
        {
            publishGate.Release();
        }
    }

    private async Task PublishNonPublishedMessagesAsync(
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Publishing to service bus requested.");

        try
        {
            using var scope = _serviceProvider.CreateScope();
            var unitOfWork = scope.ServiceProvider.GetRequiredService<IUnitOfWork>();

            while (await unitOfWork.OutboxMessages.AnyAsync(cancellationToken))
            {
                var messages = await unitOfWork.OutboxMessages
                    .GetOutboxMessagesAsync(200, cancellationToken);

                _logger.LogInformation(
                    "Fetched message from outbox {Count}", messages.Count);

                await PublishAndRemoveMessagesAsync(
                    messages, unitOfWork, cancellationToken);
            }
        }
        catch (Exception e)
        {
            _logger.LogCritical(e, "Message publish failed while attempting to send messages");
        }
    }

    private async Task PublishAndRemoveMessagesAsync(
        IEnumerable<OutboxMessage> messages, IUnitOfWork unitOfWork,
        CancellationToken cancellationToken)
    {
        foreach (var message in messages)
        {
            await SendMessageAsync(message.Event!);

            await unitOfWork.OutboxMessages.RemoveAsync(message);

            await unitOfWork.SaveChangesAsync(cancellationToken);
        }

        await Task.CompletedTask;
    }

    private async Task SendMessageAsync(Event @event)
    {
        var body = new MessageBody()
        {
            AggregateId = @event.AggregateId,
            DateTime = @event.DateTime,
            Sequence = @event.Sequence,
            Type = @event.Type.ToString(),
            UserId = @event.UserId?.ToString(),
            Version = @event.Version,
            Data = ((dynamic)@event).Data
        };

        var messageBody = JsonConvert.SerializeObject(body);

        var message = new ServiceBusMessage(Encoding.UTF8.GetBytes(messageBody))
        {
            CorrelationId = @event.Id.ToString(),
            MessageId = @event.Id.ToString(),
            PartitionKey = @event.AggregateId.ToString(),
            SessionId = @event.AggregateId.ToString(),
            Subject = @event.Type.ToString(),
            ApplicationProperties =
            {
                { nameof(@event.AggregateId), @event.AggregateId },
                { nameof(@event.Sequence), @event.Sequence },
                { nameof(@event.Version), @event.Version },
            }
        };

        await _sender.SendMessageAsync(message);
    }
}
```

### MessageBody Class

```csharp
namespace {Company}.{Domain}.Commands.Infra.Services.ServiceBus;

public class MessageBody
{
    public Guid AggregateId { get; set; }
    public int Sequence { get; set; }
    public string? UserId { get; set; }
    public required string Type { get; set; }
    public required object Data { get; set; }
    public DateTime DateTime { get; set; }
    public int Version { get; set; }
}
```

### IUnitOfWork Interface

```csharp
namespace {Company}.{Domain}.Commands.Application.Contracts.Repositories;

public interface IUnitOfWork : IDisposable
{
    IOutboxMessagesRepository OutboxMessages { get; }
    IEventRepository Events { get; }
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
```

### DI Registration

```csharp
// In InfraContainer.AddInfraServices:
services.AddScoped<IUnitOfWork, UnitOfWork>();
services.AddSingleton<IServiceBusPublisher, ServiceBusPublisher>();
services.AddSingleton(s =>
{
    return new ServiceBusClient(configuration.GetConnectionString("ServiceBus"));
});
services.AddScoped<ICommitEventService, CommitEventService>();
```

Key registration details:
- `ServiceBusPublisher` is **singleton** (persists across requests, holds the lock state)
- `CommitEventService` is **scoped** (uses scoped IUnitOfWork)
- `ServiceBusClient` is **singleton** (connection pooling)
- `UnitOfWork` is **scoped** (ties to DbContext lifetime)

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Serializing event body into OutboxMessage | OutboxMessage wraps Event via FK (navigation property) |
| No recovery poller | Use a hosted service to retry unpublished rows after process restart |
| Publishing before DB save | Save events + outbox first, then StartPublish |
| Overlapping publisher drains | Use `SemaphoreSlim` to prevent concurrent drains |
| Creating new ServiceBusClient per publish | Inject singleton ServiceBusClient, create sender in constructor |
| Batch-saving after all publishes | Remove each message individually after publish, save each time |

## Detect Existing Patterns

```bash
# Find OutboxMessage entity
grep -r "class OutboxMessage" --include="*.cs" src/

# Find CommitEventService
grep -r "CommitEventService\|ICommitEventService" --include="*.cs" src/

# Find ServiceBusPublisher
grep -r "ServiceBusPublisher\|IServiceBusPublisher" --include="*.cs" src/

# Find publisher registration
grep -r "AddSingleton.*ServiceBusPublisher" --include="*.cs" src/
```

## Adding to Existing Project

1. **Check OutboxMessage structure** -- it should wrap Event via FK, not serialize body
2. **Verify IUnitOfWork** has both `Events` and `OutboxMessages` repositories
3. **Match CommitEventService pattern** -- AddRangeAsync events, ToManyMessages outbox, SaveChangesAsync
4. **Check publisher is singleton** with lock + Task.Run pattern
5. **Verify batch size** is 200 in `GetOutboxMessagesAsync`
6. **Ensure publisher creates its own scope** for database access
