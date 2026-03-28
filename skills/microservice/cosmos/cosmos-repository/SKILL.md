---
name: cosmos-repository
description: >
  Cosmos DB repository pattern with LINQ queries, FeedIterator for pagination,
  point reads, and RU monitoring. Covers container-based data access patterns.
  Trigger: cosmos repository, LINQ query, FeedIterator, point read, RU.
metadata:
  category: microservice/cosmos
  agent: cosmos-architect
---

# Cosmos Repository — LINQ Queries & Data Access

## Core Principles

- One repository per container (not per entity type)
- Point reads (`ReadItemAsync`) are the most efficient operation
- LINQ queries via `GetItemLinqQueryable<T>()` with discriminator filtering
- `FeedIterator` for paginating large result sets
- Monitor Request Unit (RU) charges from response headers
- Cross-partition queries are expensive — avoid when possible

## Key Patterns

### Generic Cosmos Repository

```csharp
namespace {Company}.{Domain}.Cosmos.Infrastructure;

public sealed class CosmosRepository<T>(
    Container container,
    ILogger<CosmosRepository<T>> logger) where T : IContainerDocument
{
    public async Task<T?> GetByIdAsync(
        string id, PartitionKey pk, CancellationToken ct)
    {
        try
        {
            var response = await container.ReadItemAsync<T>(
                id, pk, cancellationToken: ct);

            logger.LogDebug("Point read: {RU} RUs", response.RequestCharge);
            return response.Resource;
        }
        catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            return default;
        }
    }

    public async Task<List<T>> QueryAsync(
        Expression<Func<T, bool>> predicate,
        PartitionKey? pk = null,
        CancellationToken ct = default)
    {
        var options = new QueryRequestOptions();
        if (pk.HasValue)
            options.PartitionKey = pk.Value;

        var queryable = container.GetItemLinqQueryable<T>(
            requestOptions: options)
            .Where(d => d.Discriminator == typeof(T).Name)
            .Where(predicate);

        using var iterator = queryable.ToFeedIterator();
        var results = new List<T>();
        double totalRU = 0;

        while (iterator.HasMoreResults)
        {
            var response = await iterator.ReadNextAsync(ct);
            results.AddRange(response);
            totalRU += response.RequestCharge;
        }

        logger.LogDebug("Query returned {Count} items, {RU} RUs",
            results.Count, totalRU);
        return results;
    }

    public async Task UpsertAsync(T document, CancellationToken ct)
    {
        var response = await container.UpsertItemAsync(
            document, document.PartitionKeys,
            new ItemRequestOptions { IfMatchEtag = document.ETag },
            ct);

        document.ETag = response.ETag;
        logger.LogDebug("Upsert: {RU} RUs", response.RequestCharge);
    }

    public async Task CreateAsync(T document, CancellationToken ct)
    {
        var response = await container.CreateItemAsync(
            document, document.PartitionKeys, cancellationToken: ct);

        document.ETag = response.ETag;
        logger.LogDebug("Create: {RU} RUs", response.RequestCharge);
    }

    public async Task DeleteAsync(
        string id, PartitionKey pk, CancellationToken ct)
    {
        await container.DeleteItemAsync<T>(id, pk, cancellationToken: ct);
    }
}
```

### Paginated Query with FeedIterator

```csharp
public async Task<(List<T> Items, string? ContinuationToken)> QueryPagedAsync(
    Expression<Func<T, bool>> predicate,
    int pageSize,
    string? continuationToken = null,
    CancellationToken ct = default)
{
    var queryable = container.GetItemLinqQueryable<T>(
        continuationToken: continuationToken,
        requestOptions: new QueryRequestOptions { MaxItemCount = pageSize })
        .Where(d => d.Discriminator == typeof(T).Name)
        .Where(predicate);

    using var iterator = queryable.ToFeedIterator();
    var results = new List<T>();
    string? nextToken = null;

    if (iterator.HasMoreResults)
    {
        var response = await iterator.ReadNextAsync(ct);
        results.AddRange(response);
        nextToken = response.ContinuationToken;
    }

    return (results, nextToken);
}
```

### SQL Query (For Complex Queries)

```csharp
public async Task<List<T>> QuerySqlAsync(
    string sql, Dictionary<string, object> parameters, CancellationToken ct)
{
    var queryDef = new QueryDefinition(sql);
    foreach (var param in parameters)
        queryDef = queryDef.WithParameter($"@{param.Key}", param.Value);

    using var iterator = container.GetItemQueryIterator<T>(queryDef);
    var results = new List<T>();

    while (iterator.HasMoreResults)
    {
        var response = await iterator.ReadNextAsync(ct);
        results.AddRange(response);
    }

    return results;
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Missing discriminator filter | Always filter by Discriminator in queries |
| Cross-partition queries for known PK | Provide partition key when available |
| Not tracking RU charges | Log RU charges for monitoring and optimization |
| Using ReadItemAsync without ETag | Set ETag from read for subsequent updates |
| Large unbounded queries | Use FeedIterator with MaxItemCount for pagination |

## Detect Existing Patterns

```bash
# Find Cosmos repositories
grep -r "CosmosRepository\|Container container" --include="*.cs" src/

# Find LINQ queries
grep -r "GetItemLinqQueryable" --include="*.cs" src/

# Find FeedIterator usage
grep -r "FeedIterator\|ToFeedIterator" --include="*.cs" src/

# Find RU logging
grep -r "RequestCharge" --include="*.cs" src/
```

## Adding to Existing Project

1. **Check if a generic `CosmosRepository<T>` exists** or if repos are per-entity
2. **Match the discriminator filtering** pattern used in existing queries
3. **Follow RU logging conventions** — check existing log levels
4. **Use point reads** (`ReadItemAsync`) wherever possible over queries
5. **Provide partition key** to avoid expensive cross-partition queries
