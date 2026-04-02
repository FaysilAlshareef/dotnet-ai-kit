---
alwaysApply: true
description: "Architecture profile for Domain-Driven Design projects — hard constraints"
---

# Architecture Profile: Domain-Driven Design

## HARD CONSTRAINTS

### Aggregate Roots as Consistency Boundaries

- ALWAYS route all state changes through the aggregate root — NEVER modify child entities directly
- Aggregate root MUST enforce all invariants for its boundary
- MUST use factory methods for aggregate creation — NEVER expose public constructors
- NEVER allow external code to bypass the aggregate root to modify internal entities

```
BAD:  order.Items.Add(new OrderItem(...));        // bypasses root
GOOD: order.AddItem(productId, quantity, price);  // root enforces invariants
```

### Value Objects for Identity-Less Concepts

- MUST use value objects for concepts without identity (Money, Address, DateRange)
- Value objects MUST be immutable — use `sealed record` or `readonly record struct`
- Value objects MUST validate on construction — NEVER allow invalid state
- NEVER use primitives where a value object is appropriate (primitive obsession)

```
BAD:  public decimal Price { get; set; }           // naked primitive
GOOD: public Money Price { get; private set; }     // typed value object
```

### Strongly-Typed IDs

- MUST use strongly-typed IDs for all aggregate roots and key entities
- NEVER pass raw `Guid` or `int` where a typed ID is expected
- Typed IDs prevent accidental parameter swaps at compile time

```
BAD:  public Guid GetOrder(Guid id)               // any Guid accepted
GOOD: public Order GetOrder(OrderId id)            // type-safe
```

### Domain Events for Cross-Aggregate Communication

- MUST use domain events for side effects that span aggregate boundaries
- NEVER directly call methods on one aggregate from within another aggregate
- Domain events MUST be raised through the aggregate root's event collection
- NEVER put event dispatch logic inside domain entities — dispatch in infrastructure

```
BAD:  order.Submit(); inventoryService.Reserve(order.Items);  // tight coupling
GOOD: order.Submit(); // raises OrderSubmittedEvent, handled separately
```

### Repository Per Aggregate Root

- MUST define one repository interface per aggregate root — not per entity
- NEVER create repositories for non-root entities (e.g., OrderItem)
- Repository interfaces MUST live in Domain — implementations in Infrastructure
- NEVER expose `IQueryable` from repositories — return materialized results

```
BAD:  IOrderItemRepository, IOrderLineRepository   // repos for child entities
GOOD: IOrderRepository                              // one repo for the aggregate
```

### Rich Domain Model

- MUST place business logic on domain entities — NEVER in application services
- NEVER create anemic entities with only getters and setters
- MUST use private setters on all entity properties
- MUST expose internal collections as `IReadOnlyList<T>` — NEVER as `List<T>`

```
BAD:  public List<OrderItem> Items { get; set; }    // mutable, public
GOOD: public IReadOnlyList<OrderItem> Items => _items.AsReadOnly();
```

### Bounded Context Isolation

- NEVER share entity classes across bounded contexts
- Each bounded context MUST have its own model for shared concepts
- MUST use anti-corruption layers to translate between contexts

## Testing Requirements

- MUST name test methods `{Method}_{Scenario}_{ExpectedResult}` using Arrange-Act-Assert
- Aggregate tests MUST verify correct domain events are raised
- MUST test invariant enforcement by asserting exceptions on invalid operations
- NEVER call real services (HTTP, database servers) or share mutable state between tests

## Data Access

- MUST register DbContext as Scoped and use value converters for strongly-typed IDs
- MUST use row version or concurrency tokens on concurrently updated entities
- ALWAYS use `.AsNoTracking()` for read-only queries and pass `CancellationToken` on all async calls
- NEVER load entire tables — ALWAYS filter with `Where()` and limit with `Take()`
