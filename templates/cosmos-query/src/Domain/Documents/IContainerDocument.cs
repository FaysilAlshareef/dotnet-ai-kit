namespace {{ Company }}.{{ Domain }}.Queries.Domain.Documents;

public interface IContainerDocument
{
    string Id { get; }
    string Discriminator { get; }
    string PartitionKey1 { get; }
    string PartitionKey2 { get; }
    string PartitionKey3 { get; }
    string? ETag { get; set; }
    bool IsReport { get; }
}
