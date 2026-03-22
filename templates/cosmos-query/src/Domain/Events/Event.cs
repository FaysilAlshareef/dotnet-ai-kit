namespace {{ Company }}.{{ Domain }}.Queries.Domain.Events;

public class Event<TData> where TData : IEventData
{
    public Guid Id { get; init; }
    public Guid AggregateId { get; init; }
    public int Sequence { get; init; }
    public string Type { get; init; } = default!;
    public TData Data { get; init; } = default!;
    public DateTime DateTime { get; init; }
    public int Version { get; init; }
}

public interface IEventData { }
