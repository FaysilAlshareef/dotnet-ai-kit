using MediatR;

namespace {{ Company }}.{{ ProjectName }}.Shared.Events;

/// <summary>
/// Marker interface for cross-module integration events.
/// Published via MediatR INotification for loose coupling between modules.
/// </summary>
public interface IIntegrationEvent : INotification
{
    Guid EventId { get; }
    DateTime OccurredOn { get; }
}
