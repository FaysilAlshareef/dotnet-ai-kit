using {{ Company }}.{{ Domain }}.Commands.Domain.Enums;
using {{ Company }}.{{ Domain }}.Commands.Domain.Events.DataTypes;

namespace {{ Company }}.{{ Domain }}.Commands.Domain.Events;

public abstract class Event
{
    public long Id { get; protected set; }
    public Guid AggregateId { get; protected set; }
    public int Sequence { get; protected set; }
    public Guid? UserId { get; protected set; }
    public EventType Type { get; protected set; }
    public DateTime DateTime { get; protected set; }
    public int Version { get; protected set; }
}

public abstract class Event<TData> : Event
    where TData : IEventData
{
    protected Event(
        Guid aggregateId,
        int sequence,
        Guid? userId,
        TData data,
        int version = 1
    )
    {
        AggregateId = aggregateId;
        Sequence = sequence;
        UserId = userId;
        Type = data.Type;
        Data = data;
        DateTime = DateTime.UtcNow;
        Version = version;
    }

    public TData Data { get; protected set; }
}
