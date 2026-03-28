---
alwaysApply: true
description: Enforces EF Core and data access best practices — query efficiency, DbContext lifetime, no N+1.
---

# Data Access Rules

Detect the existing data access pattern (EF Core, Dapper, or both) and follow it.

## MUST

- Use `.AsNoTracking()` for all read-only queries
- Use explicit `.Include()` for related data — never rely on lazy loading
- Use pagination for all list queries — never return unbounded results
- Use parameterized queries for all raw SQL and Dapper queries
- Register `DbContext` as Scoped — never Singleton or Transient
- Use `CancellationToken` on all async EF Core and Dapper calls
- Use value converters for strongly-typed IDs
- Use row version / concurrency tokens on entities that can be updated concurrently

## MUST NOT

- Never load entire tables — always filter with `Where()` and limit with `Take()`
- Never use lazy loading proxies (`UseLazyLoadingProxies()`)
- Never put business logic in migrations
- Never share `DbContext` across threads or async boundaries
- Never use `Find()` in loops — batch with `Where(x => ids.Contains(x.Id))`
- Never call `SaveChanges()` inside loops — batch mutations, save once
- Never use `.ToList()` before filtering — filter in the query, not in memory

## Query Patterns

| Scenario | Pattern |
|----------|---------|
| Single entity by ID | `FindAsync(id, ct)` or `FirstOrDefaultAsync(x => x.Id == id, ct)` |
| List with filter | `.Where(filter).OrderBy(sort).Skip(offset).Take(limit).ToListAsync(ct)` |
| Read-only list | `.AsNoTracking().Where(...).ToListAsync(ct)` |
| Exists check | `.AnyAsync(x => x.Email == email, ct)` — not `Count() > 0` |
| Projection | `.Select(x => new Dto(x.Id, x.Name)).ToListAsync(ct)` |

## Detection Instructions

1. Search for `.ToList()` before `.Where()` — move filter before materialization
2. Check for missing `.AsNoTracking()` on read queries
3. Search for `SaveChanges` inside loops — refactor to batch
4. Check DbContext registration is Scoped
5. Search for `Find()` inside loops — replace with batch query

## Related Skills
- `skills/data/ef-core-basics/SKILL.md` — DbContext, migrations, interceptors
- `skills/data/ef-queries/SKILL.md` — query optimization patterns
- `skills/data/repository-patterns/SKILL.md` — repository and UnitOfWork
