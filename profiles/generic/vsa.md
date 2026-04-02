---
alwaysApply: true
description: "Architecture profile for Vertical Slice Architecture projects — hard constraints"
---

# Architecture Profile: Vertical Slice Architecture

## HARD CONSTRAINTS

### Feature Folder Boundaries

- ALWAYS organize code by feature, not by layer — each slice is self-contained
- ALWAYS place Request, Response, Handler, and Validator in a single file per operation
- MUST co-locate all slice artifacts under `Features/{FeatureName}/`
- NEVER create layer folders (Domain/, Application/, Infrastructure/) inside a VSA project

```
BAD:  src/Application/Handlers/CreateOrderHandler.cs
GOOD: src/Features/Orders/CreateOrder.cs
```

### Handler Independence

- MUST have exactly one handler per feature operation — no shared handlers
- NEVER import or call a handler from another feature's namespace
- NEVER share service classes across features — if multiple slices need the same logic, extract to `Common/` only after 3+ proven duplications
- Handlers MUST be `internal sealed` — NEVER `public`

```
BAD:  public class CreateOrderHandler  // public, reused elsewhere
GOOD: internal sealed class Handler    // scoped to the slice
```

### No Cross-Feature Dependencies

- NEVER reference types from one feature folder inside another feature folder
- NEVER create shared repository abstractions — handlers talk to DbContext directly
- MUST NOT create generic `I{Entity}Repository` interfaces (defeats VSA simplicity)
- Each slice MUST be independently deletable without breaking other slices

```
BAD:  Features/Orders/CreateOrder.cs imports Features/Products/ProductService.cs
GOOD: Features/Orders/CreateOrder.cs injects AppDbContext and queries directly
```

### Data Access

- ALWAYS use DbContext directly in handlers — no repository layer
- Each slice MUST be free to use whatever data access pattern fits (EF Core, Dapper, raw SQL)
- ALWAYS use `.AsNoTracking()` for read-only query slices
- ALWAYS pass `CancellationToken` to all async data access calls
- MUST use pagination for all list query slices — NEVER return unbounded results
- NEVER use lazy loading proxies

### Endpoint Registration

- ALWAYS group endpoints by feature using an endpoint group class per feature
- MUST co-locate endpoint registration with the feature folder
- NEVER scatter route registrations across unrelated files

### Shared Code Extraction

- MUST NOT extract shared code until the same logic appears in 3+ slices
- Shared utilities go in `Common/` or `Shared/` only — NEVER in a feature folder
- NEVER create a "base handler" class that other handlers inherit from

## Testing Requirements

- MUST name test methods `{Method}_{Scenario}_{ExpectedResult}`
- MUST use Arrange-Act-Assert with clear visual separation
- NEVER call real services (HTTP, database servers) in unit tests
- NEVER share mutable state between tests
- Each feature slice SHOULD have its own test class
- MUST test the handler directly — do not test through the HTTP pipeline for unit tests

## Data Access

- MUST register DbContext as Scoped — NEVER Singleton or Transient
- ALWAYS filter with `Where()` and limit with `Take()` — NEVER load entire tables
- NEVER call `SaveChanges()` inside loops — batch mutations, save once
- NEVER use `.ToList()` before `.Where()` — filter in the query, not in memory
- MUST use value converters for strongly-typed IDs when present
