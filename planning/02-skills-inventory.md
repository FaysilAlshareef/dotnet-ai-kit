# dotnet-ai-kit - Skills Inventory

> **Note**: This document contains detailed skill descriptions from scanned internal projects.
> For the complete 120-skill inventory including generic .NET skills, see `11-expanded-skills-inventory.md`.
> For the 27 command definitions, see `04-commands-design.md`.

## Skill Format

Each skill is a `SKILL.md` file (max 400 lines) with:
```yaml
---
name: skill-name
description: >
  What this skill does. Trigger keywords for contextual loading.
---
```

Sections: Core Principles, Patterns (code examples), Anti-patterns, Decision Guide

---

## Skill Sources

| Source | Skills | Focus |
|--------|--------|-------|
| **Our Projects** | ~30 | CQRS, Event Sourcing, Service Bus, Cosmos DB, gRPC microservices |
| **dotnet-claude-kit** | ~20 adapted | Modern C#, Architecture, APIs, Resilience, Observability |
| **dotnet-clean-architecture-skills** | ~10 adapted | Clean Arch, DDD, Repository, Pipeline, Dapper |

**Total: ~120 skills** (deduplicated, merged where overlap exists)

---

## Mode Support

Skills are loaded based on detected project mode:

### Mode 1: Microservices (CQRS + Event Sourcing)
- Categories 1-8 (generic) + Categories 9-15 (microservice-specific) + 16-20 (mixed)
- Uses microservice agents: command-architect, query-architect, cosmos-architect, processor-architect, gateway-architect, controlpanel-architect

### Mode 2: Generic .NET Project
- Categories 1-8 (generic) + Categories 16-20 (mixed)
- Uses generic agents: dotnet-architect, api-designer, ef-specialist
- Supports VSA, Clean Architecture, DDD, Modular Monolith

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

## CATEGORY 5: CQRS & Messaging - Generic (4 skills)

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

## Detailed Skill Descriptions (Microservice Patterns)

The sections below preserve the original detailed descriptions from our Internal project scans.
These feed into the microservice-specific skills (Categories 9-15).

### Core Microservice Skills (shared across project types)

#### `core/event-structure` - Event<T> Pattern
- Event<TData> base class with AggregateId, Sequence, Type, DateTime, Version
- IEventData interface for event data records
- EventType constants and naming conventions
- Event serialization with Newtonsoft.Json (NullValueHandling.Ignore, StringEnumConverter)
- Sequence tracking and idempotency invariants

#### `core/grpc-service` - gRPC Service Patterns
- Proto file structure and naming conventions
- Service implementation inheriting from generated base
- MediatR integration in gRPC services
- Mapping extensions: Request → Command/Query, Output → Response
- Proto type conventions: StringValue for nullable, Timestamp for DateTime
- Enum mapping between proto and domain enums

#### `core/grpc-interceptors` - Interceptor Patterns
- ThreadCultureInterceptor: language header → Thread.CurrentThread.CurrentCulture
- ApplicationExceptionInterceptor: IProblemDetailsProvider → RpcException
- Validation interceptor with Calzolari.Grpc.AspNetCore.Validation
- AccessClaims extraction from access-claims-bin metadata header

#### `core/fluent-validation` - Validation Patterns
- AbstractValidator<TRequest> for gRPC requests
- Libyan phone validation: `^0(91|92|93|94|95)\d{7}$`
- Required vs optional field validation
- Resource string messages (Phrases.InvalidXxx)
- AddAppValidators() registration from assembly

#### `core/serilog-logging` - Logging Patterns
- LoggerServiceBuilder: Build() with configuration
- AppName, AppNamespace enrichment
- Console + Seq sinks
- WriteToConsole flag, SeqUrl configuration
- builder.Host.UseSerilog()
- LogContext.Push for enrichment (EventType, SessionId, MessageId)

#### `core/localization` - Resource File Patterns
- Phrases.resx (default Arabic) + Phrases.en.resx
- Never use plain strings in responses
- EntitiesLocalization: GetDisplayNameFromCulture()
- CultureInfo.CurrentCulture.Name == "en" pattern
- Designer.cs auto-generation

#### `core/program-setup` - Program.cs Patterns
- WebApplication.CreateBuilder pattern
- Serilog initialization before builder
- AddApplicationServices() for MediatR
- AddInfraServices() for DbContext/Repos/ServiceBus
- AddGrpc with interceptors chain
- AddAppValidators()
- MapGrpcService<T>() for each service
- builder.Host.UseSerilog()

#### `core/options-pattern` - Configuration Binding
- Options classes with [Required] attributes
- Bind from IConfiguration sections
- ValidateDataAnnotations() + ValidateOnStart()
- ConnectionStringsOption, ServiceBusOptions, ExternalServicesOptions

### Command-Side Detailed Descriptions

#### `command/aggregate` - Aggregate Pattern
- Aggregate<T> base class with uncommitted events list
- LoadFromHistory(events) using reflection/dynamic dispatch
- ApplyChange(event, isNew) with sequence validation
- Apply(Event) methods per event type
- Factory methods: Account.RegisterAmbassador(command)
- Private setters, domain invariants in methods

#### `command/event-sourcing` - Event Sourcing Flow
- Complete flow: Request → Handler → Aggregate → Event → DB → Outbox → ServiceBus
- Event table with discriminator pattern
- GenericEventConfiguration<TEntity, TData> for JSON Data property
- Unique index on (AggregateId, Sequence)
- Event loading and replay

#### `command/outbox-pattern` - Outbox Implementation
- OutboxMessage entity wrapping Event
- 1:1 relationship with cascade delete
- CommitEventService: save events + outbox atomically
- ServiceBusPublisher: background polling, batch 200, delete after publish
- Thread-safe with lock counter pattern

#### `command/service-bus-publisher` - Publishing Pattern
- ServiceBusClient singleton
- MessageBody: AggregateId, Type, Data, Sequence, Version
- CorrelationId = EventId, PartitionKey = AggregateId
- Subject = EventType string
- ApplicationProperties for metadata
- Fire-and-forget async from CommitEventService

#### `command/handler` - Command Handler Pattern
- IRequestHandler<TCommand, TOutput> with MediatR
- Validation via IQueriesServices (cross-service calls)
- Aggregate creation or loading from history
- CommitNewEventsAsync(aggregate)
- Return output DTO
- Custom exception types with IProblemDetailsProvider

#### `command/db-config` - Command DB Configuration
- ApplicationDbContext with DbSet<Event> and DbSet<OutboxMessage>
- 40+ GenericEventConfiguration registrations
- Discriminator pattern for event types
- UnitOfWork with lazy repositories

### Query-Side Detailed Descriptions (SQL Server)

#### `query/entity` - Query Entity Pattern
- Private setters on all properties
- Constructor from Event<TData> (CTO pattern)
- Private parameterized constructor for reconstruction
- Business methods taking event data
- Sequence field for idempotency
- Computed properties (HasGatewayAccount)
- Collections (List<T>) for related entities

#### `query/event-handler` - Event Handler Pattern
- IRequestHandler<Event<TData>, bool>
- Strict sequence checking: event.Sequence == entity.Sequence + 1
- Return true for already-processed events (idempotent)
- Return false for out-of-order events
- FindAsync, AddAsync, SaveChangesAsync via UnitOfWork
- Create entity on first event (sequence 1)

#### `query/service-bus-listener` - Listener Pattern
- IHostedService with ServiceBusSessionProcessor
- Dead letter processor for failed messages
- HandelSubject() switch routing
- Event<T> deserialization from UTF-8 JSON body
- LogContext enrichment
- Complete on true, Abandon on false

#### `query/query-handler` - Query Handler Pattern
- IRequestHandler<TQuery, TOutput> with MediatR
- Repository delegation for data access
- Dynamic filtering with optional parameters
- Pagination with Skip/Take
- Select projections to DTOs
- OrderByDescending for default sorting

#### `query/repository` - Repository Pattern
- AsyncRepository<T> generic base
- Specialized repositories with custom queries
- IQueryable for complex filtering
- IUnitOfWork with lazy-loaded repositories
- Index configuration for frequent filters

### Query-Side Detailed Descriptions (Cosmos DB)

#### `cosmos/entity` - Cosmos Entity Pattern
- IContainerDocument interface
- 3-level composite PartitionKeys (Primary, Secondary, Tertiary)
- Discriminator pattern for polymorphic queries
- ETag for optimistic concurrency
- IsReport flag for report vs transactional entities
- Factory methods: FromSaleInvoiceCreated()
- Nested documents (List<SoldItem> inside SaleInvoice)

#### `cosmos/repository` - Cosmos Repository Pattern
- Container-based LINQ queries with discriminator filtering
- FeedIterator for pagination
- Cross-partition queries with ToListWithoutPartitionFilterAsync
- SQL queries with parameters
- Request charge (RU) monitoring and logging

#### `cosmos/unit-of-work` - Cosmos Transactional Batch
- Insert/Replace/Upsert/Remove operations
- Single operation: direct call, 2-100: TransactionalBatch, 100+: chunked batches
- ETag-based optimistic concurrency (IfMatchEtag)
- Partition key scoping for transactions

#### `cosmos/config` - Cosmos DB Setup
- CosmosDbOptions with AccountEndpoint, AuthKey, UseServicePrincipal
- Service Principal (production) vs AuthKey (development)
- Direct connection mode for performance
- CamelCase serialization, IgnoreNullValues
- DatabaseRunner hosted service for initialization
- Container auto-creation in development only

### Processor Detailed Descriptions

#### `processor/hosted-service` - Background Service Pattern
- IHostedService for session-based listeners
- BackgroundService for custom processing loops
- ServiceBusSessionProcessor configuration (PrefetchCount, MaxConcurrentSessions)
- Manual message completion (AutoCompleteMessages = false)
- Dead letter queue monitoring

#### `processor/event-routing` - Event Routing Pattern
- Subject-based routing via switch expression
- Event<T> deserialization with LogContext enrichment
- MediatR dispatch to handlers
- Return bool: true = complete, false = abandon
- Idempotent handling of AlreadyExists RpcException

#### `processor/grpc-client` - gRPC Client Factory Pattern
- AddGrpcClient<T> with IOptions<ExternalServicesOptions>
- URL configuration from appsettings/K8s env vars
- Exception handling: RpcException status codes
- Retry semantics via message abandonment

#### `processor/batch-processing` - Batch Processing Pattern
- SemaphoreSlim for concurrent session control
- ServiceBusSessionReceiver for batch message fetching
- Deduplication by SourceId using GroupBy/First
- Batch gRPC calls for efficiency

### Gateway Detailed Descriptions

#### `gateway/endpoint` - Endpoint Controller Pattern
- REST controller with [Authorize(Policy = ...)]
- gRPC client injection via DI
- Request mapping to gRPC message
- Response mapping to output DTO
- Paginated<T> for list endpoints
- Export endpoints with batch pagination (1000 records)

#### `gateway/grpc-registration` - Service Registration Pattern
- ServicesUrlsOptions with [Required, Url] validation
- AddGrpcClient<T> with RegisterUrl helper
- ValidateOnStart for URL validation
- Proto file registration in .csproj (GrpcServices="Client")

#### `gateway/security` - Security Patterns
- JWT Bearer authentication with Authority/Audience
- Policy-based authorization (CircleOfficer, Operator, Reporter)
- Custom IAuthorizationHandler implementations
- Pentagon device authentication middleware
- Scalar/Swagger basic auth middleware

#### `gateway/documentation` - API Documentation Pattern
- Scalar UI for all gateway types (ScalarTheme.BluePlanet)
- Swagger UI is legacy only for existing old consumer gateways (multi-version V1/V2)
- OpenApiConfigurations, SwaggerGenConfigurations
- Basic auth protection on documentation endpoints

### Control Panel Detailed Descriptions

#### `controlpanel/gateway-facade` - Gateway Facade Pattern
- Gateway class with nested Management properties
- Lazy initialization (??= pattern)
- Management classes with HttpClient and route constants
- HTTP extension methods (GetAsync, PostAsync, PutAsync, PatchAsync, DeleteAsync)
- PostAsFormAsync for file uploads

#### `controlpanel/response-result` - Result Pattern
- ResponseResult<T> abstract record
- SuccessResult<T>, FailedResult<T> with ProblemDetails
- Switch() and SwitchAsync() extension methods
- Action and Func overloads for success/failure handlers

#### `controlpanel/blazor-page` - Page Component Pattern
- MudBlazor components (MudDataGrid, MudCard, MudExpansionPanels)
- Filter model with QueryStringBindable
- BindToNavigationManager for URL state sync
- PropertyChanged → reload data pattern
- Gateway call → Switch result → update state
- Dialog pattern for operations

#### `controlpanel/filter-model` - Filter ViewModel Pattern
- QueryStringBindable base class with INotifyPropertyChanged
- UpdateQueryStringIfChanged for auto URL sync
- Private backing fields with property change tracking
- ToQuery() mapping to API model
- Navigation manager integration

#### `controlpanel/services-registration` - WebApp Registration
- AddServerApiClients with HttpClient configuration
- AddAuthenticationService, AddMudBlazorAndSnackbar
- MenuItemsProvider registration
- AddLocalization, RegisterValidators
- ServerApiClientRegistrationExtension pattern

### Testing Detailed Descriptions

#### `testing/faker` - Test Data Generation
- CustomConstructorFaker<T> base (RuntimeHelpers.GetUninitializedObject)
- Entity fakers with configurable parameters
- Event fakers with sequence and data generation
- Request fakers for gRPC integration tests
- Bogus library RuleFor patterns

#### `testing/assertion` - Custom Assertions
- Static assertion extension classes per entity
- AssertEquality between events and entities
- AssertEquality between requests and events
- Sequence validation assertions
- Outbox message verification

#### `testing/integration` - Integration Test Pattern
- WebApplicationFactory<Program> with IClassFixture
- WithDefaultConfigurations extension
- DbContextHelper: Query, InsertAsync
- HandlerHelper: HandleEvent, HandleMessage
- GrpcClientHelper: Send with metadata
- ListenerHelper for Service Bus verification
- SetLiveTestsDefaultEnvironment / SetUnitTestsDefaultEnvironment
- FakeServicesHelper for external service mocking

### DevOps Detailed Descriptions

#### `devops/dockerfile` - Container Build
- Multi-stage build: base → build → publish → final
- .NET SDK and ASP.NET images (version-aware)
- Ordered COPY for layer caching (csproj first, then source)
- Non-root user, EXPOSE 8080/8081

#### `devops/k8s-manifest` - Kubernetes Deployment
- Namespace, Secret, Deployment, Service, (optional Ingress)
- Token placeholders: ___SERVICE_NAME___, ___IMAGE_TAG___
- Environment variables from secrets and config maps
- RollingUpdate strategy (maxUnavailable: 0, maxSurge: 1)
- Service Bus topics/subscriptions configuration
- External service URLs via env vars

#### `devops/github-actions` - CI/CD Workflows
- Two jobs: build-and-push + deploy
- Azure OIDC authentication
- ACR build: az acr build --image name:sha
- Token replacement in manifest
- Azure/k8s-deploy action
- Environment secrets for connection strings

### Documentation Detailed Descriptions

#### `docs/readme-generator` - README Generation
- Project analysis: scan .csproj, Program.cs, solution structure
- Badge generation: build status, .NET version, NuGet, license
- Architecture section: detect pattern and generate Mermaid diagram
- Setup section: prerequisites, clone, restore, run steps
- API summary: list endpoints from OpenAPI or controllers
- Microservice mode: per-repo README + umbrella README (cross-service overview)
- Generic mode: single README with full project documentation
- Detect existing README and merge/update rather than overwrite

#### `docs/api-documentation` - API Documentation Enrichment
- Scan minimal API endpoints and controllers for missing OpenAPI metadata
- Generate operation summaries from method names and parameter types
- Add request/response examples from test data or fakers
- Generate Markdown API reference grouped by controller/tag
- Microservice mode: gateway API docs with gRPC-to-REST mapping notes
- Generic mode: standard REST API reference
- Integration with Scalar/Swagger UI customization

#### `docs/adr` - Architecture Decision Records
- MADR (Markdown Any Decision Records) template
- Numbered: docs/adr/0001-use-event-sourcing.md
- Sections: Title, Status, Context, Decision, Consequences
- Status lifecycle: proposed → accepted → deprecated/superseded
- Cross-references between related ADRs
- Auto-generate ADR from architecture discussions during /dotnet-ai.plan
- Index file: docs/adr/README.md with table of all ADRs

#### `docs/code-documentation` - Code Documentation Standards
- XML doc comments: <summary>, <param>, <returns>, <remarks>, <example>
- Public API completeness scan: find public members missing XML docs
- Per-layer README.md explaining purpose, key types, usage
- Detect existing documentation style and match it
- Microservice mode: document event data contracts, aggregate invariants
- Generic mode: document service interfaces, repository contracts

#### `docs/deployment-guide` - Deployment Runbook
- Template: Prerequisites, Environment Variables, Deployment Steps, Verification, Rollback
- Per-environment variants (dev, staging, production)
- Microservice mode: service deployment order, service bus setup, DB migration steps
- Generic mode: single-service deployment checklist
- K8s-specific: manifest application order, secret setup, health check URLs

#### `docs/release-notes` - Release Notes & Changelog
- CHANGELOG.md following Keep a Changelog format
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security
- Auto-generate from conventional commits (feat:, fix:, breaking:)
- Semantic versioning guidance based on changes
- GitHub Release notes generation
- Microservice mode: per-service changelog + combined release notes

#### `docs/feature-spec` - Business & User Documentation
- Business requirements document template
- User guide: feature overview, step-by-step walkthrough
- FAQ section generation from clarification questions
- Stakeholder-facing release summary (non-technical)
- Integration with feature directory: .dotnet-ai-kit/features/NNN/user-docs/

#### `docs/service-documentation` - Service & System Documentation
- Service catalogue entry: name, purpose, team, dependencies, SLA
- Mermaid diagrams: event flow, service dependency, data flow
- Cross-service dependency map with communication patterns
- SLA/SLO definitions: latency targets, uptime, error budgets
- Integration with event-catalogue skill for event schema docs
- Microservice mode: per-service doc + system-wide architecture doc
- Generic mode: module documentation, component interaction diagrams

### Cross-Cutting Detailed Descriptions

#### `api/grpc-design` - gRPC API Design
- Proto file design: service definitions, message types, enums, oneof
- Code-first vs proto-first approach
- gRPC service implementation with MediatR integration
- Client generation: AddGrpcClient, client factories, interceptors
- gRPC-JSON transcoding for REST compatibility
- gRPC-Web for browser clients
- Streaming: server streaming, client streaming, bidirectional
- Error handling: Status codes, RpcException, metadata
- Health checking and reflection services
- Performance: connection pooling, compression, deadlines

---

## Total Summary

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
