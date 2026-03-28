---
alwaysApply: true
description: Enforces async/await correctness — CancellationToken propagation, no blocking, proper concurrency.
---

# Async & Concurrency Rules

Async bugs are silent killers — deadlocks, thread pool starvation, lost cancellations.

## MUST

- Always propagate `CancellationToken` through the entire async call chain
- Always use `async`/`await` end-to-end — never mix blocking and async
- Always return `Task` or `Task<T>` from async methods
- Use `Task.WhenAll` for independent parallel operations
- Use `IServiceScopeFactory` in `BackgroundService` — never inject scoped services directly
- Use `ConfigureAwait(false)` in library code only — not in ASP.NET Core app code
- Use `SemaphoreSlim` for async-safe locking — never `lock` with async code

## MUST NOT

- Never use `.Result`, `.Wait()`, or `.GetAwaiter().GetResult()` — causes deadlocks
- Never use `async void` except for event handlers
- Never use `Task.Run()` in ASP.NET Core request handlers — wastes thread pool threads
- Never fire-and-forget (`_ = DoAsync()`) without proper error handling
- Never use `Thread.Sleep()` — use `await Task.Delay()` with CancellationToken
- Never share `DbContext` or `HttpClient` instances across threads

## Patterns

| Scenario | Correct Pattern |
|----------|----------------|
| Return type | `Task<T>` default, `ValueTask<T>` for hot paths |
| Parallel calls | `Task.WhenAll(task1, task2)` |
| Timeout | `CancellationTokenSource.CreateLinkedTokenSource` + `CancelAfter` |
| Background work | `BackgroundService` + `IServiceScopeFactory` |
| Thread-safe init | `SemaphoreSlim` with double-check |
| Streaming | `IAsyncEnumerable<T>` with `[EnumeratorCancellation]` |

## Detection Instructions

1. Search for `.Result` and `.GetAwaiter().GetResult()` — convert to `await`
2. Search for `async void` — change to `async Task` (except event handlers)
3. Check all async methods accept and forward `CancellationToken`
4. Search for `Task.Run` in controllers/endpoints — remove
5. Check `BackgroundService` uses `IServiceScopeFactory`, not direct injection

## Related Skills
- `skills/core/async-patterns/SKILL.md` — complete async patterns and examples
