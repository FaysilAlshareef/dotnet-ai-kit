namespace Sample.Domain.Events;

// Marker interface for domain events. Every event carries when it occurred and
// the id of the aggregate that produced it.
public interface IDomainEvent
{
    Guid AggregateId { get; }
    DateTimeOffset OccurredOn { get; }
}

// Domain event records are immutable. Positional parameters capture the payload;
// OccurredOn is set once at construction (a non-constant default lives in the body,
// never as a positional default).
public sealed record OrderPlaced(Guid OrderId, string CustomerName, decimal Total) : IDomainEvent
{
    public Guid AggregateId => OrderId;

    public DateTimeOffset OccurredOn { get; init; } = DateTimeOffset.UtcNow;
}

public sealed record OrderCompleted(Guid OrderId) : IDomainEvent
{
    public Guid AggregateId => OrderId;

    public DateTimeOffset OccurredOn { get; init; } = DateTimeOffset.UtcNow;
}
