---
name: transactional-batch
description: >
  Use when performing atomic multi-document operations with Cosmos DB TransactionalBatch.
metadata:
  category: microservice/cosmos
  agent: cosmos-architect
  when-to-use: "When implementing Cosmos DB TransactionalBatch or atomic multi-document operations"
---

# Transactional Batch — Atomic Multi-Document Operations

## Core Principles

- `TransactionalBatch` ensures all-or-nothing semantics within a single partition
- All operations in a batch **must share the same partition key**
- Max 100 operations per batch; chunk larger batches
- `IfMatchEtag` enables optimistic concurrency on replace/upsert
- Batch response contains per-item status codes
- Use for coordinated updates (e.g., invoice + report update together)

## Key Patterns

### Basic TransactionalBatch

```csharp
namespace {Company}.{Domain}.Cosmos.Infrastructure;

public sealed class CosmosUnitOfWork(Container container)
{
    private readonly List<(IContainerDocument Document, BatchOperation Op)> _operations = [];

    public void Create(IContainerDocument document)
        => _operations.Add((document, BatchOperation.Create));

    public void Upsert(IContainerDocument document)
        => _operations.Add((document, BatchOperation.Upsert));

    public void Replace(IContainerDocument document)
        => _operations.Add((document, BatchOperation.Replace));

    public void Delete(IContainerDocument document)
        => _operations.Add((document, BatchOperation.Delete));

    public async Task CommitAsync(PartitionKey pk, CancellationToken ct)
    {
        if (_operations.Count == 0) return;

        if (_operations.Count == 1)
        {
            await ExecuteSingleAsync(_operations[0], pk, ct);
            return;
        }

        // Chunk into batches of 100 (Cosmos limit)
        foreach (var chunk in _operations.Chunk(100))
        {
            var batch = container.CreateTransactionalBatch(pk);

            foreach (var (doc, op) in chunk)
            {
                switch (op)
                {
                    case BatchOperation.Create:
                        batch.CreateItem(doc);
                        break;
                    case BatchOperation.Upsert:
                        batch.UpsertItem(doc, new TransactionalBatchItemRequestOptions
                        {
                            IfMatchEtag = doc.ETag
                        });
                        break;
                    case BatchOperation.Replace:
                        batch.ReplaceItem(doc.id, doc, new TransactionalBatchItemRequestOptions
                        {
                            IfMatchEtag = doc.ETag
                        });
                        break;
                    case BatchOperation.Delete:
                        batch.DeleteItem(doc.id);
                        break;
                }
            }

            var response = await batch.ExecuteAsync(ct);
            if (!response.IsSuccessStatusCode)
            {
                throw new CosmosBatchException(
                    $"Batch failed: {response.StatusCode}",
                    response.StatusCode);
            }
        }

        _operations.Clear();
    }

    private async Task ExecuteSingleAsync(
        (IContainerDocument Doc, BatchOperation Op) item,
        PartitionKey pk, CancellationToken ct)
    {
        switch (item.Op)
        {
            case BatchOperation.Create:
                await container.CreateItemAsync(item.Doc, pk, cancellationToken: ct);
                break;
            case BatchOperation.Upsert:
                await container.UpsertItemAsync(item.Doc, pk,
                    new ItemRequestOptions { IfMatchEtag = item.Doc.ETag }, ct);
                break;
        }
        _operations.Clear();
    }
}

public enum BatchOperation { Create, Upsert, Replace, Delete }
```

### ETag-Based Concurrency

```csharp
// Read document — ETag is populated from response
var invoice = await repo.GetByIdAsync(id, pk, ct);
// invoice.ETag is set automatically

// Modify
invoice.Apply(updateEvent);

// Write with ETag check — fails if document changed since read
uow.Replace(invoice);
await uow.CommitAsync(invoice.PartitionKeys, ct);

// Handle concurrency conflict
try
{
    await uow.CommitAsync(pk, ct);
}
catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.PreconditionFailed)
{
    // ETag mismatch — re-read and retry
    logger.LogWarning("Concurrency conflict, retrying...");
    // Re-read and retry logic
}
```

### Coordinated Multi-Document Update

```csharp
// Invoice created → update invoice + update monthly report atomically
public async Task HandleInvoiceCreated(Event<InvoiceCreatedData> @event, CancellationToken ct)
{
    var invoice = SaleInvoice.FromInvoiceCreated(@event);
    var pk = invoice.PartitionKeys;

    // Load or create report in same partition
    var report = await repo.GetByIdAsync(reportId, pk, ct)
        ?? new MerchantSalesReport { id = reportId, ... };

    report.AddInvoice(invoice.TotalAmount);

    uow.Create(invoice);
    uow.Upsert(report);
    await uow.CommitAsync(pk, ct);
}
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Batch across different partitions | All operations must share partition key |
| More than 100 operations unbatched | Chunk into batches of 100 |
| Missing ETag on replace/upsert | Always pass ETag for concurrency control |
| Ignoring batch response status | Check `IsSuccessStatusCode` and per-item results |
| Using batch for single operations | Direct API call is simpler and clearer |

## Detect Existing Patterns

```bash
# Find TransactionalBatch usage
grep -r "CreateTransactionalBatch\|TransactionalBatch" --include="*.cs" src/

# Find ETag usage
grep -r "IfMatchEtag\|ETag" --include="*.cs" src/Cosmos/

# Find CosmosUnitOfWork
grep -r "CosmosUnitOfWork" --include="*.cs" src/
```

## Adding to Existing Project

1. **Check if a `CosmosUnitOfWork` already exists** — match its API
2. **Verify partition key alignment** — batch items must share the same partition
3. **Follow the chunking pattern** for large batches
4. **Handle `PreconditionFailed` (412)** for ETag conflicts
5. **Log RU charges** from batch responses for cost monitoring
