namespace MeasurementSvc.Application.Orders;

public interface IOrderQueries
{
    Task<OrderReadModel?> GetAsync(Guid id, CancellationToken ct = default);
}

public sealed record OrderReadModel(Guid Id, decimal Total);
