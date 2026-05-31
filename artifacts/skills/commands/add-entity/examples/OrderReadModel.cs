using Sample.Domain.Events;

namespace Sample.Query.ReadModels;

// Query-side read model: a denormalized projection of command-side events.
// Every property has a private setter; state changes only through Apply(...) updaters.
// Sequence tracks the last applied event for idempotent projection.
public class OrderReadModel
{
    // Projection constructor — builds the read model from the creation event.
    public OrderReadModel(OrderPlaced @event)
    {
        Id = @event.OrderId;
        CustomerName = @event.CustomerName;
        Total = @event.Total;
        Status = "Pending";
        Sequence = 1;
        UpdatedAt = @event.OccurredOn.UtcDateTime;
    }

    // Private all-args constructor used by EF Core to materialize rows.
    private OrderReadModel(
        Guid id,
        string customerName,
        decimal total,
        string status,
        int sequence,
        DateTime updatedAt)
    {
        Id = id;
        CustomerName = customerName;
        Total = total;
        Status = status;
        Sequence = sequence;
        UpdatedAt = updatedAt;
    }

    public Guid Id { get; private set; }
    public string CustomerName { get; private set; }
    public decimal Total { get; private set; }
    public string Status { get; private set; }
    public int Sequence { get; private set; }
    public DateTime UpdatedAt { get; private set; }

    // Event updater: projects a state-change event and advances the sequence.
    public void Apply(OrderCompleted @event, int sequence)
    {
        Status = "Completed";
        Sequence = sequence;
        UpdatedAt = @event.OccurredOn.UtcDateTime;
    }
}
