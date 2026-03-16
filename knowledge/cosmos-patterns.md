# Cosmos DB Patterns

Azure Cosmos DB patterns for .NET microservice architecture.
Covers IContainerDocument, partition strategies, transactional batch, LINQ queries, and Service Principal authentication.

---

## IContainerDocument Interface

All Cosmos DB documents implement a common interface for container routing, partition keys, and concurrency.

```csharp
public interface IContainerDocument
{
    /// <summary>Container name where this document type is stored.</summary>
    string ContainerName { get; }

    /// <summary>Hierarchical partition key (up to 3 levels).</summary>
    PartitionKey PartitionKeys { get; }

    /// <summary>Discriminator string for polymorphic containers.</summary>
    string Discriminator { get; }

    /// <summary>ETag for optimistic concurrency.</summary>
    string? ETag { get; set; }
}
```

### Example Document

```csharp
public sealed class MerchantSalesReport : IContainerDocument
{
    // Cosmos DB requires lowercase 'id'
    [JsonProperty("id")]
    public string id { get; set; } = string.Empty;

    public string MerchantId { get; private set; } = string.Empty;
    public string ReportMonth { get; private set; } = string.Empty;
    public decimal TotalSales { get; private set; }
    public int TransactionCount { get; private set; }
    public DateTime LastUpdated { get; private set; }

    // IContainerDocument implementation
    public string ContainerName => "sales-reports";
    public string Discriminator => nameof(MerchantSalesReport);
    public string? ETag { get; set; }

    public PartitionKey PartitionKeys => new PartitionKeyBuilder()
        .Add(MerchantId)
        .Add(ReportMonth)
        .Add(Discriminator)
        .Build();

    // Construction from events
    public MerchantSalesReport(Event<SalesRecordedData> @event)
    {
        id = $"{@event.Data.MerchantId}-{@event.Data.Month}";
        MerchantId = @event.Data.MerchantId;
        ReportMonth = @event.Data.Month;
        TotalSales = @event.Data.Amount;
        TransactionCount = 1;
        LastUpdated = @event.DateTime;
    }

    public void Apply(Event<SalesRecordedData> @event)
    {
        TotalSales += @event.Data.Amount;
        TransactionCount++;
        LastUpdated = @event.DateTime;
    }
}
```

---

## Partition Key Strategy

### Hierarchical Partition Keys (3 Levels)

Cosmos DB supports up to 3 levels of hierarchical partition keys. Choose keys that:

1. Distribute data evenly across logical partitions
2. Are included in most query WHERE clauses
3. Are immutable after document creation

```csharp
// 3-level partition key
public PartitionKey PartitionKeys => new PartitionKeyBuilder()
    .Add(TenantId)       // Level 1: tenant isolation
    .Add(Region)         // Level 2: geographic distribution
    .Add(Discriminator)  // Level 3: document type
    .Build();
```

### Container Configuration with Hierarchical Keys

```csharp
var containerProperties = new ContainerProperties
{
    Id = "sales-reports",
    PartitionKeyPaths = new Collection<string>
    {
        "/merchantId",     // Level 1
        "/reportMonth",    // Level 2
        "/discriminator"   // Level 3
    }
};

await database.CreateContainerIfNotExistsAsync(containerProperties);
```

### Partition Key Selection Guide

| Scenario                  | Recommended Key               | Reason                        |
|---------------------------|-------------------------------|-------------------------------|
| Multi-tenant SaaS         | TenantId                      | Tenant isolation              |
| Per-user data             | UserId                        | User-scoped queries           |
| Time-series data          | Date + DeviceId               | Balanced distribution         |
| Event sourced projections | AggregateId + Discriminator   | All aggregate data co-located |
| Lookup tables             | Category + Discriminator      | Group related items           |

---

## Cosmos Repository

### Generic Repository

```csharp
public sealed class CosmosRepository<T>(Container container)
    where T : class, IContainerDocument
{
    /// <summary>Point read by ID and partition key — most efficient operation.</summary>
    public async Task<T?> GetByIdAsync(
        string id, PartitionKey pk, CancellationToken ct)
    {
        try
        {
            var response = await container.ReadItemAsync<T>(id, pk, cancellationToken: ct);
            var document = response.Resource;
            document.ETag = response.ETag;
            return document;
        }
        catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
    }

    /// <summary>Upsert with optimistic concurrency via ETag.</summary>
    public async Task UpsertAsync(T document, CancellationToken ct)
    {
        var options = new ItemRequestOptions();
        if (document.ETag is not null)
            options.IfMatchEtag = document.ETag;

        var response = await container.UpsertItemAsync(
            document, document.PartitionKeys, options, ct);

        document.ETag = response.ETag;
    }

    /// <summary>Create a new document. Fails if already exists.</summary>
    public async Task CreateAsync(T document, CancellationToken ct)
    {
        var response = await container.CreateItemAsync(
            document, document.PartitionKeys, cancellationToken: ct);
        document.ETag = response.ETag;
    }

    /// <summary>Delete by ID and partition key.</summary>
    public async Task DeleteAsync(
        string id, PartitionKey pk, CancellationToken ct)
    {
        await container.DeleteItemAsync<T>(id, pk, cancellationToken: ct);
    }

    /// <summary>LINQ query with FeedIterator for large result sets.</summary>
    public async Task<List<T>> QueryAsync(
        Expression<Func<T, bool>> predicate,
        CancellationToken ct,
        int? maxItems = null)
    {
        var queryable = container.GetItemLinqQueryable<T>()
            .Where(predicate);

        if (maxItems.HasValue)
            queryable = queryable.Take(maxItems.Value);

        using var iterator = queryable.ToFeedIterator();
        var results = new List<T>();

        while (iterator.HasMoreResults)
        {
            var response = await iterator.ReadNextAsync(ct);
            results.AddRange(response);
        }

        return results;
    }
}
```

### RU Charge Tracking

Monitor Request Unit consumption for cost optimization:

```csharp
public async Task<(T? Document, double RequestCharge)> GetWithChargeAsync(
    string id, PartitionKey pk, CancellationToken ct)
{
    try
    {
        var response = await container.ReadItemAsync<T>(id, pk, cancellationToken: ct);
        return (response.Resource, response.RequestCharge);
    }
    catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
    {
        return (null, ex.RequestCharge);
    }
}
```

---

## Transactional Batch

Atomic multi-document operations within the same partition key.

```csharp
public async Task CommitBatchAsync(
    PartitionKey pk,
    IReadOnlyList<IContainerDocument> documents,
    CancellationToken ct)
{
    // Cosmos DB batch limit: 100 operations per batch
    const int maxBatchSize = 100;

    foreach (var chunk in documents.Chunk(maxBatchSize))
    {
        var batch = container.CreateTransactionalBatch(pk);

        foreach (var doc in chunk)
        {
            if (doc.ETag is null)
            {
                batch.CreateItem(doc);
            }
            else
            {
                batch.UpsertItem(doc, new TransactionalBatchItemRequestOptions
                {
                    IfMatchEtag = doc.ETag
                });
            }
        }

        using var response = await batch.ExecuteAsync(ct);

        if (!response.IsSuccessStatusCode)
        {
            // Find the failing operation
            for (int i = 0; i < response.Count; i++)
            {
                var itemResponse = response[i];
                if (!itemResponse.IsSuccessStatusCode)
                {
                    throw new CosmosException(
                        $"Batch operation {i} failed: {itemResponse.StatusCode}",
                        itemResponse.StatusCode, 0, "", 0);
                }
            }
        }
    }
}
```

### Batch Rules

- All operations must share the same partition key
- Maximum 100 operations per batch
- Maximum 2 MB total payload per batch
- Operations: CreateItem, UpsertItem, ReplaceItem, DeleteItem, ReadItem, PatchItem
- If any operation fails, the entire batch rolls back

---

## LINQ Queries

### Paginated Query

```csharp
public async Task<(List<T> Items, string? ContinuationToken)> QueryPagedAsync(
    Expression<Func<T, bool>> predicate,
    int pageSize,
    string? continuationToken,
    CancellationToken ct)
{
    var queryOptions = new QueryRequestOptions
    {
        MaxItemCount = pageSize
    };

    var queryable = container.GetItemLinqQueryable<T>(
        requestOptions: queryOptions,
        continuationToken: continuationToken)
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

### Cross-Partition Query

```csharp
public async Task<List<T>> CrossPartitionQueryAsync(
    string sqlQuery,
    CancellationToken ct)
{
    var queryDefinition = new QueryDefinition(sqlQuery);
    var options = new QueryRequestOptions
    {
        MaxConcurrency = -1  // Unlimited parallelism across partitions
    };

    using var iterator = container.GetItemQueryIterator<T>(queryDefinition, requestOptions: options);
    var results = new List<T>();

    while (iterator.HasMoreResults)
    {
        var response = await iterator.ReadNextAsync(ct);
        results.AddRange(response);
    }

    return results;
}
```

### Parameterized SQL Query

```csharp
var query = new QueryDefinition(
    "SELECT * FROM c WHERE c.discriminator = @type AND c.merchantId = @merchantId")
    .WithParameter("@type", "MerchantSalesReport")
    .WithParameter("@merchantId", merchantId);
```

---

## Client Configuration

### Registration with Service Principal (Production)

```csharp
public static class CosmosRegistration
{
    public static IServiceCollection AddCosmosDb(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddOptions<CosmosOptions>()
            .BindConfiguration(CosmosOptions.SectionName)
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddSingleton(sp =>
        {
            var options = sp.GetRequiredService<IOptions<CosmosOptions>>().Value;

            var clientOptions = new CosmosClientOptions
            {
                SerializerOptions = new CosmosSerializationOptions
                {
                    PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase
                },
                ConnectionMode = ConnectionMode.Direct,
                MaxRetryAttemptsOnRateLimitedRequests = 5,
                MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30)
            };

            // Service Principal or Managed Identity for production
            if (string.IsNullOrEmpty(options.AuthKey))
            {
                return new CosmosClient(
                    options.Endpoint,
                    new DefaultAzureCredential(),
                    clientOptions);
            }

            // Auth key for local development
            return new CosmosClient(
                options.Endpoint,
                options.AuthKey,
                clientOptions);
        });

        // Register database and container references
        services.AddSingleton(sp =>
        {
            var client = sp.GetRequiredService<CosmosClient>();
            var options = sp.GetRequiredService<IOptions<CosmosOptions>>().Value;
            return client.GetDatabase(options.DatabaseName);
        });

        return services;
    }
}
```

### CosmosOptions

```csharp
public sealed class CosmosOptions
{
    public const string SectionName = "Cosmos";

    [Required]
    public string Endpoint { get; set; } = string.Empty;
    public string? AuthKey { get; set; }

    [Required]
    public string DatabaseName { get; set; } = string.Empty;
}
```

### AppSettings

```json
{
  "Cosmos": {
    "Endpoint": "https://{account}.documents.azure.com:443/",
    "AuthKey": null,
    "DatabaseName": "{company}-{domain}"
  }
}
```

---

## Database Runner (Initialization)

Ensure database and containers exist on application startup:

```csharp
public sealed class CosmosDatabaseRunner(
    CosmosClient client,
    IOptions<CosmosOptions> options,
    ILogger<CosmosDatabaseRunner> logger) : IHostedService
{
    public async Task StartAsync(CancellationToken ct)
    {
        var databaseResponse = await client.CreateDatabaseIfNotExistsAsync(
            options.Value.DatabaseName, cancellationToken: ct);

        logger.LogInformation("Cosmos database '{Database}' ready",
            options.Value.DatabaseName);

        var database = databaseResponse.Database;

        // Create containers with proper partition key paths
        await EnsureContainerAsync(database, "sales-reports",
            ["/merchantId", "/reportMonth", "/discriminator"], ct);

        await EnsureContainerAsync(database, "order-projections",
            ["/orderId", "/discriminator"], ct);
    }

    private async Task EnsureContainerAsync(
        Database database,
        string containerName,
        IReadOnlyList<string> partitionKeyPaths,
        CancellationToken ct)
    {
        var properties = new ContainerProperties
        {
            Id = containerName,
            PartitionKeyPaths = new Collection<string>(partitionKeyPaths.ToList())
        };

        await database.CreateContainerIfNotExistsAsync(properties, cancellationToken: ct);
        logger.LogInformation("Cosmos container '{Container}' ready", containerName);
    }

    public Task StopAsync(CancellationToken ct) => Task.CompletedTask;
}
```

---

## Change Feed (Optional)

Use the Change Feed for reactive projections:

```csharp
public sealed class OrderChangeFeedProcessor(
    Container leaseContainer,
    Container monitoredContainer,
    IServiceScopeFactory scopeFactory) : IHostedService
{
    private ChangeFeedProcessor? _processor;

    public async Task StartAsync(CancellationToken ct)
    {
        _processor = monitoredContainer
            .GetChangeFeedProcessorBuilder<OrderProjection>(
                "order-processor",
                HandleChangesAsync)
            .WithInstanceName(Environment.MachineName)
            .WithLeaseContainer(leaseContainer)
            .WithStartTime(DateTime.MinValue.ToUniversalTime())
            .Build();

        await _processor.StartAsync();
    }

    private async Task HandleChangesAsync(
        IReadOnlyCollection<OrderProjection> changes,
        CancellationToken ct)
    {
        using var scope = scopeFactory.CreateScope();
        // Process changed documents
        foreach (var change in changes)
        {
            // Handle projection update
        }
    }

    public async Task StopAsync(CancellationToken ct)
    {
        if (_processor is not null)
            await _processor.StopAsync();
    }
}
```

---

## Related Documents

- `knowledge/event-sourcing-flow.md` — Event flow with Cosmos projections
- `knowledge/concurrency-patterns.md` — ETag-based concurrency
- `knowledge/testing-patterns.md` — Cosmos DB integration testing
