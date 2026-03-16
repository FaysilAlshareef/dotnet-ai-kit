using {{ Company }}.{{ ProjectName }}.Domain.Common;

namespace {{ Company }}.{{ ProjectName }}.Domain.Interfaces;

public interface IDomainEventDispatcher
{
    Task DispatchEventsAsync(IEnumerable<DomainEvent> events, CancellationToken ct = default);
}
