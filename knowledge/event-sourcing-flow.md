# Event Sourcing Flow

Complete end-to-end event sourcing flow for CQRS microservice architecture.
Covers the full lifecycle: Command Handler -> Aggregate -> Event -> CommitEventService -> Outbox -> ServiceBusPublisher -> Query Handler.

---

## Architecture Overview

```
+---------------------------------------------------------------------------+
|                           COMMAND SIDE                                     |
|                                                                           |
|  gRPC Request                                                             |
|      |                                                                    |
|      v                                                                    |
|  +----------+    +-----------+    +------------------+                    |
|  | MediatR  |--->| Command   |--->|    Aggregate     |                    |
|  | Pipeline |    | Handler   |    | (ApplyChange)    |                    |
|  +----------+    +-----------+    +------------------+                    |
|                       |                    |                               |
|                       |           GetUncommittedEvents()                   |
|                       v                    |                               |
|              +-----------------+           |                               |
|              | CommitEventSvc  |<----------+                               |
|              | (IUnitOfWork)   |                                           |
|              +--------+--------+                                          |
|                       |                                                   |
|           +-----------+-----------+                                       |
|           v                       v                                       |
|     +------------+      +--------------+                                  |
|     | Events     |      | OutboxMessage|                                  |
|     | (DB Table) |      | (DB Table)   |                                  |
|     +------------+      +------+-------+                                  |
|                                |                                          |
|                    MarkChangesAsCommitted()                                |
|                                |                                          |
|                    StartPublish() [fire-and-forget]                        |
|                                |                                          |
|                    +-----------v-----------+                               |
|                    | ServiceBusPublisher   |                               |
|                    | (Singleton, Task.Run) |                               |
|                    | lock + CreateScope    |                               |
|                    +-----------+-----------+                               |
|                                |                                          |
+--------------------------------|------------------------------------------+
                                 |
                       Azure Service Bus
                       (Topic/Subscription)
                                 |
+--------------------------------|------------------------------------------+
|                                |           QUERY SIDE                      |
|                                v                                          |
|                    +-----------+-----------+                               |
|                    | ServiceBusListener    |                               |
|                    | (SessionProcessor)    |                               |
|                    +-----------+-----------+                               |
|                                |                                          |
|                                v                                          |
|                    +-------------------+                                   |
|                    | EventDeserializer |                                   |
|                    | (Subject->Type)   |                                   |
|                    +---------+---------+                                   |
|                              |                                            |
|                              v                                            |
|                    +--------------+    +---------------+                   |
|                    |   MediatR    |--->| Event Handler |                   |
|                    |   .Send()    |    | (Projection)  |                   |
|                    +--------------+    +-------+-------+                   |
|                                                |                          |
|                                                v                          |
|                                       +--------------+                    |
|                                       |  Query DB    |                    |
|                                       | (Projection) |                    |
|                                       +--------------+                    |
+--------------------------------------------- ----------------------------+
```

---

## Step 1: Event Hierarchy

Events follow a class hierarchy: abstract `Event` base -> generic `Event<TData>` -> concrete event classes.

### Abstract Event Base

```csharp
public abstract class Event
{
    public long Id { get; protected set; }
    public Guid AggregateId { get; protected set; }
    public int Sequence { get; protected set; }
    public Guid? UserId { get; protected set; }
    public EventType Type { get; protected set; }
    public DateTime DateTime { get; protected set; }
    public int Version { get; protected set; }
}
```

### Generic Event with Typed Data

```csharp
public abstract class Event<TData> : Event
    where TData : IEventData
{
    protected Event(
        Guid aggregateId,
        int sequence,
        Guid? userId,
        TData data,
        int version = 1)
    {
        AggregateId = aggregateId;
        Sequence = sequence;
        UserId = userId;
        Type = data.Type;
        Data = data;
        DateTime = DateTime.UtcNow;
        Version = version;
    }

    public TData Data { get; protected set; }
}
```

### IEventData Interface

```csharp
using System.Text.Json.Serialization;

public interface IEventData
{
    [JsonIgnore]
    EventType Type { get; }
}
```

### Concrete Event + Data

```csharp
// Event class with primary constructor
public class OrderCreated(
    Guid aggregateId,
    Guid? userId,
    OrderCreatedData data,
    int sequence = 1,
    int version = 1) : Event<OrderCreatedData>(aggregateId, sequence, userId, data, version)
{
}

// Event data as immutable record
public record OrderCreatedData(
    string CustomerName,
    decimal Total,
    List<Guid> Items
) : IEventData
{
    public EventType Type => EventType.OrderCreated;
}
```

---

## Step 2: Aggregate

Aggregates enforce business invariants and produce events. The base class provides event replay via static `LoadFromHistory` and new event application via `ApplyChange`.

```csharp
public abstract class Aggregate<T>
{
    private readonly List<Event> _uncommittedEvents = new();

    public Guid Id { get; protected set; }
    public int Sequence { get; internal set; }

    public IReadOnlyList<Event> GetUncommittedEvents() => _uncommittedEvents;
    public void MarkChangesAsCommitted() => _uncommittedEvents.Clear();

    public static T LoadFromHistory(IEnumerable<Event> history)
    {
        if (!history.Any())
            throw new ArgumentOutOfRangeException(nameof(history), "history.Count == 0");

        var aggregate = (T?)Activator.CreateInstance(typeof(T), nonPublic: true)
                ?? throw new NullReferenceException("Unable to generate aggregate entity");

        foreach (var e in history)
        {
            ((dynamic)aggregate).ApplyChange(e, false);
        }

        return aggregate;
    }

    protected void ApplyChange(dynamic @event, bool isNew = true)
    {
        if (@event.Sequence == 1)
        {
            Id = @event.AggregateId;
        }

        Sequence++;

        if (Id == Guid.Empty)
            throw new InvalidOperationException("Id == Guid.Empty");

        if (@event.Sequence != Sequence)
            throw new InvalidOperationException("@event.Sequence != Sequence");

        ((dynamic)this).Apply(@event);

        if (isNew)
            _uncommittedEvents.Add(@event);
    }
}
```

### Concrete Aggregate

```csharp
public class Order : Aggregate<Order>
{
    public string CustomerName { get; private set; } = null!;
    public decimal Total { get; private set; }
    private List<Guid> _items = [];
    public IReadOnlyCollection<Guid> Items => _items;

    // Factory method -- creation events always have sequence 1
    public static Order Create(ICreateOrderCommand command)
    {
        var order = new Order();
        var @event = command.ToEvent();  // Extension method creates the event
        order.ApplyChange(@event);
        return order;
    }

    // Typed Apply overload -- dynamic dispatch routes here
    public void Apply(OrderCreated @event)
    {
        CustomerName = @event.Data.CustomerName;
        Total = @event.Data.Total;
        _items = @event.Data.Items;
    }

    // Business method -- pass Sequence + 1 for non-creation events
    public void AddItems(IAddItemsCommand command)
    {
        if (command.Items.All(_items.Contains))
            throw new ItemAlreadyAddedException(command.UserId);

        var @event = command.ToEvent(sequence: Sequence + 1, _items);
        ApplyChange(@event);
    }

    public void Apply(OrderItemsAdded @event)
    {
        _items.AddRange(@event.Data.Items);
    }
}
```

---

## Step 3: Command Handler

Handlers orchestrate the flow: load or create aggregate, apply business rules, commit.

```csharp
// Create handler -- checks aggregate does NOT exist
public class CreateOrderHandler(IUnitOfWork unitOfWork, ICommitEventService commitEventsService)
    : IRequestHandler<CreateOrderCommand>
{
    private readonly IUnitOfWork _unitOfWork = unitOfWork;
    private readonly ICommitEventService _commitEventsService = commitEventsService;

    public async Task Handle(CreateOrderCommand request, CancellationToken cancellationToken)
    {
        var events = await _unitOfWork.Events
            .GetAllByAggregateIdAsync(request.Id, cancellationToken);

        if (events.Any())
            throw new OrderAlreadyExistException();

        var order = Order.Create(request);

        await _commitEventsService.CommitNewEventsAsync(order);
    }
}

// Update handler -- checks aggregate DOES exist, loads from history
public class AddItemsHandler(ICommitEventService commitEventsService, IUnitOfWork _unitOfWork)
    : IRequestHandler<AddItemsToOrderCommand>
{
    private readonly ICommitEventService _commitEventsService = commitEventsService;

    public async Task Handle(AddItemsToOrderCommand command, CancellationToken cancellationToken)
    {
        var events = await _unitOfWork.Events
            .GetAllByAggregateIdAsync(command.OrderId, cancellationToken);

        if (!events.Any())
            throw new OrderNotFoundException(command.UserId);

        var order = Order.LoadFromHistory(events);

        order.AddItems(command);

        await _commitEventsService.CommitNewEventsAsync(order);
    }
}
```

---

## Step 4: CommitEventService (Transactional Save)

Saves events and outbox messages via IUnitOfWork in a single `SaveChangesAsync` call, then signals the publisher.

```csharp
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
1. Get uncommitted events from the aggregate
2. Add events to the Events repository via UnitOfWork
3. Create OutboxMessage wrappers for each event via `OutboxMessage.ToManyMessages`
4. Add outbox messages to the OutboxMessages repository
5. `SaveChangesAsync` persists both events and outbox messages atomically
6. Clear uncommitted events from the aggregate
7. Signal `StartPublish()` (fire-and-forget)

---

## Step 5: ServiceBusPublisher (Fire-and-Forget)

A singleton service that publishes outbox messages to Azure Service Bus. Uses `Task.Run` (fire-and-forget), `lock` for thread safety, and creates its own DI scope for database access.

```csharp
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
        Task.Run(PublishNonPublishedMessages);
    }

    private void PublishNonPublishedMessages()
    {
        if (lockedScopes > 2)
            return;

        lockedScopes++;

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

                    PublishAndRemoveMessagesAsync(messages, unitOfWork)
                        .GetAwaiter().GetResult();
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

Key details:
- **Singleton** -- persists across requests, holds lock state
- `StartPublish()` calls `Task.Run(PublishNonPublishedMessages)` -- fire-and-forget
- `lockedScopes > 2` guard prevents too many queued threads
- `lock (_lockObject)` ensures only one thread publishes at a time
- Creates its own scope for `IUnitOfWork` access (singleton cannot inject scoped services)
- Reads outbox in batches of 200 via `GeOutboxMessageAsync(200)`
- For each message: send to Service Bus, remove from outbox, save -- one at a time
- The `MessageBody` wrapper extracts event metadata and `((dynamic)@event).Data` for the body
- `SessionId` and `PartitionKey` are set to `AggregateId` for ordered processing

---

## Step 6: OutboxMessage Entity

```csharp
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

OutboxMessage wraps Event via FK (shared primary key). It does NOT serialize the event body -- the publisher reads the Event navigation property at publish time.

---

## Step 7: Service Bus Message Properties

| Service Bus Property | Value | Purpose |
|---------------------|-------|---------|
| SessionId | AggregateId.ToString() | Ordered processing per aggregate |
| PartitionKey | AggregateId.ToString() | Partitioning |
| Subject | EventType.ToString() | Event routing on query side |
| CorrelationId | Event.Id.ToString() | Tracing |
| MessageId | Event.Id.ToString() | Deduplication |
| Body | JSON serialized MessageBody | Event data payload |
| ApplicationProperties | AggregateId, Sequence, Version | Additional metadata |

---

## Step 8: Service Bus Listener (Query Side)

The query side listens using session processors. Sessions ensure ordered processing per aggregate.

```csharp
public sealed class OrderEventListener(
    ServiceBusClient client,
    IServiceScopeFactory scopeFactory,
    ILogger<OrderEventListener> logger) : IHostedService
{
    private ServiceBusSessionProcessor? _processor;

    public async Task StartAsync(CancellationToken ct)
    {
        _processor = client.CreateSessionProcessor(
            topicName, subscriptionName,
            new ServiceBusSessionProcessorOptions
            {
                MaxConcurrentSessions = 10,
                SessionIdleTimeout = TimeSpan.FromSeconds(5)
            });

        _processor.ProcessMessageAsync += ProcessMessageAsync;
        _processor.ProcessErrorAsync += ProcessErrorAsync;
        await _processor.StartProcessingAsync(ct);
    }

    private async Task ProcessMessageAsync(ProcessSessionMessageEventArgs args)
    {
        using var scope = scopeFactory.CreateScope();
        var mediator = scope.ServiceProvider.GetRequiredService<IMediator>();

        var eventType = args.Message.Subject;
        var body = args.Message.Body.ToString();

        var @event = EventDeserializer.Deserialize(eventType, body);
        var result = await mediator.Send(@event);

        if (result is true)
            await args.CompleteMessageAsync(args.Message);
        else
            await args.AbandonMessageAsync(args.Message);
    }
}
```

---

## Key Guarantees

1. **Atomic save**: Events and outbox messages are saved in a single `SaveChangesAsync` call via IUnitOfWork
2. **At-least-once delivery**: The outbox pattern guarantees every committed event is eventually published
3. **Ordered per aggregate**: Service Bus sessions (keyed by AggregateId) ensure events arrive in order
4. **Idempotent consumers**: Query-side handlers check sequence numbers to skip already-processed events
5. **No data loss**: Events are never deleted from the event store; outbox messages are deleted after publish

---

## DI Registration

```csharp
// ApplicationContainer (Application layer)
public static class ApplicationContainer
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddMediatR(m => m.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly()));
        return services;
    }
}

// InfraContainer (Infrastructure layer)
public static class InfraContainer
{
    public static IServiceCollection AddInfraServices(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddSqlDb(configuration);
        services.AddScoped<IUnitOfWork, UnitOfWork>();
        services.AddSingleton<IServiceBusPublisher, ServiceBusPublisher>();
        services.AddSingleton(s =>
        {
            return new ServiceBusClient(configuration.GetConnectionString("ServiceBus"));
        });
        services.AddScoped<ICommitEventService, CommitEventService>();
        return services;
    }
}
```

---

## Related Documents

- `knowledge/outbox-pattern.md` -- Detailed outbox pattern implementation
- `knowledge/service-bus-patterns.md` -- Azure Service Bus configuration
- `knowledge/event-versioning.md` -- Event schema evolution
- `knowledge/concurrency-patterns.md` -- Sequence-based idempotency
- `knowledge/dead-letter-reprocessing.md` -- Handling failed messages
