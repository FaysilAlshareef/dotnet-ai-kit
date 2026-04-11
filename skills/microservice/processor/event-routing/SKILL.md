---
name: event-routing
description: >
  Use when routing Service Bus events by subject to typed MediatR handlers.
metadata:
  category: microservice/processor
  agent: processor-architect
  when-to-use: "When implementing subject-based event routing or inline HandleAsync dispatch"
---

# Event Routing — Subject-Based Inline Dispatch

## Core Principles

- Routing is INLINE in each listener class (no separate IEventRouter or EventDeserializer)
- `HandleSubject()` method uses a switch expression on `message.Subject`
- Each case calls a typed `HandleAsync<TEventData>(message)` method
- `HandleAsync<T>` deserializes `Event<T>` from JSON body, creates a DI scope, and calls `IMediator.Send()`
- Returns `bool`: `true` = complete message, `false` = abandon message
- Unknown subjects return `Task.FromResult(true)` to complete (not retry)
- `LogContext.Push` with `PropertyEnricher` for EventType, SessionId, MessageId

## Key Patterns

### Subject-Based Switch in Listener

```csharp
// Inside the listener class (e.g., OrderListener)
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

### Event Type Constants

```csharp
namespace {Company}.{Domain}.Processor.Infra.ServiceBus.Constants;

public class EventType
{
    public const string OrderCreated = "OrderCreated";
    public const string OrderUpdated = "OrderUpdated";
    public const string OrderCompleted = "OrderCompleted";
}

// Separate constants class per source domain
public static class AccountEventType
{
    public const string AccountConfirmed = "AccountConfirmed";
    public const string AccountUpdated = "AccountUpdated";
    public const string SubscriptionCreated = "SubscriptionCreated";
    public const string SubscriptionRemoved = "SubscriptionRemoved";
}
```

### HandleAsync with Serilog Enrichment

```csharp
// Inside the listener class
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

private async Task<bool> SendAsync<T>(IMediator mediator, Event<T> @event)
{
    var result = await mediator.Send(@event);

    if (!result)
        _logger.LogWarning(
            "Event Not Handling With Aggregate : {id}, Type : {type} and sequence : {sequence}",
            @event.AggregateId,
            @event.Type,
            @event.Sequence);

    return result;
}
```

### Event<T> Envelope

```csharp
namespace {Company}.{Domain}.Processor.Events;

public class Event<T> : IRequest<bool>
{
    public required Guid AggregateId { get; init; }
    public required Guid? UserId { get; init; }
    public required int Sequence { get; init; }
    public required string Type { get; init; }
    public required T Data { get; init; }
    public required DateTime DateTime { get; set; }
    public required int Version { get; init; }

    public string GetDataAsJson() =>
        JsonConvert.SerializeObject(Data, new JsonSerializerSettings()
        {
            Formatting = Formatting.Indented,
            NullValueHandling = NullValueHandling.Ignore,
            ContractResolver = new CamelCasePropertyNamesContractResolver()
        });
}
```

### ProcessMessageAsync Calls HandleSubject

```csharp
// Main processor handler (ProcessSessionMessageEventArgs)
private async Task Processor_ProcessMessageAsync(ProcessSessionMessageEventArgs arg)
{
    Task<bool> isHandledTask = HandleSubject(arg.Message.Subject, arg.Message);

    var isHandled = await isHandledTask;

    if (isHandled)
        await arg.CompleteMessageAsync(arg.Message);
    else
        await arg.AbandonMessageAsync(arg.Message);
}

// DLQ processor handler (ProcessMessageEventArgs -- different type, no session)
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

### Multi-Source Listener Example

```csharp
// A listener consuming events from a different domain
private Task<bool> HandleSubject(string subject, ServiceBusReceivedMessage message)
{
    return subject switch
    {
        AccountEventType.AccountConfirmed => HandleAsync<AccountConfirmedData>(message),
        AccountEventType.AccountUpdated => HandleAsync<AccountUpdatedData>(message),
        AccountEventType.SubscriptionCreated => HandleAsync<SubscriptionCreatedData>(message),
        AccountEventType.SubscriptionRemoved => HandleAsync<SubscriptionRemovedData>(message),
        _ => Task.FromResult(true) // Ignore unknown events
    };
}
```

## Complete Flow

```
ServiceBusSessionProcessor
  -> ProcessMessageAsync(ProcessSessionMessageEventArgs arg)
    -> HandleSubject(arg.Message.Subject, arg.Message)
      -> switch on Subject string
        -> HandleAsync<TEventData>(message)
          -> PropertyEnricher (EventType, SessionId, MessageId)
          -> LogContext.Push(...)
          -> Encoding.UTF8.GetString(message.Body)
          -> JsonConvert.DeserializeObject<Event<T>>(json)
          -> _provider.CreateScope()
          -> scope.GetRequiredService<IMediator>()
          -> mediator.Send(@event)
    -> if true: CompleteMessageAsync
    -> if false: AbandonMessageAsync
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Separate EventRouter/EventDeserializer class | Inline HandleSubject + HandleAsync in each listener |
| Using LogContext.PushProperty | Use LogContext.Push with PropertyEnricher instances |
| Retrying unknown event types | Return Task.FromResult(true) for unknown subjects |
| Getting body via message.Body.ToString() | Use Encoding.UTF8.GetString(message.Body) |
| Using System.Text.Json | Use Newtonsoft.Json (JsonConvert.DeserializeObject) |
| Creating mediator outside scope | Create DI scope, then resolve IMediator from scope |

## Detect Existing Patterns

```bash
# Find subject-based routing
grep -r "Subject\|HandleSubject\|HandelSubject" --include="*.cs" src/

# Find HandleAsync methods
grep -r "HandleAsync<" --include="*.cs" src/

# Find LogContext.Push usage
grep -r "LogContext.Push" --include="*.cs" src/

# Find PropertyEnricher usage
grep -r "PropertyEnricher" --include="*.cs" src/
```

## Adding to Existing Project

1. **Add new event type constant** to the appropriate constants class
2. **Create event data class** in `Events/Incoming/{SourceDomain}/`
3. **Add case to HandleSubject switch** in the relevant listener
4. **Create MediatR handler** implementing `IRequestHandler<Event<TData>, bool>`
5. **Follow existing LogContext enrichment** -- always push EventType, SessionId, MessageId
