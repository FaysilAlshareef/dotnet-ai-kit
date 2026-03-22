using MediatR;

namespace {{ Company }}.{{ ProjectName }}.Domain.Common;

public abstract record DomainEvent : INotification
{
    public Guid EventId { get; init; } = Guid.NewGuid();
    public DateTime OccurredOn { get; init; } = DateTime.UtcNow;
}
