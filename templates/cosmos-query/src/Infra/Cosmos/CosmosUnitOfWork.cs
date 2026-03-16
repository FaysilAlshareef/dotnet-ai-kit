using Microsoft.Azure.Cosmos;
using {{ Company }}.{{ Domain }}.Queries.Domain.Documents;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Cosmos;

public class CosmosUnitOfWork(Container container)
{
    private readonly List<(IContainerDocument Doc, OperationType Op)> _operations = [];

    public void Insert(IContainerDocument doc) => _operations.Add((doc, OperationType.Create));
    public void Replace(IContainerDocument doc) => _operations.Add((doc, OperationType.Replace));
    public void Upsert(IContainerDocument doc) => _operations.Add((doc, OperationType.Upsert));
    public void Remove(IContainerDocument doc) => _operations.Add((doc, OperationType.Delete));

    public async Task CommitAsync()
    {
        if (_operations.Count == 0) return;

        if (_operations.Count == 1)
        {
            var (doc, op) = _operations[0];
            var partitionKey = new PartitionKeyBuilder()
                .Add(doc.PartitionKey1)
                .Add(doc.PartitionKey2)
                .Add(doc.PartitionKey3)
                .Build();

            switch (op)
            {
                case OperationType.Create:
                    await container.CreateItemAsync(doc, partitionKey);
                    break;
                case OperationType.Replace:
                    await container.ReplaceItemAsync(doc, doc.Id, partitionKey,
                        new ItemRequestOptions { IfMatchEtag = doc.ETag });
                    break;
                case OperationType.Upsert:
                    await container.UpsertItemAsync(doc, partitionKey);
                    break;
                case OperationType.Delete:
                    await container.DeleteItemAsync<IContainerDocument>(doc.Id, partitionKey);
                    break;
            }
        }
        else
        {
            // TransactionalBatch for multiple operations
            var first = _operations[0].Doc;
            var partitionKey = new PartitionKeyBuilder()
                .Add(first.PartitionKey1)
                .Add(first.PartitionKey2)
                .Add(first.PartitionKey3)
                .Build();

            var batch = container.CreateTransactionalBatch(partitionKey);
            foreach (var (doc, op) in _operations)
            {
                switch (op)
                {
                    case OperationType.Create:
                        batch.CreateItem(doc);
                        break;
                    case OperationType.Replace:
                        batch.ReplaceItem(doc.Id, doc,
                            new TransactionalBatchItemRequestOptions { IfMatchEtag = doc.ETag });
                        break;
                    case OperationType.Upsert:
                        batch.UpsertItem(doc);
                        break;
                    case OperationType.Delete:
                        batch.DeleteItem(doc.Id);
                        break;
                }
            }

            await batch.ExecuteAsync();
        }

        _operations.Clear();
    }
}
