# dotnet-ai-kit - Rules Design

## Rules Philosophy

Rules are always loaded into context (max 100 lines each, ~900 lines total).
They enforce company conventions (from config) without requiring explicit skill loading.
Rules are company-agnostic — they use `{Company}` placeholder resolved from `.dotnet-ai-kit/config.yml`.
Each rule file includes YAML frontmatter with `alwaysApply: true` and a `description` field, following the Claude Code rules format.

---

## Rule Files (16 rules)

### 1. `.claude/rules/naming.md` - Naming Conventions

```yaml
---
alwaysApply: true
description: Enforces naming conventions using configured company name and detected project patterns.
---
```

**Conventions** (company-agnostic, uses config):

#### Microservice Mode
- Solution: `{Company}.{Domain}.{Side}.sln` (e.g., `Acme.Competition.Commands.sln`)
- Projects: `{Company}.{Domain}.{Side}.{Layer}` (e.g., `Acme.Competition.Commands.Domain`)
- Layers: Domain, Application, Infra, Grpc, Test, Test.Live
- Service Bus Topics: `{company}-{domain}-{side}` (e.g., `acme-competition-commands` where company=acme, domain=competition, side=commands)
- K8s: `{environment}-manifest.yaml`

#### Generic Mode
- Solution: `{Company}.{ProjectName}.sln` or `{ProjectName}.sln`
- Projects: Follow detected convention or `{Company}.{ProjectName}.{Layer}`
- Layers: Depends on architecture (VSA: Features/, Clean Arch: Domain/Application/Infrastructure/API)

#### Both Modes
- Aggregates: PascalCase singular (Account, Competition, SoldCard)
- Events: `{Aggregate}{Action}` (CompetitionCreated, AccountLinkedToGateway)
- Event Data: `{EventName}Data` record (CompetitionCreatedData)
- Handlers: `{EventName}Handler` or `{CommandName}Handler`
- Commands: `{Action}{Aggregate}Command` (RegisterAmbassadorCommand)
- Queries: `Get{Entities}Query` (GetAccountsQuery)
- Output DTOs: `{Entity}Output` or `Get{Entities}Output`
- Proto services: `{Domain}{Side}` (AccountCommands, AccountQueries)
- Proto files: `snake_case.proto` (account_commands.proto)
- Repositories: `I{Entity}Repository` / `{Entity}Repository`
- Fakers: `{Entity}Faker`, `{Event}Faker`
- Asserts: `{Entity}Assert` or `{Entity}sAssert`
- Extensions: `{Entity}{Side}Extensions` (AccountCommandExtensions)
- Resources: `Phrases.resx` / `Phrases.en.resx`

**Key Rule**: If an existing project has different naming conventions, FOLLOW the existing ones.
Only apply these conventions for new files/projects.

---

### 2. `.claude/rules/coding-style.md` - C# Style

```yaml
---
alwaysApply: true
description: Enforces C# coding conventions, version-aware (respects detected .NET version).
---
```

**Version-Aware Rules**:
- Detect .NET version from `<TargetFramework>` in .csproj files
- Use features available for the detected version
- Do NOT upgrade syntax to newer version unless asked

**DO** (all versions):
- Use file-scoped namespaces (.NET 6+)
- Use `var` for local variables when type is obvious
- Use expression-bodied members for single-line methods
- Use `sealed` on classes that shouldn't be inherited
- Use records for immutable data (event data, DTOs)
- Use `private set` on entity properties (query side)
- Use factory methods for aggregate creation
- Don't use `DateTime.Now` - use injected time provider
- Don't use string concatenation for SQL - use parameterized queries
- Don't use `async void` - always return Task
- Don't catch generic `Exception` unless re-throwing
- Don't use `public set` on domain entities
- Follow SOLID principles, clean code, and best practices
- Before using any package or framework feature, check the official documentation first — don't guess APIs

**DO** (version-specific, only when detected version supports it):
- Primary constructors for DI injection (.NET 8+)
- `required` on properties that must be set (.NET 7+)
- Collection expressions `[..]` (.NET 8+)
- `field` keyword (.NET 14+)

**Key Rule**: Match the C# language level of the existing project. Never force-upgrade.

---

### 3. `.claude/rules/localization.md` - Localization Rules

```yaml
---
alwaysApply: true
description: Enforces resource-based localization in all projects using resource files.
---
```

**Rules**:
- NEVER use plain strings in gRPC responses or error messages
- ALWAYS use `Phrases.{Key}` from resource files
- Default culture from config (as configured)
- Secondary language in `Phrases.{lang}.resx`
- Use EntitiesLocalization for entity display names (microservice mode)
- ThreadCultureInterceptor handles culture switching via "language" gRPC header (microservice mode)
- Control panel uses IStringLocalizer (microservice mode)
- For generic projects: use IStringLocalizer or Phrases pattern based on what's already in the project

**Key Rule**: If the existing project doesn't use localization, don't add it unless asked.
If it uses a different pattern (IStringLocalizer vs Phrases), follow the existing pattern.

---

### 4. `.claude/rules/error-handling.md` - Error Handling

```yaml
---
alwaysApply: true
description: Enforces error handling patterns appropriate to the project mode.
---
```

**Microservice Mode**:
- Domain exceptions implement `IProblemDetailsProvider`
- ApplicationExceptionInterceptor converts to RpcException
- Problem details include: Type, Title, Status, Detail
- Status code mapping: NotFound → gRPC NotFound, Conflict → AlreadyExists
- gRPC metadata key: `problem-details-bin`
- Control panel uses ResponseResult<T> with Switch pattern
- Idempotent handlers return true for AlreadyExists RpcException

**Generic Mode**:
- Use Result<T> pattern (Result.Success, Result.Failure) or ProblemDetails RFC 9457
- Map to HTTP status codes via ProblemDetails
- Use global exception handler middleware
- FluentValidation → ValidationException → 400 Bad Request

**Both Modes**:
- Never swallow exceptions - log then re-throw or return false for retry
- Never return generic error messages to users
- Use structured logging for exception context
- Client must send an ID for idempotency — never generate idempotency keys server-side
- For retry scenarios, use client-provided correlation IDs

**Key Rule**: Detect and follow the existing error handling pattern in the project.

---

### 5. `.claude/rules/architecture.md` - Architecture Rules

```yaml
---
alwaysApply: true
description: Enforces architectural boundaries appropriate to the detected architecture pattern.
---
```

**Microservice Mode**:
- Domain layer has ZERO external dependencies
- Application depends only on Domain
- Infrastructure implements Domain/Application interfaces
- Grpc references Application and Infrastructure
- MediatR for CQRS dispatch (IRequest/IRequestHandler)
- Event<T> for all domain events
- Outbox pattern for reliable publishing (command side)
- Sequence-based idempotency (query side)
- UnitOfWork for transaction management
- Options pattern for all configuration
- gRPC for inter-service communication
- Azure Service Bus for event messaging
- Resource files for all user-facing strings
- Row version + concurrency tokens for SQL Server entities (sequence in most entities)
- Event catalogue maintained per service
- Event versioning with versioned handlers for schema evolution

**Generic Mode - Clean Architecture**:
- Domain → Application → Infrastructure → API/Web
- No circular dependencies between layers
- Domain has no dependencies on infrastructure

**Generic Mode - Vertical Slice**:
- Feature folder per operation
- Each slice is independent
- Shared infrastructure via DI, not direct reference

**Generic Mode - DDD**:
- Bounded contexts with clear boundaries
- Aggregates enforce invariants
- Domain events for cross-aggregate communication

**Key Rule**: DETECT the architecture from the existing project structure before applying rules.
If the project uses a different pattern than expected, follow what exists.

---

### 6. `.claude/rules/existing-projects.md` - Existing Project Rules

```yaml
---
alwaysApply: true
description: Rules for working with existing codebases - detect, respect, extend.
---
```

**Core Principle**: Detect before generate. Respect before change. Check docs before using.

**Detection Rules**:
1. **Always scan first** - Before generating any code, scan the project for:
   - .NET version (`<TargetFramework>` in .csproj)
   - Architecture pattern (folder structure, layer names)
   - Naming conventions (existing classes, namespaces)
   - NuGet packages (what's already used)
   - Existing patterns (DI registration style, error handling, logging)

2. **Respect what exists**:
   - Use the same .NET version as the project
   - Follow the same naming conventions (even if different from our defaults)
   - Use the same packages (don't introduce competing libraries)
   - Match the same code style (formatting, spacing, patterns)
   - Don't change the project structure

3. **Extend, don't refactor**:
   - Add new files following existing patterns
   - Register new services the same way existing ones are registered
   - Use the same base classes and interfaces the project already uses
   - Match the same test structure and patterns

**Never During Implementation**:
- Never change .NET version
- Never refactor existing code while adding features
- Never introduce new architectural patterns alongside existing ones
- Never switch libraries (e.g., don't add Dapper if the project uses EF Core)
- Never reorganize folder structure
- Never guess package/framework APIs — always check official documentation first
- Never deploy — AI must never deploy to any environment. Use K8s manifests + GitHub Actions for deployments
- Rollback strategies are documented but executed by the deployment pipeline, not by AI

**When No Project Exists**:
- Use defaults from config (company name, naming pattern)
- Use latest stable .NET version — currently .NET 10 (or as configured)
- Follow the architecture recommended by `/dotnet-ai.plan`
- Apply full conventions from rules 1-5

---

## Rules Summary

| Rule | Lines | Focus |
|------|-------|-------|
| naming.md | ~80 | Company-agnostic naming, mode-aware, respect-existing |
| coding-style.md | ~60 | Version-aware C# style, no force-upgrade |
| localization.md | ~40 | Resource files, conditional on project usage |
| error-handling.md | ~55 | Mode-aware error patterns (microservice vs generic) |
| architecture.md | ~80 | Multi-architecture layer boundaries |
| existing-projects.md | ~65 | Detect & respect existing codebases |
| multi-repo.md | ~46 | Event contract ownership, cross-repo branch naming, deploy order, no circular deps |
| **TOTAL** | **~826** | Max budget: 900 lines (16 × avg ~52 lines) |

---

