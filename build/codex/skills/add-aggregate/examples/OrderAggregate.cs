using Sample.Domain.Events;

namespace Sample.Domain.Aggregates;

// Event-sourced aggregate root. State changes are expressed as domain events
// raised through Raise(...) and folded into state by the matching Apply(...) overload.
public sealed class Order : AggregateRoot
{
    public string CustomerName { get; private set; } = null!;
    public decimal Total { get; private set; }
    public OrderStatus Status { get; private set; }

    // Required by the event-replay/factory path; not for public use.
    private Order()
    {
    }

    // Factory method (not a public constructor) creates a new aggregate.
    public static Order Place(Guid id, string customerName, decimal total)
    {
        if (total <= 0m)
            throw new ArgumentOutOfRangeException(nameof(total), "Order total must be positive.");

        var order = new Order();
        order.Raise(new OrderPlaced(id, customerName, total));
        return order;
    }

    // Business method: guards invariants, then raises the event.
    public void Complete()
    {
        if (Status == OrderStatus.Completed)
            throw new InvalidOperationException("Order is already completed.");

        Raise(new OrderCompleted(Id));
    }

    private void Apply(OrderPlaced @event)
    {
        Id = @event.OrderId;
        CustomerName = @event.CustomerName;
        Total = @event.Total;
        Status = OrderStatus.Pending;
    }

    private void Apply(OrderCompleted @event) => Status = OrderStatus.Completed;
}

public enum OrderStatus
{
    Pending,
    Completed,
}
