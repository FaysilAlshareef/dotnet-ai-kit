# Outbox Pattern

Transactional outbox pattern for reliable event publishing in CQRS microservice architecture.
Guarantees at-least-once delivery by persisting outbox messages in the same save operation as domain events.

---

## Overview

The outbox pattern solves the dual-write problem: when you need to save data to a database AND send a message to a message broker, you cannot guarantee both succeed atomically. The outbox pattern writes the outbox message to the database in the same save operation as the business data, then a separate process reads and publishes those messages.

In this architecture, `OutboxMessage` wraps an `Event` via a foreign key (shared primary key). The publisher reads the Event navigation property to construct the Service Bus message at publish time.

```
+-------------------------------------------+
|       Single SaveChangesAsync Call         |
|                                            |
|  +----------------+   +-----------------+  |
|  |  Events Table  |   | OutboxMessages  |  |
|  |  (appended)    |   | (FK to Event)   |  |
|  +----------------+   +-----------------+  |
|                                            |
+-------------------------------------------+
                   |
         +---------+  (fire-and-forget Task.Run)
         v
+------------------------+
| ServiceBusPublisher    |
| (Singleton, lock)      |
+----------+-------------+
           |
           v
+------------------------+
| Azure Service Bus      |
| (Topic)                |
+------------------------+
```

---

## OutboxMessage Entity

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
- `Id` is `long` -- shared with `Event.Id` via foreign key configuration
- **No Body, Subject, SessionId, or Topic columns** -- the message body is constructed at publish time from the Event navigation property
- `ToManyMessages` is a static factory that creates one OutboxMessage per Event
- Private parameterless constructor for EF Core materialization

### EF Core Configuration

```csharp
using {Company}.{Domain}.Commands.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace {Company}.{Domain}.Commands.Infra.Persistence.Configurations;

public class OutboxMessageConfiguration : IEntityTypeConfiguration<OutboxMessage>
{
    public void Configure(EntityTypeBuilder<OutboxMessage> builder)
    {
        builder.HasOne(e => e.Event)
            .WithOne()
            .HasForeignKey<OutboxMessage>(e => e.Id)
            .IsRequired()
            .OnDelete(DeleteBehavior.Cascade);
    }
}
```

Key details:
- **1:1 relationship**: `OutboxMessage.Id` IS the foreign key to `Event.Id` (shared primary key)
- `HasOne(e => e.Event).WithOne()` -- one-directional navigation from OutboxMessage to Event
- `HasForeignKey<OutboxMessage>(e => e.Id)` -- the OutboxMessage's own PK is the FK
- Cascade delete cleans up the relationship

---

## ICommitEventService

```csharp
using {Company}.{Domain}.Commands.Domain.Core;

namespace {Company}.{Domain}.Commands.Application.Contracts.Services.BaseServices;

public interface ICommitEventService
{
    Task CommitNewEventsAsync<T>(Aggregate<T> model);
}
```

---

## CommitEventService Implementation

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

    private async Task SaveToDatabase(IReadOnlyList<Event> newEvents)
    {
        await _unitOfWork.Events.AddRangeAsync(newEvents);

        var messages = OutboxMessage.ToManyMessages(newEvents);

        await _unitOfWork.OutboxMessages.AddRangeAsync(messages);

        await _unitOfWork.SaveChangesAsync();
    }
}
```

Key flow:
1. Get uncommitted events from the aggregate (`IReadOnlyList<Event>`)
2. Add events to the Events repository via `_unitOfWork.Events.AddRangeAsync`
3. Create OutboxMessage wrappers via `OutboxMessage.ToManyMessages(newEvents)`
4. Add outbox messages via `_unitOfWork.OutboxMessages.AddRangeAsync`
5. Single `_unitOfWork.SaveChangesAsync()` persists both atomically
6. `model.MarkChangesAsCommitted()` clears the aggregate's uncommitted events
7. `_serviceBusPublisher.StartPublish()` signals the publisher (fire-and-forget)

Note: There is **no explicit `BeginTransactionAsync`** -- the single `SaveChangesAsync` call is atomic.

---

## IUnitOfWork

```csharp
namespace {Company}.{Domain}.Commands.Application.Contracts.Repositories;

public interface IUnitOfWork : IDisposable
{
    IOutboxMessagesRepository OutboxMessages { get; }
    IEventRepository Events { get; }
    Task<int> SaveChangesAsync();
}
```

### IOutboxMessagesRepository

```csharp
namespace {Company}.{Domain}.Commands.Application.Contracts.Repositories;

public interface IOutboxMessagesRepository : IAsyncRepository<OutboxMessage>
{
    Task<bool> AnyAsync();
    Task<List<OutboxMessage>> GeOutboxMessageAsync(int count);
}
```

### OutboxMessageRepository Implementation

```csharp
public class OutboxMessageRepository : AsyncRepository<OutboxMessage>, IOutboxMessagesRepository
{
    private readonly ApplicationDbContext _appDbContext;

    public OutboxMessageRepository(ApplicationDbContext appDbContext) : base(appDbContext)
    {
        _appDbContext = appDbContext;
    }

    public async override Task<IEnumerable<OutboxMessage>> GetAllAsync()
    {
        return await _appDbContext.OutboxMessages
                                  .Include(o => o.Event)
                                  .ToListAsync();
    }

    public async Task<bool> AnyAsync()
        => await _appDbContext.OutboxMessages.AnyAsync();

    public async Task<List<OutboxMessage>> GeOutboxMessageAsync(int count)
        => await _appDbContext.OutboxMessages.Include(o => o.Event).Take(count).ToListAsync();
}
```

---

## IServiceBusPublisher

```csharp
namespace {Company}.{Domain}.Commands.Application.Contracts.Services.ServiceBus;

public interface IServiceBusPublisher
{
    void StartPublish();
}
```

---

## ServiceBusPublisher Implementation

Full implementation of the singleton publisher with lock, Task.Run, and batch processing.

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

    private static readonly object _lockObject = new();
    private int lockedScopes;

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

    public void StartPublish()
    {
        // Don't wait.
        Task.Run(PublishNonPublishedMessages);
    }

    private void PublishNonPublishedMessages()
    {
        _logger.LogInformation("Publishing to service bus requested.");

        if (lockedScopes > 2)
            return;

        lockedScopes++;

        _logger.LogWarning(
            "Thread attempting to lock a scope in publisher with locked scopes = {LockedScopes}",
            lockedScopes);

        try
        {
            lock (_lockObject)
            {
                using var scope = _serviceProvider.CreateScope();

                var unitOfWork = scope.ServiceProvider.GetRequiredService<IUnitOfWork>();

                while (unitOfWork.OutboxMessages.AnyAsync().GetAwaiter().GetResult())
                {
                    var messages = unitOfWork.OutboxMessages
                        .GeOutboxMessageAsync(200).GetAwaiter().GetResult();

                    _logger.LogInformation("Fetched Message From outbox {Count}", messages.Count);

                    PublishAndRemoveMessagesAsync(messages, unitOfWork).GetAwaiter().GetResult();
                }
            }
        }
        catch (Exception e)
        {
            _logger.LogCritical(e, "Message published failed while attempting to send messages");
        }
        finally
        {
            lockedScopes--;
            _logger.LogWarning(
                "Thread let go of the lock in publisher with locked scopes = {LockedScopes}",
                lockedScopes);
        }
    }

    private async Task PublishAndRemoveMessagesAsync(
        IEnumerable<OutboxMessage> messages, IUnitOfWork unitOfWork)
    {
        foreach (var message in messages)
        {
            await SendMessageAsync(message.Event!);

            await unitOfWork.OutboxMessages.RemoveAsync(message);

            await unitOfWork.SaveChangesAsync();
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

### Publisher Architecture Details

| Aspect | Detail |
|--------|--------|
| Lifetime | Singleton |
| Trigger | `StartPublish()` called by CommitEventService after save |
| Threading | `Task.Run(PublishNonPublishedMessages)` -- fire-and-forget |
| Concurrency | `lock (_lockObject)` + `lockedScopes` counter (max 2 pending) |
| Scope | Creates its own `IServiceProvider.CreateScope()` for IUnitOfWork |
| Batch size | 200 via `GeOutboxMessageAsync(200)` |
| Processing | While loop until no more outbox messages |
| Per-message | Send to Service Bus, remove from DB, save -- one at a time |
| Error | `LogCritical` on exception, decrement `lockedScopes` in `finally` |

### Service Bus Message Properties

| Property | Value | Purpose |
|----------|-------|---------|
| SessionId | `@event.AggregateId.ToString()` | Ordered processing per aggregate |
| PartitionKey | `@event.AggregateId.ToString()` | Partitioning |
| Subject | `@event.Type.ToString()` | Event type for routing |
| CorrelationId | `@event.Id.ToString()` | Tracing |
| MessageId | `@event.Id.ToString()` | Deduplication |
| Body | `JsonConvert.SerializeObject(body)` as UTF8 bytes | Event payload |
| ApplicationProperties | AggregateId, Sequence, Version | Additional metadata |

---

## DI Registration

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

| Service | Lifetime | Reason |
|---------|----------|--------|
| UnitOfWork | Scoped | Tied to DbContext lifetime |
| ServiceBusPublisher | Singleton | Holds lock state, persists across requests |
| ServiceBusClient | Singleton | Connection pooling |
| CommitEventService | Scoped | Uses scoped IUnitOfWork |

---

## Key Differences from Typical Outbox Patterns

1. **No Body column**: OutboxMessage wraps Event via FK, not by serializing the event body
2. **No BackgroundService**: Publisher is a singleton triggered by `StartPublish()`, not a polling background service
3. **Delete after publish**: Published messages are removed from the outbox, not marked with `PublishedAt`
4. **Lock-based concurrency**: Uses `lock` + `lockedScopes` counter, not `SemaphoreSlim`
5. **Synchronous within lock**: Uses `.GetAwaiter().GetResult()` inside the lock block
6. **Per-message save**: Each message is removed and saved individually, not batch-removed

---

## Related Documents

- `knowledge/event-sourcing-flow.md` -- Complete flow overview
- `knowledge/service-bus-patterns.md` -- Azure Service Bus configuration
- `knowledge/dead-letter-reprocessing.md` -- Handling failed messages
