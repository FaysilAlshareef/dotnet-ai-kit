# dotnet-ai-kit - Expanded Skills Inventory (Microservices + Generic .NET)

## Skill Sources

| Source | Skills | Focus |
|--------|--------|-------|
| **Our Projects** | ~30 | CQRS, Event Sourcing, Service Bus, Cosmos DB, gRPC microservices |
| **dotnet-claude-kit** | ~20 adapted | Modern C#, Architecture, APIs, Resilience, Observability |
| **dotnet-clean-architecture-skills** | ~10 adapted | Clean Arch, DDD, Repository, Pipeline, Dapper |

**Total: ~120 skills** (deduplicated, merged where overlap exists)
> For the 27 command definitions, see `04-commands-design.md`. For the command alias system, see Section G in that file.

---

## Architecture Modes

dotnet-ai-kit supports TWO modes:

### Mode 1: Microservices (CQRS + Event Sourcing)
- Our patterns
- Multi-repo orchestration
- Event-driven architecture
- gRPC inter-service communication

### Mode 2: Generic .NET Project
- VSA, Clean Architecture, DDD, Modular Monolith
- REST APIs with Minimal API or Controllers
- Standard EF Core, Dapper
- Single-repo or multi-project solutions

The `/dotnet-ai.init` or `/dotnet-ai.configure` command detects or asks which mode.

> For detailed code patterns and content specifications for generic .NET skills (Categories 1-8), see `14-generic-skills-spec.md`.

---

## CATEGORY 1: Core Language & Style (4 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 1 | `core/modern-csharp` | dotnet-claude-kit | C# 13/14 features: primary constructors, records, collection expressions, field keyword, pattern matching |
| 2 | `core/coding-conventions` | Original | Company-agnostic naming, file-scoped namespaces, sealed classes, expression bodies |
| 3 | `core/dependency-injection` | dotnet-claude-kit | Keyed services, scoped/transient/singleton, decorator pattern, factory delegates |
| 4 | `core/configuration` | dotnet-claude-kit | Options pattern, IOptionsSnapshot, secrets management, ValidateOnStart |

---

## CATEGORY 2: Architecture (5 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 5 | `architecture/advisor` | dotnet-claude-kit | Questionnaire → recommend VSA, Clean Arch, DDD, Modular Monolith, or Microservices |
| 6 | `architecture/vertical-slice` | dotnet-claude-kit | Feature folders, one handler per operation, minimal ceremony |
| 7 | `architecture/clean-architecture` | Combined | 4-layer pattern, dependency inversion, use case handlers |
| 8 | `architecture/ddd` | Combined | Aggregates, value objects, domain events, strongly-typed IDs |
| 9 | `architecture/project-structure` | dotnet-claude-kit | .slnx, Directory.Build.props, central package management |

---

## CATEGORY 3: Web API (5 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 10 | `api/minimal-api` | dotnet-claude-kit | IEndpointGroup auto-discovery, TypedResults, endpoint filters, OpenAPI |
| 11 | `api/controllers` | clean-arch-skills | RESTful controllers with routing, versioning, MediatR integration |
| 12 | `api/versioning` | dotnet-claude-kit | Asp.Versioning strategies (URL/header/query) |
| 13 | `api/openapi` | dotnet-claude-kit | Native OpenAPI support, transformers, security schemes |
| 14 | `api/scalar` | dotnet-claude-kit | Scalar UI setup, themes, authentication prefill |

---

## CATEGORY 4: Data Access (5 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 15 | `data/ef-core` | Combined | DbContext, migrations, interceptors, compiled queries, value converters, row version, concurrency tokens |
| 16 | `data/repository-pattern` | clean-arch-skills | Repository interfaces, EF Core implementations per aggregate root |
| 17 | `data/dapper` | clean-arch-skills | Multi-mapping, pagination, dynamic filtering, CTEs |
| 18 | `data/specification-pattern` | clean-arch-skills | Composable query criteria, includes, ordering, pagination |
| 19 | `data/audit-trail` | clean-arch-skills | IAuditable interface, EF interceptor, CreatedAt/UpdatedAt auto-population |

---

## CATEGORY 5: CQRS & Messaging (4 skills - generic)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 20 | `cqrs/command-generator` | clean-arch-skills | Commands + handlers + validators using MediatR |
| 21 | `cqrs/query-generator` | clean-arch-skills | Queries + handlers + response DTOs with Dapper |
| 22 | `cqrs/pipeline-behaviors` | clean-arch-skills | Logging, validation, transaction, caching behaviors |
| 23 | `cqrs/domain-events` | Combined | Domain events, handlers, outbox pattern (generic version) |

---

## CATEGORY 6: Error Handling & Resilience (3 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 24 | `resilience/result-pattern` | Combined | Result<T>, Error types, ProblemDetails RFC 9457 |
| 25 | `resilience/polly` | dotnet-claude-kit | Retry, circuit breaker, timeout, fallback, hedging |
| 26 | `resilience/caching` | dotnet-claude-kit | HybridCache, output caching, distributed cache patterns. Cache invalidation notes provided as dev team guidance |

---

## CATEGORY 7: Security (3 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 27 | `security/jwt-authentication` | clean-arch-skills | Token generation, validation, refresh tokens, claims |
| 28 | `security/permission-authorization` | clean-arch-skills | HasPermission attribute, policy provider, handlers |
| 29 | `security/security-scan` | dotnet-claude-kit | CVEs, secrets detection, OWASP patterns, auth audit |

---

## CATEGORY 8: Observability (3 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 30 | `observability/serilog` | Combined | Two-stage bootstrap, enrichers, Seq sink, structured logging, distributed tracing correlation |
| 31 | `observability/opentelemetry` | dotnet-claude-kit | Traces, metrics, IMeterFactory, Aspire Dashboard, distributed tracing with Seq + recommended exporters |
| 32 | `observability/health-checks` | clean-arch-skills | DB checks, HTTP checks, custom checks, K8s readiness |

---

## CATEGORY 9: Microservice - Event Sourcing (6 skills) [OUR PATTERNS]

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 33 | `microservice/event-structure` | Internal projects | Event<TData>, IEventData, EventType, sequence tracking |
| 34 | `microservice/aggregate` | Internal projects | Aggregate<T>, LoadFromHistory, ApplyChange, factory methods |
| 35 | `microservice/event-sourcing-flow` | Internal projects | Complete flow: handler → aggregate → event → DB → outbox → bus |
| 36 | `microservice/outbox-pattern` | Internal projects | OutboxMessage, CommitEventService, ServiceBusPublisher |
| 37 | `microservice/command-handler` | Internal projects | IRequestHandler with validation, aggregate commit, output |
| 38 | `microservice/command-db-config` | Internal projects | ApplicationDbContext, discriminator, GenericEventConfiguration |

---

## CATEGORY 10: Microservice - Query Side (5 skills) [OUR PATTERNS]

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 39 | `microservice/query-entity` | Internal projects | Private setters, CTO constructors, sequence-based concurrency, row version, rich models |
| 40 | `microservice/query-event-handler` | Internal projects | Strict sequence checking, idempotent, entity state changes |
| 41 | `microservice/service-bus-listener` | Internal projects | IHostedService, SessionProcessor, dead letter queue reprocessing, subject routing |
| 42 | `microservice/query-handler` | Internal projects | MediatR queries, filtering, pagination, DTO projections |
| 43 | `microservice/query-repository` | Internal projects | AsyncRepository<T>, UnitOfWork, specialized queries |

---

## CATEGORY 11: Microservice - Cosmos DB (4 skills) [OUR PATTERNS]

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 44 | `microservice/cosmos-entity` | Internal projects | IContainerDocument, PartitionKeys, discriminator, ETag |
| 45 | `microservice/cosmos-repository` | Internal projects | LINQ queries, FeedIterator, RU monitoring |
| 46 | `microservice/cosmos-unit-of-work` | Internal projects | TransactionalBatch, ETag concurrency, chunked batches |
| 47 | `microservice/cosmos-config` | Internal projects | ServicePrincipal vs AuthKey, direct mode, DatabaseRunner |

---

## CATEGORY 12: Microservice - Processor (4 skills) [OUR PATTERNS]

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 48 | `microservice/hosted-service` | Internal projects | IHostedService, BackgroundService, session processors |
| 49 | `microservice/event-routing` | Internal projects | Subject-based routing, MediatR dispatch, idempotent |
| 50 | `microservice/grpc-client` | Internal projects | AddGrpcClient<T>, ExternalServicesOptions, error handling |
| 51 | `microservice/batch-processing` | Internal projects | SemaphoreSlim, session receiver, deduplication |

---

## CATEGORY 13: Microservice - gRPC (3 skills) [OUR PATTERNS]

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 52 | `microservice/grpc-service` | Internal projects | Proto files, service impl, MediatR, mapping extensions |
| 53 | `microservice/grpc-interceptors` | Internal projects | Culture, exception, validation interceptors |
| 54 | `microservice/grpc-validation` | Internal projects | FluentValidation for proto requests, Calzolari integration |

---

## CATEGORY 14: Microservice - Gateway (4 skills) [OUR PATTERNS]

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 55 | `microservice/gateway-endpoint` | Internal projects | Controllers, Paginated<T>, export, gRPC→REST |
| 56 | `microservice/gateway-registration` | Internal projects | Client factory, URL options, ValidateOnStart |
| 57 | `microservice/gateway-security` | Internal projects | JWT, policies, Pentagon, Scalar/Swagger auth |
| 58 | `microservice/gateway-documentation` | Internal projects | Scalar API documentation for all gateway types (Swagger is legacy only for existing old projects) |

---

## CATEGORY 15: Microservice - Control Panel (5 skills) [OUR PATTERNS]

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 59 | `microservice/cp-gateway-facade` | Internal projects | Gateway class, nested management, HttpExtensions |
| 60 | `microservice/cp-response-result` | Internal projects | ResponseResult<T>, Switch pattern, ProblemDetails |
| 61 | `microservice/cp-blazor-page` | Internal projects | MudBlazor, MudDataGrid, dialogs, RenderFragment |
| 62 | `microservice/cp-filter-model` | Internal projects | QueryStringBindable, URL sync, PropertyChanged |
| 63 | `microservice/cp-services` | Internal projects | WebApp registration, menu items, API clients |

---

## CATEGORY 16: Testing (4 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 64 | `testing/unit-testing` | clean-arch-skills | xUnit, NSubstitute, FluentAssertions, AAA pattern |
| 65 | `testing/integration-testing` | Combined | WebApplicationFactory, Testcontainers, Respawn |
| 66 | `testing/microservice-testing` | Internal projects | CustomConstructorFaker, assertion extensions, full-cycle |
| 67 | `testing/tdd-workflow` | dotnet-claude-kit | Red-green-refactor cycle, multi-cycle features |

---

## CATEGORY 17: DevOps & Infrastructure (5 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 68 | `devops/dockerfile` | Combined | Multi-stage build, non-root, health checks |
| 69 | `devops/k8s-manifest` | Internal projects | Deployment, Service, Secrets, token placeholders, per-environment manifests ({env}-manifest.yaml) |
| 70 | `devops/github-actions` | Combined | Build+deploy, Azure OIDC, ACR, AKS, environment secrets, deployment environments |
| 71 | `devops/aspire` | dotnet-claude-kit | .NET Aspire orchestration, service defaults, local development environment setup |
| 72 | `devops/ci-cd` | dotnet-claude-kit | GitHub Actions + Azure DevOps YAML pipelines |

---

## CATEGORY 18: Workflow & Productivity (5 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 73 | `workflow/multi-repo` | Original | Multi-repo coordination, dependency order |
| 74 | `workflow/existing-project` | Original | Detection, convention learning, version respect |
| 75 | `workflow/feature-lifecycle` | Original | SDD phases adapted for microservices |
| 76 | `workflow/convention-learner` | dotnet-claude-kit | Detect patterns, enforce consistency |
| 77 | `workflow/scaffolding` | dotnet-claude-kit | Architecture-aware feature scaffolding |

---

## CATEGORY 19: Background Jobs & Email (3 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 78 | `infra/quartz-jobs` | clean-arch-skills | IJob, cron scheduling, persistent store |
| 79 | `infra/email-service` | clean-arch-skills | IEmailService, SendGrid/SES, templates |
| 80 | `infra/messaging` | dotnet-claude-kit | Wolverine/MassTransit, sagas, outbox (generic) |

---

## CATEGORY 20: Code Quality & Review (3 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 81 | `quality/standards-review` | Original | Company standards checklist for reviews |
| 82 | `quality/coderabbit` | Original | CodeRabbit CLI integration |
| 83 | `quality/de-sloppify` | dotnet-claude-kit | 7-step cleanup: format, usings, dead code, sealed |

---

## CATEGORY 21: Cross-Cutting Additions (10 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 84 | `microservice/event-versioning` | Original | Versioned event handlers, event schema evolution, upcasting strategies |
| 85 | `data/db-migrations` | Original | EF Core migration CI/CD pipeline, Cosmos DB manual migration CI/CD plan |
| 86 | `resilience/rate-limiting` | Original | Pentagon service (microservice), ASP.NET rate limiting middleware (generic), throttling strategies |
| 87 | `testing/performance-testing` | Original | Load testing, BenchmarkDotNet for hot paths, Test.Live projects for Service Bus throughput |
| 88 | `api/cors-configuration` | Original | CORS policy setup, origin whitelisting, credential handling, preflight configuration |
| 89 | `microservice/event-catalogue` | Original | Event catalogue per service, event schema documentation, cross-service event registry |
| 90 | `api/real-time` | Original | SignalR for internal real-time, SSE for public-facing real-time communication |
| 91 | `infra/feature-flags` | Original | Feature flag solutions evaluation, toggle patterns, recommended packages |
| 92 | `architecture/multi-tenancy` | Original | Multi-tenant architecture patterns, tenant isolation strategies, data partitioning |
| 93 | `api/grpc-design` | Original | gRPC API design for .NET: proto file design, service implementation, client generation, gRPC-JSON transcoding, gRPC-Web |

---

## CATEGORY 22: Documentation (8 skills)

| # | Skill | Source | Description |
|---|-------|--------|-------------|
| 94 | `docs/readme-generator` | Original | README.md generation from project analysis: badges, setup, architecture diagram, API summary. Per-repo + umbrella (microservice) |
| 95 | `docs/api-documentation` | Original | OpenAPI doc enrichment: operation summaries, examples, schema descriptions. Markdown API reference generation |
| 96 | `docs/adr` | Original | Architecture Decision Records: MADR format, numbered sequence, status lifecycle, cross-references |
| 97 | `docs/code-documentation` | Original | XML doc comments for public APIs, per-layer README, inline documentation standards. Detects existing style |
| 98 | `docs/deployment-guide` | Original | Deployment runbook generation: prerequisites, steps, rollback, verification. Per-environment, per-service |
| 99 | `docs/release-notes` | Original | Changelog and release notes from git history: Keep a Changelog format, conventional commits, semantic versioning |
| 100 | `docs/feature-spec` | Original | User-facing feature documentation and business specs. Distinct from SDD spec — this is for stakeholders |
| 101 | `docs/service-documentation` | Original | Service catalogue, Mermaid diagrams, event flow docs, cross-service dependency map, SLA/SLO definitions |

---

## TOTAL: 120 skills

| Category | Count | Source |
|----------|-------|--------|
| Core Language & Style | 4 | Generic |
| Architecture | 5 | Generic |
| Web API | 5 | Generic |
| Data Access | 5 | Generic |
| CQRS & Messaging (generic) | 4 | Generic |
| Error Handling & Resilience | 3 | Generic |
| Security | 3 | Generic |
| Observability | 3 | Generic |
| Microservice - Event Sourcing | 6 | Our Patterns |
| Microservice - Query Side | 5 | Our Patterns |
| Microservice - Cosmos DB | 4 | Our Patterns |
| Microservice - Processor | 4 | Our Patterns |
| Microservice - gRPC | 3 | Our Patterns |
| Microservice - Gateway | 4 | Our Patterns |
| Microservice - Control Panel | 5 | Our Patterns |
| Testing | 4 | Mixed |
| DevOps & Infrastructure | 5 | Mixed |
| Workflow & Productivity | 5 | Mixed |
| Background Jobs & Email | 3 | Generic |
| Code Quality & Review | 3 | Mixed |
| Cross-Cutting Additions | 10 | Mixed |
| Documentation | 8 | Mixed |
| **TOTAL** | **120** | |

---

## Agent Expansion

| Agent | Scope | Skills Loaded |
|-------|-------|---------------|
| `dotnet-architect` | Generic .NET architecture | architecture/*, core/*, project-structure |
| `api-designer` | REST API design | api/*, resilience/*, security/* |
| `ef-specialist` | EF Core & data access | data/*, cqrs/* (generic) |
| `command-architect` | Microservice command side | microservice/event-*, microservice/command-*, microservice/grpc-* |
| `query-architect` | Microservice query side (SQL) | microservice/query-*, microservice/grpc-* |
| `cosmos-architect` | Microservice query side (Cosmos) | microservice/cosmos-*, microservice/query-event-handler |
| `processor-architect` | Microservice processor | microservice/hosted-*, microservice/event-routing, microservice/grpc-client |
| `gateway-architect` | Microservice gateway | microservice/gateway-*, api/* |
| `controlpanel-architect` | Microservice control panel | microservice/cp-* |
| `test-engineer` | Testing (all types) | testing/unit-testing, testing/integration-testing, testing/microservice-testing, testing/tdd-workflow, testing/performance-testing |
| `reviewer` | Code review | quality/*, security/* |
| `devops-engineer` | CI/CD, Docker, K8s | devops/*, observability/* |
| `docs-engineer` | Documentation (all types) | docs/*, api/openapi, microservice/event-catalogue |

**Total: 13 agents**

---

## How Modes Work

### User says: `/dotnet-ai.init`

**If microservice patterns detected** (or user selects "Microservices"):
→ Loads microservice skills + core skills
→ Routes to microservice agents
→ SDD lifecycle with multi-repo

**If generic .NET project** (or user selects "Generic"):
→ Loads generic skills only (categories 1-8, 16-22)
→ Routes to generic agents (dotnet-architect, api-designer, ef-specialist)
→ SDD lifecycle with single repo
→ Supports VSA, Clean Architecture, DDD, Modular Monolith

**Mixed**: Some features may use both (e.g., generic API project that later adds event sourcing)
