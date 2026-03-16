using MediatR;
using {{ Company }}.{{ ProjectName }}.Domain.Common;
using {{ Company }}.{{ ProjectName }}.Domain.Interfaces;

namespace {{ Company }}.{{ ProjectName }}.Infrastructure.Data;

/// <summary>
/// Collects domain events from aggregate roots after SaveChanges
/// and publishes them via MediatR as notifications.
/// </summary>
public class DomainEventInterceptor(IMediator mediator) : IDomainEventDispatcher
{
    public async Task DispatchEventsAsync(
        IEnumerable<DomainEvent> events, CancellationToken ct = default)
    {
        foreach (var domainEvent in events)
        {
            await mediator.Publish(domainEvent, ct);
        }
    }
}
