---
name: sequence-checking
description: >
  Inline sequence validation for idempotent event handlers. Covers the exact guard pattern
  using Sequence != @event.Sequence - 1, returning true for already-processed duplicates,
  and false for out-of-order gaps. No helper class — logic is inlined in each handler.
  Trigger: sequence check, idempotent, event ordering, gap detection.
category: microservice/query
agent: query-architect
---

# Sequence Checking — Inline Idempotent Guard

## Core Principles

- Every event has `int Sequence` starting at 1, incrementing by 1 per aggregate
- Every query entity tracks `int Sequence { get; private set; }`
- Sequence validation is **inlined** in each handler — no helper class
- The core guard: `if (entity.Sequence != @event.Sequence - 1)`
- Returning `true` tells the listener to **CompleteMessage** (processed or already done)
- Returning `false` tells the listener to **AbandonMessage** (retry later)
- After processing, entity behavior method updates `Sequence` to `@event.Sequence`

## The Core Guard Pattern

The sequence check is a single `if` statement that handles both duplicates and gaps:

```csharp
if (entity.Sequence != @event.Sequence - 1)
    return entity.Sequence >= @event.Sequence;
```

This single expression covers TWO cases:
- **Already processed** (entity.Sequence >= event.Sequence): returns `true` (idempotent)
- **Gap / out of order** (entity.Sequence < event.Sequence - 1): returns `false` (retry)

## Key Patterns

### Update Handler with Sequence Guard

```csharp
public async Task<bool> Handle(
    Event<OrderUpdatedData> @event,
    CancellationToken cancellationToken)
{
    var order = await _unitOfWork.Orders.FindAsync(@event.AggregateId);

    // Entity not found — creation event hasn't been processed yet
    if (order is null)
        return false;

    // THE CORE GUARD: check sequence is exactly next expected
    if (order.Sequence != @event.Sequence - 1)
        return order.Sequence >= @event.Sequence;
        // entity.Sequence >= event.Sequence -> true (already processed, complete msg)
        // entity.Sequence < event.Sequence - 1 -> false (gap, abandon msg)

    // Process: call entity behavior method (which sets Sequence internally)
    order.UpdateDetails(@event.Data, @event.Sequence);

    await _unitOfWork.SaveChangesAsync();

    return true;
}
```

### Creation Handler — Different Pattern

Creation handlers do NOT use the sequence guard. They check for existence instead:

```csharp
public async Task<bool> Handle(
    Event<OrderCreatedData> @event,
    CancellationToken cancellationToken)
{
    var order = await _unitOfWork.Orders.FindAsync(@event.AggregateId);

    // Already exists — idempotent, return true
    if (order is not null)
        return true;

    order = new Order(@event);  // Constructor sets Sequence = @event.Sequence
    await _unitOfWork.Orders.AddAsync(order);
    await _unitOfWork.SaveChangesAsync();

    return true;
}
```

### Sequence Update in Entity Behavior Method

The entity behavior method is where `Sequence` gets updated:

```csharp
// In the entity class
public void UpdateDetails(OrderUpdatedData data, int sequence)
{
    CustomerName = data.CustomerName;
    Email = data.Email;
    Total = data.Total;
    Sequence = sequence;  // <-- Sequence updated to @event.Sequence
}
```

### Alternative: IncrementSequence Pattern

Some entities use `IncrementSequence()` after calling the behavior method:

```csharp
if (product.Sequence == @event.Sequence - 1)
{
    product.Update(@event);
    product.IncrementSequence();  // Sequence++
    await _unitOfWork.SaveChangesAsync();
}

return product.Sequence >= @event.Sequence;
```

## Sequence Decision Matrix

```
Condition                              | Return | Message Action | Why
---------------------------------------|--------|----------------|--------------------
entity is null (update event)          | false  | Abandon        | Creation not yet processed
entity.Sequence == @event.Sequence - 1 | true   | Complete       | Next in order, process it
entity.Sequence >= @event.Sequence     | true   | Complete       | Already processed (idempotent)
entity.Sequence < @event.Sequence - 1  | false  | Abandon        | Gap — missing intermediate events
entity is not null (creation event)    | true   | Complete       | Already created (idempotent)
```

## Why Return True for Duplicates

Returning `true` for already-processed events is critical because:

1. The listener calls `CompleteMessageAsync` when handler returns `true`
2. This removes the message from the Service Bus queue permanently
3. If we returned `false`, the message would be abandoned and retried forever
4. The duplicate would never be cleared, causing an infinite retry loop
5. Returning `true` = "I have handled this (or it was already handled), move on"

## Why Return False for Gaps

Returning `false` for sequence gaps causes:

1. The listener calls `AbandonMessageAsync`
2. Service Bus retries the message later
3. By that time, the missing intermediate event(s) should have been processed
4. Sessions ensure per-aggregate ordering, but gaps can occur during recovery

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| `SequenceChecker` helper class | Inline the check in each handler |
| `if (@event.Sequence <= entity.Sequence) return true` | `if (entity.Sequence != @event.Sequence - 1) return entity.Sequence >= @event.Sequence` |
| Separate if statements for duplicate and gap | Single combined expression |
| Throwing on sequence mismatch | Return bool — let listener decide action |
| Not updating Sequence after processing | Behavior method must set `Sequence = sequence` |

## Detect Existing Patterns

```bash
# Find the core sequence guard pattern
grep -r "Sequence != @event.Sequence - 1" --include="*.cs" Application/

# Find Sequence >= comparison for idempotency
grep -r "Sequence >= @event.Sequence" --include="*.cs" Application/

# Find entity Sequence property
grep -r "public int Sequence" --include="*.cs" Domain/Entities/
```

## Adding to Existing Project

1. **Use the exact guard pattern**: `if (entity.Sequence != @event.Sequence - 1) return entity.Sequence >= @event.Sequence;`
2. **Creation handlers** use existence check, not sequence check
3. **Entity behavior methods** must update `Sequence` to the new value
4. **Never throw** on sequence mismatch — always return bool
5. **Test with duplicates** to verify `true` is returned (not reprocessed)
6. **Test with gaps** to verify `false` is returned (abandoned for retry)
