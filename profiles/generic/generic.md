---
alwaysApply: true
description: "Architecture profile for generic .NET projects — hard constraints"
---

# Architecture Profile: Generic .NET

This is the fallback profile applied when no specific architecture pattern is detected.
It enforces universal .NET constraints that apply to all project types.

## HARD CONSTRAINTS

### Layer Dependency Direction

- Dependencies MUST flow in one direction — outer layers depend on inner layers
- NEVER create circular references between projects or namespaces
- Domain/core logic MUST NOT depend on infrastructure concerns (databases, HTTP, file I/O)
- ALWAYS verify project references follow a clear dependency direction

```
BAD:  ProjectA references ProjectB, ProjectB references ProjectA  // circular
GOOD: ProjectA references ProjectB (one direction only)
```

### Code Organization

- MUST use `sealed` on classes not designed for inheritance
- MUST use `private set` on entity properties — NEVER expose public setters on domain objects
- MUST use records for immutable data (DTOs, event data, value objects)
- NEVER use `async void` — ALWAYS return `Task` or `Task<T>`
- NEVER use `DateTime.Now` — ALWAYS use an injected time provider
- NEVER catch generic `Exception` unless re-throwing with context

```
BAD:  catch (Exception) { /* swallowed */ }
GOOD: catch (SpecificException ex) { _logger.LogError(ex, "..."); throw; }
```

### Naming Conventions

- Aggregates and entities: PascalCase singular (`Order`, `Product`)
- Commands: `{Action}{Aggregate}Command` (`CreateOrderCommand`)
- Queries: `Get{Entities}Query` (`GetOrdersQuery`)
- Handlers: `{CommandOrQuery}Handler` (`CreateOrderCommandHandler`)
- Repository interfaces: `I{Entity}Repository` with implementations as `{Entity}Repository`
- Test methods: `{Method}_{Scenario}_{ExpectedResult}`

### Error Handling

- NEVER swallow exceptions — log then re-throw or return a typed error
- NEVER return generic error messages to users — use structured error types
- MUST use structured logging for all exception context
- MUST use global exception handler middleware in web applications
- MUST map domain errors to appropriate HTTP status codes

### Dependency Injection

- ALWAYS use constructor injection — NEVER use service locator pattern
- MUST register services with appropriate lifetimes (Scoped for DbContext, Singleton for stateless)
- NEVER resolve services manually with `IServiceProvider` inside business logic

## Testing Requirements

- MUST name test methods `{Method}_{Scenario}_{ExpectedResult}`
- MUST use Arrange-Act-Assert with clear visual separation
- NEVER call real services (HTTP, gRPC, database servers) in unit tests
- NEVER share mutable state between tests
- NEVER write tests that depend on execution order
- MUST NOT use `Thread.Sleep` or `Task.Delay` in tests — use async patterns
- MUST test both success paths and error cases
- MUST mock external dependencies — NEVER hit real services

## Data Access

- MUST register DbContext as Scoped — NEVER Singleton or Transient
- ALWAYS use `.AsNoTracking()` for all read-only queries
- ALWAYS use explicit `.Include()` for related data — NEVER rely on lazy loading
- ALWAYS pass `CancellationToken` to all async EF Core and Dapper calls
- MUST use pagination for all list queries — NEVER return unbounded results
- NEVER use lazy loading proxies (`UseLazyLoadingProxies()`)
- NEVER load entire tables — ALWAYS filter with `Where()` and limit with `Take()`
- NEVER call `SaveChanges()` inside loops — batch mutations, save once
- NEVER use `.ToList()` before `.Where()` — filter in the query, not in memory
- NEVER use `Find()` in loops — batch with `Where(x => ids.Contains(x.Id))`
- MUST use parameterized queries for all raw SQL — NEVER use string concatenation
