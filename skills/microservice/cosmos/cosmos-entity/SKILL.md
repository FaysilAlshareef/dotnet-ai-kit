---
name: cosmos-entity
description: >
  Cosmos DB entity design with IContainerDocument, hierarchical partition keys,
  discriminator pattern, and ETag concurrency. Covers entity modeling for NoSQL documents.
  Trigger: cosmos entity, partition key, discriminator, IContainerDocument, NoSQL.
metadata:
  category: microservice/cosmos
  agent: cosmos-architect
  when-to-use: "When creating or modifying Cosmos DB entities, partition keys, discriminators"
  paths: "${detected_paths.cosmos_entities}/**/*.cs"
---

# Cosmos Entity — IContainerDocument Pattern

## Core Principles

- All Cosmos entities implement `IContainerDocument` interface
- 3-level hierarchical partition keys via `PartitionKeyBuilder`
- Discriminator string enables polymorphic containers (multiple entity types per container)
- `ETag` for optimistic concurrency control
- `id` property is required by Cosmos DB (lowercase)
- Factory methods create entities from events (same CTO pattern as SQL query side)
- Nested documents (lists, embedded objects) are first-class in Cosmos

## Key Patterns

### IContainerDocument Interface

```csharp
namespace {Company}.{Domain}.Cosmos.Domain;

public interface IContainerDocument
{
    string ContainerName { get; }
    PartitionKey PartitionKeys { get; }
    string Discriminator { get; }
    string? ETag { get; set; }
}
```

### Entity Implementation

```csharp
namespace {Company}.{Domain}.Cosmos.Domain;

public sealed class SaleInvoice : IContainerDocument
{
    public string id { get; set; } = string.Empty;
    public string MerchantId { get; private set; } = string.Empty;
    public string InvoiceNumber { get; private set; } = string.Empty;
    public decimal TotalAmount { get; private set; }
    public DateTime CreatedAt { get; private set; }
    public List<SoldItem> Items { get; private set; } = [];
    public int Sequence { get; private set; }

    // IContainerDocument
    public string ContainerName => "invoices";
    public string Discriminator => nameof(SaleInvoice);
    public string? ETag { get; set; }

    public PartitionKey PartitionKeys => new PartitionKeyBuilder()
        .Add(MerchantId)
        .Add(CreatedAt.ToString("yyyy-MM"))
        .Add(Discriminator)
        .Build();

    // Factory method from event
    public static SaleInvoice FromInvoiceCreated(Event<InvoiceCreatedData> @event)
    {
        return new SaleInvoice
        {
            id = @event.AggregateId.ToString(),
            MerchantId = @event.Data.MerchantId,
            InvoiceNumber = @event.Data.InvoiceNumber,
            TotalAmount = @event.Data.TotalAmount,
            CreatedAt = @event.DateTime,
            Items = @event.Data.Items.Select(i => new SoldItem
            {
                ProductId = i.ProductId,
                ProductName = i.ProductName,
                Quantity = i.Quantity,
                UnitPrice = i.UnitPrice
            }).ToList(),
            Sequence = @event.Sequence
        };
    }

    // Apply update event
    public void Apply(Event<InvoiceUpdatedData> @event)
    {
        TotalAmount = @event.Data.TotalAmount;
        Sequence = @event.Sequence;
    }
}
```

### Nested Document

```csharp
namespace {Company}.{Domain}.Cosmos.Domain;

public sealed class SoldItem
{
    public string ProductId { get; set; } = string.Empty;
    public string ProductName { get; set; } = string.Empty;
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal LineTotal => Quantity * UnitPrice;
}
```

### Report Entity (Aggregated Data)

```csharp
namespace {Company}.{Domain}.Cosmos.Domain;

public sealed class MerchantSalesReport : IContainerDocument
{
    public string id { get; set; } = string.Empty;
    public string MerchantId { get; private set; } = string.Empty;
    public string ReportMonth { get; private set; } = string.Empty;
    public decimal TotalSales { get; private set; }
    public int InvoiceCount { get; private set; }
    public bool IsReport => true;

    public string ContainerName => "reports";
    public string Discriminator => nameof(MerchantSalesReport);
    public string? ETag { get; set; }

    public PartitionKey PartitionKeys => new PartitionKeyBuilder()
        .Add(MerchantId)
        .Add(ReportMonth)
        .Add(Discriminator)
        .Build();

    public void AddInvoice(decimal amount)
    {
        TotalSales += amount;
        InvoiceCount++;
    }
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Missing `id` property (lowercase) | Cosmos requires lowercase `id` |
| Single partition key | Use hierarchical partition keys (up to 3 levels) |
| Missing Discriminator | Required for polymorphic container queries |
| Public setters everywhere | Private setters with factory methods and Apply |
| Large nested arrays (unbounded) | Keep nested arrays bounded; split if > 100 items |

## Detect Existing Patterns

```bash
# Find IContainerDocument implementations
grep -r "IContainerDocument" --include="*.cs" src/

# Find PartitionKeyBuilder usage
grep -r "PartitionKeyBuilder" --include="*.cs" src/

# Find Discriminator properties
grep -r "Discriminator =>" --include="*.cs" src/

# Find factory methods
grep -r "public static.*From" --include="*.cs" src/Cosmos/Domain/
```

## Adding to Existing Project

1. **Check existing `IContainerDocument` interface** — match the contract exactly
2. **Follow partition key strategy** — consistent across entities in same container
3. **Match discriminator naming** — typically the class name
4. **Use factory methods** for entity creation from events
5. **Keep `id` lowercase** — Cosmos DB requirement
6. **Set ETag from read operations** — needed for optimistic concurrency on updates
