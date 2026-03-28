---
alwaysApply: true
description: Enforces performance best practices — no N+1 queries, proper caching, efficient async, memory awareness.
---

# Performance Rules

Fast by default. Measure before optimizing, but avoid known anti-patterns from the start.

## MUST

- Use `.AsNoTracking()` on read-only EF Core queries
- Use `.Select()` projections to fetch only needed columns — never load full entities for display
- Use pagination on all list endpoints — never return unbounded result sets
- Use `async`/`await` for all I/O-bound operations
- Use `IMemoryCache` or `HybridCache` for frequently accessed, rarely changing data
- Use `StringBuilder` for string concatenation in loops (not `+=`)
- Use `HashSet<T>` for contains-checks on large collections (not `List<T>.Contains()`)

## MUST NOT

- Never execute queries inside loops (N+1 problem) — batch with `.Where(x => ids.Contains(x.Id))`
- Never call `.ToList()` before `.Where()` — filter in the database, not in memory
- Never load entire tables — always filter and paginate
- Never use `Task.Run()` in ASP.NET Core request handlers
- Never allocate large objects in hot paths — reuse with `ArrayPool<T>` when applicable
- Never ignore `CancellationToken` — cancelled requests should stop work, not waste resources

## Caching Rules

| Data Pattern | Cache Strategy |
|-------------|---------------|
| Static reference data | `IMemoryCache` with long TTL |
| Per-request repeated lookup | Request-scoped cache or `HybridCache` |
| Cross-server shared data | `IDistributedCache` (Redis) |
| API responses | Output caching with `[OutputCache]` |
| Conditional responses | ETag + If-None-Match (304 Not Modified) |

## Detection Instructions

1. Search for queries inside `foreach`/`for` loops — refactor to batch
2. Search for `.ToList()` before `.Where()` — move filter before materialization
3. Check list endpoints for pagination — add `Skip/Take`
4. Search for `string +=` in loops — replace with `StringBuilder`
5. Check for missing caching on read-heavy endpoints

## Related Skills
- `skills/api/caching-strategies/SKILL.md` — output cache, distributed cache, ETag
- `skills/core/async-patterns/SKILL.md` — efficient async patterns
- `skills/data/ef-queries/SKILL.md` — query optimization
