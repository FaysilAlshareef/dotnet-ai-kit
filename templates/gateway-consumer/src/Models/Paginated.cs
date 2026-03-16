namespace {{ Company }}.Gateways.{{ Domain }}.Consumers.Models;

public class Paginated<T>
{
    public List<T> Items { get; init; } = [];
    public int TotalCount { get; init; }
    public int PageNumber { get; init; }
    public int PageSize { get; init; }
    public bool HasNextPage => PageNumber * PageSize < TotalCount;
}
