namespace {{ Company }}.{{ ProjectName }}.Domain.Common;

public abstract class AggregateRoot<TId> : Entity<TId> where TId : StronglyTypedId
{
    private readonly List<DomainEvent> _domainEvents = [];
    public IReadOnlyList<DomainEvent> DomainEvents => _domainEvents;

    protected void RaiseDomainEvent(DomainEvent @event) => _domainEvents.Add(@event);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
