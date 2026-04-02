---
alwaysApply: true
description: "Architecture profile for Modular Monolith projects — hard constraints"
---

# Architecture Profile: Modular Monolith

## HARD CONSTRAINTS

### Module Boundaries

- Each module MUST be a self-contained unit with its own domain, data, and API surface
- MUST structure each module as: Api (public contracts), Core (logic), Infrastructure (data)
- Module internals MUST be `internal` — NEVER expose implementation classes as `public`
- NEVER create circular dependencies between modules
- Other modules MUST reference only the Api/contracts project — NEVER Core or Infrastructure

```
BAD:  Shipping.Core references Orders.Core             // internal dependency
GOOD: Shipping.Core references Orders.Api               // public contracts only
```

### No Direct Cross-Module Database Access

- Each module MUST own its data with a separate DbContext
- MUST use separate database schemas per module for data isolation
- NEVER share database tables between modules
- NEVER query another module's DbContext directly — use the module's public API

```
BAD:  // In Shipping module
      var order = await _orderDbContext.Orders.FindAsync(id);  // direct DB access
GOOD: // In Shipping module
      var order = await _orderModule.GetOrderSummaryAsync(id, ct);  // public API
```

### Inter-Module Communication

- Modules MUST communicate via integration events (async) or module interfaces (sync reads)
- NEVER make synchronous cross-module calls during write operations
- Integration events MUST be defined in the SharedKernel or publishing module's Api project
- MUST use eventual consistency for cross-module state changes — NEVER distributed transactions

```
BAD:  // In Orders module during write
      await _inventoryModule.ReserveStockAsync(items);  // sync write across modules
GOOD: // Orders raises event, Inventory handles asynchronously
      RaiseDomainEvent(new OrderPlacedIntegrationEvent(orderId, items));
```

### Shared Kernel

- SharedKernel MUST contain only truly cross-cutting types: base classes, common interfaces
- NEVER put business logic in the shared kernel
- Integration event contracts MAY live in SharedKernel
- MUST keep SharedKernel minimal — when in doubt, keep it in the module

### Module Registration

- Each module MUST have its own DI registration extension method
- The host WebApi project is the composition root — it registers all modules
- NEVER register another module's internal services from the host

```
BAD:  // In Program.cs
      services.AddScoped<OrderModule>();           // registering internals directly
GOOD: // In Program.cs
      services.AddOrderModule(configuration);      // module registers itself
```

### Module Public API Design

- MUST define module interfaces in the Api project with DTOs
- NEVER expose domain entities through module interfaces — ALWAYS use DTOs
- Module interfaces MUST be the only entry point for cross-module reads

## Testing Requirements

- MUST name test methods `{Method}_{Scenario}_{ExpectedResult}`
- MUST use Arrange-Act-Assert with clear visual separation
- NEVER call real services (HTTP, database servers) in unit tests
- NEVER share mutable state between tests
- Module tests MUST be isolated — NEVER depend on another module's state
- Integration event handlers MUST be testable independently of the publishing module

## Data Access

- MUST register each module's DbContext as Scoped — NEVER Singleton or Transient
- MUST use `modelBuilder.HasDefaultSchema("{module}")` for schema isolation
- MUST use separate migrations history tables per module
- ALWAYS use `.AsNoTracking()` for read-only queries
- ALWAYS pass `CancellationToken` to all async data access calls
- NEVER load entire tables — ALWAYS filter with `Where()` and limit with `Take()`
- NEVER call `SaveChanges()` inside loops — batch mutations, save once
- NEVER use lazy loading proxies
