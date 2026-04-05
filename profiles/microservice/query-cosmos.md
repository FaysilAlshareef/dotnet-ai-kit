---
alwaysApply: true
description: "Architecture profile for query (Cosmos DB) projects — hard constraints"
---

# Architecture Profile: Query — Cosmos DB

## HARD CONSTRAINTS

### Cosmos Entity Pattern
- ALWAYS implement `IContainerDocument` interface on every Cosmos entity
- MUST use lowercase `id` property — Cosmos DB requires it, NEVER uppercase `Id`
- ALWAYS include `Discriminator` property returning `nameof(ClassName)` — required for polymorphic queries
- MUST include `ETag` property for optimistic concurrency — NEVER omit it
- ALWAYS use hierarchical partition keys via `PartitionKeyBuilder` (up to 3 levels)
- MUST use factory methods for entity creation from events — NEVER public constructors with raw data
- MUST keep nested arrays bounded — NEVER allow unbounded growth beyond 100 items

```csharp
// ANTI-PATTERN: missing id (lowercase)
public Guid Id { get; set; } // WRONG — Cosmos requires lowercase
public string id { get; set; } = string.Empty; // CORRECT

// ANTI-PATTERN: single partition key
public PartitionKey PartitionKeys => new(MerchantId); // WRONG
public PartitionKey PartitionKeys => new PartitionKeyBuilder()
    .Add(MerchantId).Add(ReportMonth).Add(Discriminator).Build(); // CORRECT
```

### Partition Key Design
- ALWAYS choose partition keys based on query patterns — NEVER based on data structure alone
- NEVER use entity Id as the sole partition key — causes poor distribution
- NEVER use timestamp as the only partition key — causes hot partitions on recent data
- MUST provide partition key to queries whenever possible — NEVER rely on cross-partition queries in hot paths
- ALWAYS create partial key helper methods for scoped queries (e.g., `ForMerchant`, `ForMerchantMonth`)
- Entities in the same container MUST share the same partition key hierarchy

### Transactional Batch
- ALL operations in a `TransactionalBatch` MUST share the same partition key — NEVER batch across partitions
- MUST chunk batches into groups of 100 maximum — Cosmos hard limit
- ALWAYS pass `IfMatchEtag` on replace/upsert operations — NEVER skip concurrency checks
- MUST check `IsSuccessStatusCode` on batch response — NEVER ignore it
- ALWAYS handle `PreconditionFailed` (412) for ETag conflicts with re-read and retry
- Use direct API call for single operations — NEVER wrap a single op in a TransactionalBatch

### Repository Pattern
- One repository per container — NEVER one per entity type
- ALWAYS filter by `Discriminator` in LINQ queries — NEVER omit it
- ALWAYS use `ReadItemAsync` (point read) when id and partition key are known — NEVER query
- MUST use `FeedIterator` with `MaxItemCount` for paginated queries — NEVER unbounded queries
- MUST log RU charges from response headers — NEVER ignore `RequestCharge`

```csharp
// ANTI-PATTERN: query without discriminator
var items = container.GetItemLinqQueryable<T>()
    .Where(predicate); // WRONG — missing discriminator filter

// CORRECT:
var items = container.GetItemLinqQueryable<T>()
    .Where(d => d.Discriminator == typeof(T).Name)
    .Where(predicate);
```

## Testing Requirements

- MUST test ETag-based concurrency conflicts (PreconditionFailed scenarios)
- MUST test point reads returning null for missing documents
- MUST verify partition key alignment in batch operations
- MUST monitor RU consumption in integration tests

## Data Access

- ALWAYS use point reads for known id + partition key combinations
- ALWAYS provide partition key scope when querying — avoid cross-partition fan-out
- MUST set ETag from read operations for subsequent update/replace calls
- ALWAYS use Cosmos SDK `Container` directly in repositories — NEVER EF Core for Cosmos
