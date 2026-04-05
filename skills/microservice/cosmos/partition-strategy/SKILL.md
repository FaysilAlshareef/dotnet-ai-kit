---
name: partition-strategy
description: >
  Cosmos DB partition key strategy with composite/hierarchical keys, cross-partition
  query patterns, and hot partition avoidance. Covers design decisions for data distribution.
  Trigger: partition key, composite key, data distribution, cross-partition query.
metadata:
  category: microservice/cosmos
  agent: cosmos-architect
  when-to-use: "When designing Cosmos DB partition keys or optimizing cross-partition queries"
---

# Partition Strategy — Hierarchical Partition Keys

## Core Principles

- Partition keys determine **data distribution** and **query efficiency**
- Cosmos supports **hierarchical partition keys** (up to 3 levels)
- Queries within a single partition are fast and cheap (RU-efficient)
- Cross-partition queries fan out to all partitions (expensive)
- Choose keys based on query patterns, not data structure
- Avoid hot partitions — distribute writes evenly

## Key Patterns

### Hierarchical Partition Key Definition

```csharp
// Container definition with 3-level partition key
var containerProperties = new ContainerProperties
{
    Id = "invoices",
    PartitionKeyPaths = new Collection<string>
    {
        "/merchantId",    // Level 1: tenant/merchant isolation
        "/reportMonth",   // Level 2: time-based partitioning
        "/discriminator"  // Level 3: entity type
    }
};
```

### Building Partition Keys

```csharp
// Full 3-level key for point reads/writes
public PartitionKey PartitionKeys => new PartitionKeyBuilder()
    .Add(MerchantId)           // Level 1
    .Add(ReportMonth)          // Level 2
    .Add(Discriminator)        // Level 3
    .Build();

// Partial key for scoped queries (Level 1 only)
public static PartitionKey ForMerchant(string merchantId) =>
    new PartitionKeyBuilder()
        .Add(merchantId)
        .Build();

// Partial key for time-scoped queries (Level 1 + 2)
public static PartitionKey ForMerchantMonth(string merchantId, string month) =>
    new PartitionKeyBuilder()
        .Add(merchantId)
        .Add(month)
        .Build();
```

### Query Patterns by Partition Scope

```csharp
// Fastest: Point read with full partition key
var invoice = await container.ReadItemAsync<SaleInvoice>(
    id, SaleInvoice.ForMerchantMonth("M001", "2025-03"));

// Fast: Query within full partition
var invoices = await repo.QueryAsync(
    i => i.TotalAmount > 1000,
    SaleInvoice.ForMerchantMonth("M001", "2025-03"));

// Medium: Query with partial partition key (fan-out within merchant)
var allInvoices = await repo.QueryAsync(
    i => i.TotalAmount > 1000,
    SaleInvoice.ForMerchant("M001"));

// Slow: Cross-partition query (avoid in production hot paths)
var report = await repo.QueryAsync(
    i => i.TotalAmount > 10000);
```

### Strategy Decision Guide

```
Query Pattern                    | Recommended Partition Key
-------------------------------- | -------------------------
Single tenant, time-series       | TenantId / Year-Month / EntityType
Multi-tenant, per-user data      | TenantId / UserId / EntityType
Geographic data                  | Region / City / EntityType
Order processing                 | CustomerId / OrderDate / EntityType
IoT telemetry                    | DeviceId / Date / EntityType
```

### Container Design Patterns

```
Pattern 1: Entity-per-container
  - invoices container → SaleInvoice documents
  - reports container → MerchantSalesReport documents
  - Simple, clear boundaries
  - Best for independent entity lifecycles

Pattern 2: Polymorphic container
  - sales container → SaleInvoice + SoldItem + SalesReport
  - Uses Discriminator for filtering
  - Enables TransactionalBatch across types
  - Best when entities share partition key and need atomic operations
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Using entity Id as partition key | Choose keys based on query patterns |
| Single-value partition key | Use hierarchical keys for flexibility |
| Timestamp as only partition key | Causes hot partitions on recent data |
| Cross-partition queries in hot paths | Design partitions around common queries |
| Ignoring RU costs | Monitor and optimize partition strategy |

## Detect Existing Patterns

```bash
# Find partition key definitions
grep -r "PartitionKeyBuilder\|PartitionKeyPaths" --include="*.cs" src/

# Find container properties
grep -r "ContainerProperties\|ContainerName" --include="*.cs" src/

# Find cross-partition queries
grep -r "ToListWithoutPartitionFilter\|EnableCrossPartition" --include="*.cs" src/
```

## Adding to Existing Project

1. **Map existing partition key strategy** before adding new entities
2. **New entities in same container** must use the same partition key hierarchy
3. **Add partial key helper methods** for scoped queries
4. **Monitor RU consumption** when changing query patterns
5. **Test with realistic data volumes** — partition strategy matters at scale
