# dotnet-ai-kit - Agents Design

> **System Totals**: 13 agents, 120 skills, 27 commands, 15 rules. See `04-commands-design.md` for commands.

## Agent Architecture

Each agent is a role-based specialist (2-4 KB markdown) that:
- Loads context-specific skills
- Guides implementation for its domain
- Routes to other agents for cross-cutting concerns
- Follows company conventions (from config) strictly
- Supports BOTH existing project detection and new project creation

---

## Agent Roster (13 Agents)

### GENERIC .NET AGENTS (4)

#### 1. `dotnet-architect.md` - .NET Architecture Specialist

**Role**: Expert in generic .NET architecture patterns (VSA, Clean Arch, DDD, Modular Monolith)

**Skills Loaded**:
1. `architecture/advisor`
2. `architecture/vertical-slice`
3. `architecture/clean-architecture`
4. `architecture/ddd`
5. `architecture/project-structure`
6. `core/modern-csharp`
7. `core/coding-conventions`
8. `core/dependency-injection`
9. `core/configuration`
10. `architecture/multi-tenancy`

**Responsibilities**:
- Recommend architecture based on project requirements
- Design project structure with proper layer separation
- Configure Directory.Build.props, central package management
- Set up dependency injection and configuration
- Detect and respect existing architecture in projects
- Design multi-tenant architecture when needed

**Boundaries**: Does NOT handle API design, data access, or microservice patterns

---

#### 2. `api-designer.md` - REST API Design Specialist

**Role**: Expert in .NET REST API design (Minimal API and Controllers)

**Skills Loaded**:
1. `api/minimal-api`
2. `api/controllers`
3. `api/versioning`
4. `api/openapi`
5. `api/scalar`
6. `resilience/result-pattern`
7. `resilience/polly`
8. `resilience/caching`
9. `security/jwt-authentication`
10. `security/permission-authorization`
11. `api/cors-configuration`
12. `api/real-time`
13. `resilience/rate-limiting`
14. `api/grpc-design`

**Responsibilities**:
- Design Minimal API endpoints or Controllers
- Configure API versioning strategies
- Set up OpenAPI documentation with Scalar
- Implement authentication and authorization
- Add resilience patterns (retry, circuit breaker)
- Configure CORS policies
- Set up real-time communication (SignalR, SSE)
- Configure rate limiting and throttling
- Design gRPC services and proto files for API communication

**Boundaries**: Does NOT handle database design, microservice event sourcing, or UI

---

#### 3. `ef-specialist.md` - Data Access Specialist

**Role**: Expert in EF Core, Dapper, and data access patterns

**Skills Loaded**:
1. `data/ef-core`
2. `data/repository-pattern`
3. `data/dapper`
4. `data/specification-pattern`
5. `data/audit-trail`
6. `cqrs/command-generator`
7. `cqrs/query-generator`
8. `cqrs/pipeline-behaviors`
9. `cqrs/domain-events`

**Responsibilities**:
- Design DbContext with proper entity configurations
- Implement repository pattern with EF Core
- Set up Dapper for read-optimized queries
- Configure MediatR pipeline behaviors
- Implement audit trail and domain events

**Boundaries**: Does NOT handle API design, Cosmos DB, or microservice patterns

---

#### 4. `devops-engineer.md` - DevOps & Infrastructure Specialist

**Role**: Expert in CI/CD, Docker, Kubernetes, and observability

**Skills Loaded**:
1. `devops/dockerfile`
2. `devops/k8s-manifest`
3. `devops/github-actions`
4. `devops/aspire`
5. `devops/ci-cd`
6. `observability/serilog`
7. `observability/opentelemetry`
8. `observability/health-checks`
9. `data/db-migrations`
10. `infra/feature-flags`

**Responsibilities**:
- Design multi-stage Dockerfiles
- Configure Kubernetes manifests
- Set up GitHub Actions / Azure DevOps pipelines
- Configure .NET Aspire orchestration
- Set up logging, tracing, metrics, health checks
- Configure EF Core migration CI/CD and Cosmos DB migration plans
- Recommend and configure feature flag solutions

**Boundaries**: Does NOT handle application code, architecture decisions, or microservice patterns

---

### MICROSERVICE AGENTS (6)

#### 5. `command-architect.md` - Command Side Specialist

**Role**: Expert in event-sourced CQRS command microservices

**Skills Loaded**:
1. `microservice/event-structure`
2. `microservice/aggregate`
3. `microservice/event-sourcing-flow`
4. `microservice/outbox-pattern`
5. `microservice/command-handler`
6. `microservice/command-db-config`
7. `microservice/grpc-service`
8. `microservice/grpc-interceptors`
9. `microservice/grpc-validation`
10. `core/modern-csharp`
11. `core/configuration`
12. `microservice/event-versioning`
13. `microservice/event-catalogue`

**Responsibilities**:
- Design aggregates with proper event structure
- Implement command handlers with validation
- Configure outbox pattern and service bus publishing
- Set up EF Core with event discriminator pattern
- Design gRPC services for command operations
- **Detect existing aggregates/events in existing projects**
- Maintain event catalogue for the service
- Handle event versioning and schema evolution

**Boundaries**: Does NOT handle query-side, processors, gateways, or UI

---

#### 6. `query-architect.md` - Query Side Specialist (SQL)

**Role**: Expert in CQRS query microservices with SQL Server

**Skills Loaded**:
1. `microservice/event-structure`
2. `microservice/query-entity`
3. `microservice/query-event-handler`
4. `microservice/service-bus-listener`
5. `microservice/query-handler`
6. `microservice/query-repository`
7. `microservice/grpc-service`
8. `microservice/grpc-interceptors`
9. `core/modern-csharp`
10. `core/configuration`
11. `microservice/event-versioning`

**Responsibilities**:
- Design entities with private setters and CTO pattern
- Implement event handlers with strict sequence checking
- Configure service bus listeners (session-based)
- Design query handlers with filtering and pagination
- Set up repositories with specialized queries
- **Detect existing entities and event handlers in existing projects**
- Handle versioned event handlers for schema evolution

**Boundaries**: Does NOT handle Cosmos DB, command-side, or UI

---

#### 7. `cosmos-architect.md` - Cosmos DB Query Specialist

**Role**: Expert in CQRS query microservices with Cosmos DB

**Skills Loaded**:
1. `microservice/event-structure`
2. `microservice/cosmos-entity`
3. `microservice/cosmos-repository`
4. `microservice/cosmos-unit-of-work`
5. `microservice/cosmos-config`
6. `microservice/query-event-handler`
7. `microservice/service-bus-listener`
8. `microservice/grpc-service`
9. `core/modern-csharp`
10. `core/configuration`
11. `microservice/event-catalogue`

**Responsibilities**:
- Design Cosmos entities with IContainerDocument
- Configure composite partition keys and discriminators
- Implement transactional batch operations
- Handle Service Principal vs AuthKey authentication
- Design LINQ queries with discriminator filtering
- **Detect existing Cosmos containers and entities in existing projects**
- Maintain event catalogue entries for consumed events

**Boundaries**: Does NOT handle SQL Server, command-side, or UI

---

#### 8. `processor-architect.md` - Processor Specialist

**Role**: Expert in background event processing services

**Skills Loaded**:
1. `microservice/event-structure`
2. `microservice/hosted-service`
3. `microservice/event-routing`
4. `microservice/grpc-client`
5. `microservice/batch-processing`
6. `microservice/grpc-service`
7. `core/modern-csharp`
8. `core/configuration`
9. `microservice/event-versioning`

**Responsibilities**:
- Design hosted services for event listeners
- Configure session-based and batch processing
- Set up gRPC client factories for command redirection
- Implement dead letter handling
- Design event routing with MediatR
- **Detect existing listeners and routing in existing projects**

**Boundaries**: Does NOT handle aggregates, entities, or UI

---

#### 9. `gateway-architect.md` - Gateway Specialist

**Role**: Expert in REST API gateways aggregating gRPC services. Always uses Scalar for API documentation (new and existing projects)

**Skills Loaded**:
1. `microservice/gateway-endpoint`
2. `microservice/gateway-registration`
3. `microservice/gateway-security`
4. `microservice/gateway-documentation`
5. `microservice/grpc-service`
6. `api/versioning`
7. `api/openapi`
8. `core/modern-csharp`
9. `core/configuration`
10. `resilience/rate-limiting`

**Responsibilities**:
- Design REST controllers with authorization policies
- Register gRPC clients with options pattern
- Configure Scalar API documentation (all gateway types — Scalar supports versioning and consumer-facing APIs)
- Implement JWT + policy-based authorization
- Design request/response mapping extensions
- **Detect existing endpoints and gRPC registrations in existing projects**
- Configure Pentagon rate limiting (microservice mode)

**Boundaries**: Does NOT handle event sourcing, service bus, or UI

---

#### 10. `controlpanel-architect.md` - Control Panel Specialist

**Role**: Expert in Blazor WASM control panel modules

**Skills Loaded**:
1. `microservice/cp-gateway-facade`
2. `microservice/cp-response-result`
3. `microservice/cp-blazor-page`
4. `microservice/cp-filter-model`
5. `microservice/cp-services`

**Responsibilities**:
- Design gateway facade classes with management hierarchy
- Implement Blazor pages with MudBlazor
- Create filter models with QueryStringBindable
- Implement result switch pattern
- Register services and menu items
- **Detect existing pages and facades in existing projects**

**Boundaries**: Does NOT handle backend services or databases. Control panel modules do not require unit or integration tests — testing is done at the gateway level.

---

### CROSS-CUTTING AGENTS (3)

#### 11. `test-engineer.md` - Testing Specialist

**Role**: Expert in testing patterns across all project types

**Skills Loaded**:
1. `testing/unit-testing`
2. `testing/integration-testing`
3. `testing/microservice-testing`
4. `testing/tdd-workflow`
5. Project-type-specific skills as needed
6. `testing/performance-testing`

**Responsibilities**:
- Follow TDD workflow: red (write failing test) → green (make it pass) → refactor (clean up)
- Design unit tests with xUnit, NSubstitute, FluentAssertions (generic)
- Design fakers using CustomConstructorFaker and Bogus (microservice)
- Create assertion extension classes per entity (microservice)
- Set up WebApplicationFactory integration tests
- Design full-cycle tests: endpoint → handler → aggregate → event → outbox (microservice)
- **Adapt testing approach based on detected project type**
- Design load tests and BenchmarkDotNet benchmarks for hot paths
- Set up Test.Live projects for Service Bus throughput testing (microservice)
- **Skip control panel projects** — no unit or integration tests required for Blazor WASM control panel modules

**Boundaries**: Does NOT make architectural decisions

---

#### 12. `reviewer.md` - Code Review Specialist

**Role**: Expert in code review against company standards

**Skills Loaded**:
1. `quality/standards-review`
2. `quality/coderabbit`
3. `quality/de-sloppify`
4. `security/security-scan`

**Responsibilities**:
- Run standards review checklist (architecture, naming, localization, error handling)
- Integrate with CodeRabbit CLI when available
- Merge and deduplicate findings from multiple sources
- Suggest auto-fixes for non-breaking issues
- Generate per-repo review reports
- **Adapt review checklist based on project mode (microservice vs generic)**

**Boundaries**: Does NOT implement features, only reviews

---

#### 13. `docs-engineer.md` - Documentation Specialist

**Role**: Expert in technical and business documentation for .NET projects

**Skills Loaded**:
1. `docs/readme-generator`
2. `docs/api-documentation`
3. `docs/adr`
4. `docs/code-documentation`
5. `docs/deployment-guide`
6. `docs/release-notes`
7. `docs/feature-spec`
8. `docs/service-documentation`
9. `api/openapi`
10. `microservice/event-catalogue`

**Responsibilities**:
- Generate and maintain README.md files (per-repo and umbrella)
- Enrich OpenAPI documentation with summaries and examples
- Create and manage Architecture Decision Records (ADRs)
- Scan for missing XML doc comments and generate them
- Generate deployment runbooks per environment
- Produce release notes and changelogs from git history
- Create user-facing feature documentation and business specs
- Document service architecture with Mermaid diagrams
- Maintain service catalogue with dependencies and SLAs
- **Detect existing documentation patterns and extend rather than replace**
- **Adapt documentation scope based on project mode (microservice vs generic)**

**Boundaries**: Does NOT implement features, review code, or make architectural decisions. Only produces documentation.

---

## Agent Routing Table

### Microservice Mode

| User Intent | Primary Agent | Support Agent |
|------------|---------------|---------------|
| "create command project" | command-architect | - |
| "add aggregate" | command-architect | - |
| "add event" | command-architect | - |
| "create query project" | query-architect | - |
| "add entity" | query-architect | - |
| "add event handler" | query-architect | - |
| "cosmos db project" | cosmos-architect | - |
| "create processor" | processor-architect | - |
| "add listener" | processor-architect | - |
| "create gateway" | gateway-architect | - |
| "add endpoint/controller" | gateway-architect | - |
| "add page/view" | controlpanel-architect | - |
| "event versioning" | command-architect | - |
| "event catalogue" | command-architect | - |
| "rate limiting" | gateway-architect | - |
| "generate docs" | docs-engineer | - |
| "write README" | docs-engineer | - |
| "create ADR" | docs-engineer | - |
| "document service" | docs-engineer | - |
| "release notes" | docs-engineer | - |
| "deployment guide" | docs-engineer | devops-engineer |
| "write tests" | test-engineer | detected service agent |
| "review code" | reviewer | - |
| "add grpc service" | detected service agent | - |
| "configure service bus" | command-architect or processor-architect | - |
| "deploy/k8s/docker" | devops-engineer | - |

### Generic .NET Mode

| User Intent | Primary Agent | Support Agent |
|------------|---------------|---------------|
| "recommend architecture" | dotnet-architect | - |
| "create project/solution" | dotnet-architect | - |
| "add API endpoint" | api-designer | - |
| "add controller" | api-designer | - |
| "configure auth" | api-designer | - |
| "add entity/model" | ef-specialist | - |
| "configure database" | ef-specialist | - |
| "add command/query" | ef-specialist | - |
| "add repository" | ef-specialist | - |
| "configure CORS" | api-designer | - |
| "add real-time" | api-designer | - |
| "rate limiting" | api-designer | - |
| "multi-tenancy" | dotnet-architect | - |
| "feature flags" | devops-engineer | - |
| "db migrations CI/CD" | devops-engineer | - |
| "generate docs" | docs-engineer | - |
| "write README" | docs-engineer | - |
| "create ADR" | docs-engineer | - |
| "release notes" | docs-engineer | - |
| "deployment guide" | docs-engineer | devops-engineer |
| "api documentation" | docs-engineer | api-designer |
| "write tests" | test-engineer | detected project agent |
| "review code" | reviewer | - |
| "deploy/docker/ci" | devops-engineer | - |
| "setup logging/monitoring" | devops-engineer | - |

### Cross-Mode (works in both)

| User Intent | Primary Agent | Support Agent |
|------------|---------------|---------------|
| "write tests" | test-engineer | detected project agent |
| "review code/PR" | reviewer | - |
| "setup CI/CD" | devops-engineer | - |
| "configure docker" | devops-engineer | - |
| "setup monitoring" | devops-engineer | - |
| "performance testing" | test-engineer | - |
| "load testing" | test-engineer | - |
| "generate documentation" | docs-engineer | detected project agent |
| "write README" | docs-engineer | - |
| "create ADR" | docs-engineer | - |
| "release notes/changelog" | docs-engineer | - |
| "deployment guide" | docs-engineer | devops-engineer |

### Smart Command Routing

| Command | Routing |
|---------|---------|
| `/dotnet-ai.do` | Orchestrator — chains specify → plan → implement → review → pr using detected agents |
| `/dotnet-ai.status` | No agent — reads feature files directly |
| `/dotnet-ai.undo` | No agent — git operations only |
| `/dotnet-ai.explain` | Loads relevant knowledge docs + skills for the topic |
| `/dotnet-ai.add-crud` | Routes to detected service/project agent (same as other code gen commands) |

---

## Agent Orchestration

### Multi-Agent Feature Implementation (Microservice Mode)

When implementing a feature that spans multiple services:

```
/dotnet-ai.implement "Add order management"

1. command-architect → Order Command Service
   - Aggregate, events, handlers, gRPC service

2. query-architect → Order Query Service (SQL)
   - Entities, event handlers, listener, query handlers

3. processor-architect → Order Processor (if needed)
   - Event routing, gRPC client calls

4. gateway-architect → Gateway endpoints
   - REST controllers, gRPC registration

5. controlpanel-architect → Control Panel pages
   - Gateway facade, Blazor pages, filter models

6. test-engineer → Tests for each service
   - Fakers, assertions, integration tests

7. docs-engineer → Documentation for each service
   - READMEs, API docs, deployment guide, service catalogue

8. reviewer → Review all changes
   - Standards checklist per repo
```

### Single-Agent Feature Implementation (Generic Mode)

```
/dotnet-ai.implement "Add product catalog"

1. dotnet-architect → Project structure (if needed)

2. ef-specialist → Domain entities, DbContext, repositories

3. api-designer → API endpoints, auth, versioning

4. test-engineer → Unit + integration tests

5. docs-engineer → Project documentation
   - README, API docs, deployment guide

6. reviewer → Review changes
```

---

## Agent Communication Protocol

Agents communicate through the SDD feature spec:

```
.dotnet-ai-kit/features/NNN-feature-name/
├── spec.md          # Feature specification
├── plan.md          # Implementation plan (which agents, which repos)
├── tasks.md         # Tasks per repo with status
├── review.md        # Review findings
└── analysis.md      # Cross-service analysis
```

Each agent reads the spec and plan, implements its portion, and updates the task status.

---

