# dotnet-ai-kit v2 — Full Artifact Catalog

**Date:** 2026-05-30 · **Extends:** [22-v2-project-structure.md](22-v2-project-structure.md) · [21-v2-architecture-blueprint.md](21-v2-architecture-blueprint.md)

Every artifact that ships in v2, with a one-line preview. **Existing** previews are the artifacts' *real* `description:` fields (trimmed); **🆕 NEW** items come from the expansion research (grounded, 2026-05-30); **🔀 MERGE** marks v1 duplicates being consolidated.

**Counts:** 32 commands (27 + 5 lifecycle additions) · 15 agents (13 kept + 2 new) · 21 rules (16 + 5 new) · 12 profiles · ~130 existing skills (− a few merges) + ~30 new skills. *(The new commands + the enforcement/selector/multi-repo decisions are detailed in [24](24-v2-selector-gates-lifecycle-multirepo.md); the full testable requirements are in [25](25-v2-requirements.md).)*

**Invocation legend:** `[cmd]` = command-skill (`disable-model-invocation: true`, shows as slash command, user-only) · `[auto]` = model-invocable knowledge skill · `[bg]` = background (`user-invocable: false`).

---

## 1. Commands (27) — authored as command-skills `[cmd]`

All carry `disable-model-invocation: true` → they surface as `/dotnet-ai:<name>` (+ `/dai:<alias>`), user-driven, zero always-on budget. Each bundles its workflow script + examples.

### SDD lifecycle
- **do** — runs the full SDD lifecycle from spec to PR (one-command feature builder)
- **specify** — creates a feature specification from a description
- **clarify** — resolves ambiguities in a feature specification
- **plan** — generates an implementation plan from the spec
- **tasks** — breaks the plan into ordered, dependency-aware tasks
- **analyze** — cross-artifact consistency check before coding
- **implement** — executes all planned implementation tasks
- **review** — reviews code against standards and conventions
- **verify** — verifies build, tests, and formatting pass
- **pr** — creates a pull request with linked changes

### Code generation
- **add-aggregate** — event-sourced aggregate + events (command side)
- **add-entity** — query-side read-model entity + handler
- **add-event** — new domain event for an existing aggregate
- **add-endpoint** — API endpoint with request/response
- **add-page** — Blazor control-panel page with data grid
- **add-crud** — full CRUD stack (entity, handlers, endpoint, tests)
- **add-tests** — test suite for existing code

### Project & smart
- **init** — initialize dotnet-ai-kit in a .NET solution
- **configure** — interactive configuration wizard
- **detect** — detect architecture, .NET version, patterns
- **learn** — generate a project constitution + topic split
- **docs** — generate docs (readme, api, adr, deploy, release, service, code, feature, all)
- **status** — current feature progress and next step
- **undo** — safely revert the last AI-generated changes
- **explain** — explain a pattern with examples

### Session
- **checkpoint** — save a progress checkpoint for handoff
- **wrap-up** — end session with summary + handoff notes

### 🆕 Lifecycle additions (see [24](24-v2-selector-gates-lifecycle-multirepo.md))
- **constitution** 🆕 — establish/amend the project's governing principles (splits from `learn`); gates analyze/review
- **checklist** 🆕 — generate + run a feature-specific quality checklist as a gate (before implement / before PR)
- **orchestrate** 🆕 — the **multi-repo conductor**: init every affected repo, project `feature-brief.md` to each, sequence implementation by dependency, report cross-repo status
- **release** 🆕 — post-merge close-out: version bump + changelog + tag + GitHub release (+ optional deploy hook)
- **fix** 🆕 — TDD bug-fix loop: write a failing test reproducing the symptom → fix → verify it passes
- *(+ `tasks --issues` flag — convert tasks to linked GitHub issues)*
- *Note: `constitution` splits from `learn` (`learn` = extract knowledge; `constitution` = author/amend governing principles).*

---

## 2. Agents (15)

Specialist subagents; each **references** the skills it owns (no bundled resources of their own). Projected per tool (Claude `.md`, Codex `.toml`, Cursor `.md`, Copilot `.agent.md`).

### Kept (13)
- **dotnet-architect** — leads overall .NET solution architecture and design patterns
- **api-designer** — designs REST and gRPC API contracts and endpoint conventions
- **command-architect** — architects CQRS command-side aggregates and event sourcing
- **query-architect** — architects CQRS query-side read models and projections
- **cosmos-architect** — designs Cosmos DB data models and query-side projections
- **processor-architect** — architects background processors and event-handler services
- **gateway-architect** — designs API gateway routing, aggregation, and BFF patterns
- **controlpanel-architect** — designs Blazor admin control-panel UI and workflows
- **ef-specialist** — manages EF Core models, migrations, and queries
- **devops-engineer** — manages CI/CD pipelines, Docker, and infrastructure as code
- **docs-engineer** — generates and maintains project documentation and ADRs
- **test-engineer** — designs unit, integration, and E2E test suites
- **reviewer** — reviews code for quality, patterns, and architectural compliance

### 🆕 New (2)
- **aspire-architect** 🆕 — owns Aspire AppHost topology, ServiceDefaults, integrations, deployment
- **ai-engineer** 🆕 — owns LLM integration (Microsoft.Extensions.AI), prompt/tooling design, eval, provider abstraction

> The v1 `dotnet-ai-architect` is a Cursor spike **fixture** → moved to `tests/fixtures/` (not a shipped agent).

---

## 3. Rules (21)

### Conventions — universal, always-on (5 + 2 new)
- **coding-style** — C# coding conventions, version-aware
- **async-concurrency** — async/await correctness, CancellationToken propagation, no blocking
- **security** — auth, input validation, secrets, CORS, output encoding
- **existing-projects** — detect, respect, extend existing codebases
- **tool-calls** — sequential tool calls + verify tool availability
- **mediator-abstraction** 🆕 — dispatch CQRS through a thin `ISender`/`IMediator` port (MediatR is now commercial)
- **deterministic-enforcement** 🆕 — declares which rules have a paired Roslyn analyzer (keeps advisory + deterministic layers in sync)

### Domain — path-scoped, JIT-loaded (11 + 3 new)
- **api-design** — REST conventions: status codes, ProblemDetails, versioning, endpoints
- **architecture** — architectural boundaries for the detected pattern
- **configuration** — strongly-typed Options pattern with startup validation
- **data-access** — EF Core efficiency, DbContext lifetime, no N+1
- **error-handling** — error patterns appropriate to project mode (Result/ProblemDetails/RpcException)
- **localization** — resource-based localization across projects
- **multi-repo** — event-contract + deployment conventions for microservices
- **naming** — naming conventions from company name + detected patterns
- **observability** — structured logging, tracing, health checks, metrics
- **performance** — no N+1, caching, efficient async, memory awareness
- **testing** — test naming, structure, isolation (.NET + Python)
- **messaging-bus-selection** 🆕 — choose a bus given the MassTransit v9 license change; abstract behind `IMessageBus`
- **testing-platform** 🆕 — standardize on Microsoft.Testing.Platform runner config
- **ai-integration** 🆕 — Microsoft.Extensions.AI vs Semantic Kernel vs Agent Framework; pin provider previews

---

## 4. Profiles (12) — architecture hard-constraints (path-scoped, hook-injected)

### Generic (5)
- **clean-arch** — Clean Architecture 4-layer dependency direction
- **vsa** — Vertical Slice Architecture feature folders
- **ddd** — Domain-Driven Design aggregates/value-objects/bounded-contexts
- **modular-monolith** — module isolation + inter-module communication
- **generic** — baseline .NET constraints (no specific architecture)

### Microservice (7)
- **command** — event-sourced write side
- **query-sql** — SQL read side
- **query-cosmos** — Cosmos read side
- **processor** — background event processor
- **gateway** — REST gateway over gRPC
- **controlpanel** — Blazor WASM module
- **hybrid** — combined command + query

---

## 5. Skills

### 5.1 Existing skills by category (the rebuild set)

**api/**
- caching-strategies — distributed cache, output cache, ETags
- content-negotiation — response formats, custom formatters, Accept headers
- controller-patterns — controller REST APIs: action results, model binding, MediatR
- controllers 🔀 — RESTful controllers w/ MediatR + ProblemDetails *(merge → controller-patterns)*
- grpc-design — gRPC services, proto files, gRPC-Web/JSON transcoding
- minimal-api — minimal endpoints: route groups, filters, TypedResults
- openapi-scalar — OpenAPI spec generation + Scalar UI
- scalar 🔀 — Scalar API docs UI *(merge → openapi-scalar)*
- rate-limiting — rate limiting / throttling
- signalr-realtime — SignalR hubs, WebSockets, push
- versioning — API versioning / multiple versions

**architecture/**
- advisor — choose a pattern (VSA/Clean/DDD/Modular/Micro) for a new project
- clean-architecture — 4-layer separation + dependency inversion
- cqrs-basics 🔀 — CQRS read/write + MediatR behaviors *(→ decision-guide linking cqrs/)*
- ddd-patterns — aggregates, value objects, domain events, bounded contexts
- modular-monolith — module isolation + inter-module communication
- multi-tenancy — tenant isolation, per-tenant DB, query filters
- vertical-slice — feature folders + co-located code

**core/**
- async-patterns — async code, CancellationToken propagation, pitfalls
- coding-conventions — C# style: namespaces, sealed, var, XML docs
- configuration — IConfiguration, Options pattern, appsettings, secrets
- csharp-idioms — records, pattern matching, primary ctors, collection expressions
- dependency-injection — registration, lifetimes, decorator/keyed services
- design-patterns — factory, builder, strategy, decorator, mediator
- error-handling — domain exceptions, ProblemDetails, RpcException mapping
- fluent-validation — FluentValidation validators, custom/async rules
- functional-csharp — Result types, railway-oriented, immutability
- mapping-strategies — DTO↔domain: manual, LINQ projections, AutoMapper *(note: AutoMapper now commercial — see mediator-abstraction rationale)*
- modern-csharp — C# 12/13/14 features
- solid-principles — evaluating/applying SOLID
- coding-conventions, csharp-idioms, modern-csharp 🔀 — *consider consolidating the three style skills*

**cqrs/** *(decouple from MediatR namespace per mediator-abstraction)*
- command-generator — new CQRS command + handler + validator
- query-generator — new CQRS query + handler + DTO + pagination
- request-response — CQRS contracts w/ FluentValidation + Result
- mediatr-handlers — request/notification handlers, dispatch
- notification-handlers — domain events via notifications, multiple handlers
- pipeline-behaviors — cross-cutting behaviors (validation/logging/transactions)

**data/**
- audit-trail — automatic CreatedAt/UpdatedBy via EF interceptors
- dapper — read-optimized queries alongside EF Core
- db-transactions — transactions, isolation levels, cross-context coordination
- ef-core-basics — DbContext config, entity config, connection resiliency
- ef-migrations — create/apply/manage EF Core migrations
- ef-queries — LINQ, raw SQL, compiled queries, N+1 fixes
- repository-patterns — repository + Unit of Work + specification
- specification-pattern — composable query criteria

**detection/**
- smart-detect — detect project type, architecture, solution structure

**devops/**
- aspire-orchestration 🔀refresh — .NET Aspire local orchestration *(deepen → Aspire 13.1; see §5.2)*
- azure-resources — provision Service Bus, Cosmos, SQL
- dockerfile — write/optimize Dockerfiles for .NET
- github-actions — CI/CD workflows for build/test/deploy
- kubernetes — K8s manifests for .NET microservices

**docs/**
- adr — Architecture Decision Records
- api-docs — generate/enrich API docs from OpenAPI
- architecture-docs — document architecture with Mermaid + topology
- changelog-gen — changelogs from git history / release notes
- diagram-gen — Mermaid architecture/event-flow/sequence diagrams
- onboarding — developer onboarding/setup guides
- readme-gen — README from project analysis
- runbook — deployment runbooks, troubleshooting, rollback

**infra/**
- background-jobs — background jobs, recurring tasks, Hangfire
- email-notifications — email w/ templates, SendGrid, SES
- feature-flags — feature flags, percentage rollouts, runtime toggles
- file-storage — upload/download via Azure Blob or local FS

**microservice/command/**
- aggregate-design — event-sourced aggregate roots
- aggregate-testing — tests for event-sourced aggregates
- command-handler — MediatR command handlers (event-sourced)
- event-design — domain events w/ Event<TData> hierarchy
- event-store — EF Core event store w/ discriminator mapping
- event-versioning — evolve event schemas / migrate event data
- outbox — reliable event publishing via outbox + Service Bus

**microservice/query/**
- query-entity — query-side entities w/ private setters + event state
- query-handler — MediatR query handlers w/ pagination/filtering/DTOs
- event-handler — query-side event handlers w/ sequence checking + idempotency
- listener-pattern — Service Bus session listeners as IHostedService
- sequence-checking — inline sequence validation for idempotent processing

**microservice/cosmos/**
- cosmos-entity — Cosmos document entities w/ partition keys + discriminators
- cosmos-repository — Cosmos repository w/ LINQ + FeedIterator pagination
- partition-strategy — partition-key choice + cross-partition queries
- transactional-batch — atomic multi-doc ops via TransactionalBatch

**microservice/processor/**
- batch-processing — batch event processing w/ BackgroundService + concurrency
- event-routing — route Service Bus events by subject to MediatR handlers
- grpc-client — call external gRPC services w/ retry + client factory
- hosted-service — IHostedService w/ ServiceBusSessionProcessor + DLQ

**microservice/gateway/**
- endpoint-registration — register gRPC client factories + service URLs
- gateway-endpoint — REST gateway controllers delegating to gRPC
- gateway-security — JWT auth, policies, role-based access on gateway
- scalar-docs — Scalar API docs for gateway endpoints

**microservice/controlpanel/**
- blazor-component — MudBlazor data grids, dialogs, forms
- gateway-facade — typed HttpClient wrappers for control-panel calls
- mudblazor-patterns — MudBlazor theming, dialogs, snackbar
- query-string-bindable — sync filter models with URL query strings
- response-result — ResponseResult<T> + Switch pattern in UI

**microservice/grpc/**
- service-definition — proto files + gRPC service classes w/ MediatR
- validation — FluentValidation on gRPC requests (Calzolari)
- interceptors — gRPC interceptors: exception mapping, culture, claims

**microservice/** (cross-cutting)
- event-catalogue — document cross-service event schemas / event registry *(fix broken reflection sample, [event-catalogue/SKILL.md:189](skills/microservice/event-catalogue/SKILL.md))*

**observability/**
- health-checks — health endpoints, K8s probes, health UI
- opentelemetry — distributed tracing, metrics, OTLP exporters
- serilog-structured — Serilog structured logging, enrichers, Seq

**quality/**
- architectural-fitness — NetArchTest architecture tests
- code-analysis — Roslyn analyzers, StyleCop, EditorConfig
- review-checklist — standards-based review checklists + severity

**resilience/**
- circuit-breaker — circuit breaker against cascading failures
- polly-resilience — Polly v8 pipelines: retry/timeout/fallback
- retry-patterns — retry w/ exponential backoff + jitter

**security/**
- auth-jwt — JWT auth, token generation, refresh flows
- auth-policies — policy-based authorization w/ custom requirements
- cors-configuration — CORS policies for .NET APIs
- data-protection — encrypt at rest via Data Protection API
- input-sanitization — XSS prevention, CSP headers, upload validation

**testing/**
- unit-testing — xUnit, NSubstitute/Moq, FluentAssertions
- integration-testing — WebApplicationFactory, Testcontainers, fixtures
- performance-testing — BenchmarkDotNet, load/throughput
- test-fixtures — Bogus fakers, assertion extensions, helpers

**workflow/** (process skills)
- sdd-lifecycle — the SDD lifecycle from plan through ship
- plan-templates — mode-specific implementation-plan templates
- plan-artifacts — supporting artifacts (briefs, service maps)
- feature-tracking — feature status + directories + multi-service coordination
- multi-repo-workflow — coordinate changes across repos
- git-worktree-isolation — isolate feature work in worktrees
- code-review-workflow — review completed implementation pre-merge
- receiving-review-feedback — process CodeRabbit/PR feedback before changing code
- verification-gate — require verification before claiming done
- systematic-debugging — debug methodically before proposing fixes
- session-management — checkpoint / wrap-up / handoff

### 5.2 🆕 New skills by domain (rebuild + expand)

**Aspire (13.1)** — `aspire-architect` agent owns these
- aspire-integrations 🆕 — hosting integration packages (Redis/PG/RabbitMQ/SB) + WithReference wiring
- aspire-deployment 🆕 — `aspire deploy`, publishers, container-registry resources, azd → ACA
- aspire-testing 🆕 — `Aspire.Hosting.Testing` end-to-end tests over the app graph

**AI integration** — `ai-engineer` agent owns these
- extensions-ai-chat 🆕 — `IChatClient` + middleware pipeline (DI, tool invocation, OTel, caching)
- extensions-ai-embeddings 🆕 — `IEmbeddingGenerator` + vector store for RAG/semantic search

**Minimal APIs / ASP.NET Core 10**
- minimal-api-patterns 🆕 — route groups, `Results<T1,T2>` unions, `[AsParameters]`, controllers-vs-minimal guide
- endpoint-filters 🆕 — `IEndpointFilter` for cross-cutting concerns
- minimal-api-validation 🆕 — source-generated `AddValidation()` + `[ValidatableType]`
- server-sent-events 🆕 — `TypedResults.ServerSentEvents()` / `SseItem<T>` streaming

**Messaging & mediator**
- mediator-migration 🆕 — migrate off MediatR to source-gen Mediator / Wolverine (or pin <13)
- masstransit-consumers 🆕 — consumers, retry/redelivery, RabbitMQ + Azure SB (w/ license caveat)
- masstransit-sagas 🆕 — saga state machines + persistence + correlation
- wolverine-messaging 🆕 — MIT alternative: handlers, outbox/inbox, mediator mode
- dapr-building-blocks 🆕 — `DaprClient` state/pub-sub/invocation + component YAML
- dapr-pubsub 🆕 — topic subscriptions, CloudEvents, dead-letter
- dapr-workflow 🆕 — durable orchestration via Dapr Workflow SDK

**Roslyn (deterministic enforcement)**
- roslyn-analyzer 🆕 — author `DiagnosticAnalyzer` + `CodeFixProvider` for kit conventions
- incremental-source-generator 🆕 — `IIncrementalGenerator` done right (ForAttributeWithMetadataName, equatable models)
- analyzer-packaging 🆕 — package as `analyzers/dotnet/cs` + `.editorconfig` severity

**Modern testing**
- playwright-e2e 🆕 — cross-browser E2E for the Blazor control panel
- mutation-testing 🆕 — Stryker.NET w/ mutation-score CI threshold
- tunit-testing 🆕 — source-gen, MTP-native testing (opt-in; flag pre-1.0)

**Blazor (.NET 10)**
- blazor-render-modes 🆕 — Static SSR / Interactive Server/WASM/Auto per component
- blazor-persistent-state 🆕 — `[PersistentState]` + circuit persistence across reconnects
- blazor-hybrid 🆕 (low priority) — reuse control-panel components in MAUI Blazor Hybrid

**Auth**
- entra-id-auth 🆕 — `Microsoft.Identity.Web` for Entra ID (OIDC, downstream tokens, MI)
- openiddict-server 🆕 — self-hosted OAuth2/OIDC server (OpenIddict 10.x; CVE-2026-40372 patch)
- passkeys-webauthn 🆕 — ASP.NET Core 10 Identity passkey/WebAuthn

**GraphQL**
- graphql-hotchocolate 🆕 — HotChocolate v15 queries/mutations/subscriptions/DataLoader/@authorize

---

### Notes
- **Consolidation (🔀):** `controllers`→`controller-patterns`, `scalar`→`openapi-scalar`, `cqrs-basics`→decision-guide; review the three core style skills (`coding-conventions`/`csharp-idioms`/`modern-csharp`) for merge. Each merge reclaims an always-on listing slot.
- **Licensing follow-through:** `cqrs/*` and `mapping-strategies` reference MediatR/AutoMapper, both now commercial — decouple per the `mediator-abstraction` rule.
- **Every skill** ships the resource model from [22 §2](22-v2-project-structure.md): `scripts/` (.py default), `examples/` (compilable C#), `references/`, `assets/`, `evals/`.
