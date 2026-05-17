namespace MeasurementSvc.Domain.Orders;

public sealed record Order(Guid Id, decimal Total)
{
    public static Order Create(decimal total) => new(Guid.NewGuid(), total);
}
