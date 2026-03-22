using {{ Company }}.{{ Domain }}.Commands.Domain.Events;

namespace {{ Company }}.{{ Domain }}.Commands.Domain.Core;

public abstract class Aggregate<T>
{
    private readonly List<Event> _uncommittedEvents = new();

    public Guid Id { get; protected set; }
    public int Sequence { get; internal set; }

    public IReadOnlyList<Event> GetUncommittedEvents() => _uncommittedEvents;
    public void MarkChangesAsCommitted() => _uncommittedEvents.Clear();

    public static T LoadFromHistory(IEnumerable<Event> history)
    {
        if (!history.Any())
            throw new ArgumentOutOfRangeException(nameof(history), "history.Count == 0");

        var aggregate = (T?)Activator.CreateInstance(typeof(T), nonPublic: true)
                ?? throw new NullReferenceException("Unable to generate aggregate entity");

        foreach (var e in history)
        {
            ((dynamic)aggregate).ApplyChange(e, false);
        }

        return aggregate;
    }

    protected void ApplyChange(dynamic @event, bool isNew = true)
    {
        if (@event.Sequence == 1)
        {
            Id = @event.AggregateId;
        }

        Sequence++;

        if (Id == Guid.Empty)
            throw new InvalidOperationException("Id == Guid.Empty");

        if (@event.Sequence != Sequence)
            throw new InvalidOperationException("@event.Sequence != Sequence");

        ((dynamic)this).Apply(@event);

        if (isNew)
            _uncommittedEvents.Add(@event);
    }
}
