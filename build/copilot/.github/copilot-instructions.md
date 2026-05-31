# Copilot Instructions

## async-concurrency

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

## coding-style

# C# Coding Style

Detect .NET version from `<TargetFramework>` in .csproj files.
Use only features available for the detected version.
Match the existing project style. Never force-upgrade syntax.

## DO (All Versions)

- Use file-scoped namespaces (.NET 6+)
- Use `var` for local variables when type is obvious from the right-hand side
- Use expression-bodied members for single-line methods and properties
- Use `sealed` on classes not designed for inheritance
- Use records for immutable data (event data, DTOs, value objects)
- Use `private set` on entity properties (query side)
- Use factory methods for aggregate creation
- Follow SOLID principles, clean code, and best practices

## DO NOT (All Versions)

- Do not use `DateTime.Now` -- use an injected time provider
- Do not use string concatenation for SQL -- use parameterized queries
- Do not use `async void` -- always return `Task` or `Task<T>`
- Do not catch generic `Exception` unless re-throwing
- Do not use `public set` on domain entity properties
- Do not guess package/framework APIs -- check official documentation first

## DO (Version-Specific)

Only use these when the detected .NET version supports them:
- Primary constructors for DI injection (.NET 8+ / C# 12)
- `required` modifier on properties that must be set (.NET 7+ / C# 11)
- Collection expressions `[..]` (.NET 8+ / C# 12)
- `field` keyword in properties (.NET 14+ / C# 14)

## Key Rule

Before writing any code, detect the project's .NET version and existing style.
Match the C# language level of the existing project.
When in doubt, use the more conservative syntax that works across more versions.

## Related Skills
- `skills/core/solid-principles/SKILL.md` — when to apply and when over-applying hurts
- `skills/core/design-patterns/SKILL.md` — pattern selection for modern C#
- `skills/core/coding-conventions/SKILL.md` — detailed convention patterns

## existing-projects

# Existing Project Rules

Core principle: Detect before generate. Respect before change. Check docs before using.

## Detection -- Always Scan First

Before generating any code, scan the project for:
- .NET version (`<TargetFramework>` in .csproj)
- Architecture pattern (folder structure, layer names)
- Naming conventions (existing classes, namespaces)
- NuGet packages (what is already used)
- Existing patterns (DI registration style, error handling, logging)

## Respect What Exists

- Use the same .NET version as the project
- Follow the same naming conventions, even if different from defaults
- Use the same packages -- do not introduce competing libraries
- Match the same code style (formatting, spacing, patterns)
- Do not change the project structure

## Extend, Don't Refactor

- Add new files following existing patterns
- Register new services the same way existing ones are registered
- Use the same base classes and interfaces the project already uses
- Match the same test structure and patterns

## Never During Implementation

- Never change .NET version
- Never refactor existing code while adding features
- Never introduce new architectural patterns alongside existing ones
- Never switch libraries (e.g., do not add Dapper if the project uses EF Core)
- Never reorganize folder structure
- Never guess package/framework APIs -- always check official documentation first
- Never deploy -- AI must never deploy to any environment
- Rollback strategies are documented but executed by the deployment pipeline, not by AI

## When No Project Exists

- Use defaults from config (company name, naming pattern)
- Use latest stable .NET version -- currently .NET 10 (or as configured)
- Follow the architecture recommended by the plan
- Apply full conventions from all other rules

## Related Skills

- `skills/workflow/sdd-lifecycle/`, `skills/core/coding-conventions/`

## security

# Security Rules

Every endpoint, every input, every secret — secure by default.

## MUST

- All API endpoints MUST have `[Authorize]` unless explicitly designed as public (annotate public endpoints with `[AllowAnonymous]` to signal intent)
- All user input MUST be validated at the API boundary before processing
- All output rendered in HTML MUST be encoded (`HtmlEncoder.Default.Encode()`)
- All SQL MUST use parameterized queries — never concatenate user input
- All secrets MUST use user secrets (dev) or Key Vault / environment variables (prod)
- All production APIs MUST enforce HTTPS
- All CORS policies MUST use explicit origins — never `AllowAnyOrigin()` with `AllowCredentials()`
- All file uploads MUST validate extension, MIME type, and size

## MUST NOT

- Do not store secrets in `appsettings.json`, source code, or environment-specific config files committed to git
- Do not log sensitive data (passwords, tokens, connection strings, PII)
- Do not return stack traces or internal exception details in production responses
- Do not disable CORS or use wildcard origins in production
- Do not use `@Html.Raw()` on user-provided content without sanitization
- Do not trust client-side validation alone — always re-validate server-side

## Security Headers

Production APIs should include:
- `Content-Security-Policy: default-src 'self'`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Detection Instructions

1. Check for endpoints missing `[Authorize]` — add or mark `[AllowAnonymous]` with comment
2. Check for raw SQL string concatenation — replace with parameterized queries
3. Check for secrets in appsettings.json — move to user secrets or Key Vault
4. Check for `AllowAnyOrigin()` combined with `AllowCredentials()` — fix CORS policy
5. Check for missing input validation on POST/PUT endpoints

## Related Skills
- `skills/security/auth-jwt/SKILL.md` — JWT authentication patterns
- `skills/security/auth-policies/SKILL.md` — policy-based authorization
- `skills/security/cors-configuration/SKILL.md` — CORS policy setup
- `skills/security/input-sanitization/SKILL.md` — XSS prevention, CSP headers
- `skills/security/data-protection/SKILL.md` — encryption, Key Vault

## tool-calls

# Tool Call Best Practices

## Sequential Tool Calls

Use sequential tool calls instead of chaining commands with `&&`.
Each tool call should be a single, focused operation.

### DO

- Run one command per tool call
- Check the result of each command before proceeding
- Use separate tool calls for build, test, and format steps

### DO NOT

- Do not chain commands with `&&` (e.g., `dotnet build && dotnet test`)
- Do not chain commands with `;` unless failures are acceptable
- Do not use `||` for fallback logic in a single tool call
- Do not combine unrelated operations in one shell invocation

### Example -- Correct

Step 1: `dotnet build`
Step 2: (check result) then `dotnet test`
Step 3: (check result) then `dotnet format --verify-no-changes`

### Example -- Incorrect

Single call: `dotnet build && dotnet test && dotnet format --verify-no-changes`

## Tool Availability

Before constructing a command, verify the tool is available:

- Check if `dotnet` is on PATH before running .NET commands
- Check if `git` is on PATH before running git commands
- Check if `gh` is on PATH before running GitHub CLI commands
- Check if `docker` is on PATH before running container commands

If a tool is not available, inform the user and suggest installation:

| Tool     | Install URL                             |
|----------|-----------------------------------------|
| dotnet   | https://dot.net/download                |
| git      | https://git-scm.com/downloads           |
| gh       | https://cli.github.com                  |
| docker   | https://docs.docker.com/get-docker/     |

## Error Handling

- Read the full error output before retrying a command
- Do not retry the same command without changing something
- Report clear error messages to the user with suggested fixes

## Related Skills

- `skills/workflow/systematic-debugging/`

