using Microsoft.Azure.Cosmos;
using Microsoft.Azure.Cosmos.Linq;
using {{ Company }}.{{ Domain }}.Queries.Domain.Documents;

namespace {{ Company }}.{{ Domain }}.Queries.Infra.Cosmos;

public class CosmosRepository(Container container)
{
    public async Task<T?> GetByIdAsync<T>(string id, PartitionKey partitionKey)
        where T : IContainerDocument
    {
        try
        {
            var response = await container.ReadItemAsync<T>(id, partitionKey);
            return response.Resource;
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return default;
        }
    }

    public async Task<List<T>> QueryAsync<T>(Func<IQueryable<T>, IQueryable<T>> query)
        where T : IContainerDocument
    {
        var results = new List<T>();
        var queryable = query(container.GetItemLinqQueryable<T>());
        using var iterator = queryable.ToFeedIterator();

        while (iterator.HasMoreResults)
        {
            var response = await iterator.ReadNextAsync();
            results.AddRange(response);
        }

        return results;
    }
}
