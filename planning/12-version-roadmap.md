# dotnet-ai-kit - Version Roadmap

## Overview

This document organizes the project's build phases into versioned releases and plans future feature additions beyond v1.0.

---

## v1.0 — Foundation Release

**Goal**: Full SDD lifecycle for .NET microservices and generic projects, targeting Claude Code first.

### Included Phases (from 06-build-roadmap.md)

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Foundation (plugin structure, rules, AGENTS.md) | Planned |
| 2 | Configuration (config.yml, permissions) | Planned |
| 3 | Knowledge (16 reference documents) | Planned |
| 4 | Core + Workflow Skills (8 core + 3 workflow + 9 gap-analysis) | Planned |
| 5 | SDD Planning Commands (specify, clarify, plan, tasks, analyze) | Planned |
| 6 | Command Skills (6 command-side skills + agent) | Planned |
| 7 | Query Skills (5 query + 4 cosmos skills + agents) | Planned |
| 8 | Other Skills (processor, gateway, controlpanel, testing) | Planned |
| 9 | Implementation (implement command + multi-repo orchestration) | Planned |
| 10 | Review System (review + CodeRabbit + verify) | Planned |
| 11 | Code Generation (add-aggregate, add-entity, add-event, etc.) | Planned |
| 12 | PR & Session (pr, checkpoint, wrap-up) | Planned |
| 13 | Templates (11 project scaffolds: 7 microservice + 4 generic) | Planned |
| 14 | Permissions (permission configs) | Planned |
| 15 | Documentation System (8 docs skills + agent + command) | Planned |

### v1.0 Deliverables Summary

| Component | Count |
|-----------|-------|
| Rules | 6 |
| Agents | 13 |
| Skills | 104 |
| Commands | 27 |
| Knowledge Docs | 16 |
| Templates | 11 |
| Permission Configs | 4 |

### v1.0 Scope Boundaries

**In scope**: Claude Code plugin, full SDD lifecycle, microservice + generic .NET, single-repo and multi-repo, CodeRabbit integration.

**Out of scope**: Simple REST microservices (v1.1), MassTransit/broker abstraction (v1.1), YARP gateway (v1.1), Sagas/Choreography (v1.2), Dapr (v1.2), SignalR (v1.2), other AI tools (v1.1), alternative event stores (v2.0), GraphQL (v2.0), serverless (v2.0).

### v1.0 Late Additions

- Claude Code plugin format
- Agent Skills spec compliance
- 4 hooks (bash-guard, edit-format, scaffold-restore, commit-lint)
- C# LSP MCP config (.mcp.json)

---

## v1.1 — Microservice Flexibility & Multi-Tool

**Goal**: Make the tool relevant to ALL .NET microservice teams (not just event-sourcing), expand beyond Claude Code, and add high-value quick wins.

**Timeline**: After v1.0 stabilization.

### Microservice Expansion (Priority)

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 1 | Simple REST Microservice Mode | High | Very High | New "rest-micro" mode: database-per-service, Minimal API/Controllers, EF Core, no event sourcing, no gRPC. New templates, agent routing, code-gen support. Covers the ~70% of microservices that don't use event sourcing. |
| 2 | MassTransit Messaging Abstraction | High | Very High | Replace Azure-Service-Bus-only messaging with MassTransit. Supports RabbitMQ, Kafka, Azure Service Bus, AWS SQS/SNS, InMemory (testing) through one API. New skills for consumers, producers, message contracts. Update outbox/processor patterns. |
| 3 | YARP API Gateway | Medium | High | YARP reverse proxy replacing custom gateway templates. Route configuration, service discovery, request transformation, rate limiting, load balancing, health-based routing. New template + agent update. |

### Multi-Tool & Quick Wins

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 4 | Cursor Integration (Phase 16a) | Medium | High | .cursorrules generation, rules + commands in Cursor format |
| 5 | GitHub Copilot Integration (Phase 16b) | Medium | High | Copilot Extensions, .agent.md command format |
| 6 | Codex CLI Integration (Phase 16c) | Low | Medium | AGENTS.md generation, instruction format |
| 7 | gRPC-Web for Blazor WASM | Low | Medium | Browser-side gRPC calls from control panel, replaces REST facade |
| 8 | API Contract Testing (Pact) | Low | Medium | Consumer-driven contract tests for gRPC and REST |
| 9 | .NET Aspire Enhanced Orchestration | Low | Medium | Deeper Aspire service defaults, resource provisioning, dashboard configuration |

### New Skills for v1.1

| Skill | Category | Agent |
|-------|----------|-------|
| `microservice/rest-micro/crud-service` | Microservice | dotnet-architect |
| `microservice/rest-micro/database-per-service` | Microservice | ef-specialist |
| `microservice/rest-micro/api-composition` | Microservice | api-designer |
| `microservice/rest-micro/inter-service-http` | Microservice | api-designer |
| `microservice/messaging/masstransit-consumer` | Microservice | processor-architect |
| `microservice/messaging/masstransit-producer` | Microservice | command-architect |
| `microservice/messaging/message-contracts` | Microservice | dotnet-architect |
| `microservice/messaging/masstransit-testing` | Testing | test-engineer |
| `api/yarp-gateway` | API | gateway-architect |
| `api/yarp-routing` | API | gateway-architect |
| `api/yarp-transforms` | API | gateway-architect |
| `microservice/grpc-web` | gRPC | controlpanel-architect |
| `testing/contract-testing` | Testing | test-engineer |
| `devops/aspire-advanced` | DevOps | devops-engineer |
| `integration/cursor` | Workflow | N/A (CLI) |
| `integration/copilot` | Workflow | N/A (CLI) |
| `integration/codex` | Workflow | N/A (CLI) |

### New Templates for v1.1

| Template | Type | Description |
|----------|------|-------------|
| `rest-micro` | Microservice | Simple REST microservice (Minimal API + EF Core + database-per-service) |
| `yarp-gateway` | Microservice | YARP reverse proxy gateway (replaces custom gateway template) |

### New Knowledge Docs for v1.1

| Document | Description |
|----------|-------------|
| `masstransit-patterns.md` | MassTransit consumers, producers, sagas, testing, broker configuration |
| `rest-microservice-patterns.md` | Database-per-service, API composition, inter-service communication without event sourcing |
| `yarp-gateway-patterns.md` | YARP configuration, route matching, transforms, service discovery |

### v1.1 Additional Features

- Roslyn MCP tools (semantic .NET code analysis -- find_symbol, find_references, get_diagnostics, detect_antipatterns, find_dead_code)
- Cursor, GitHub Copilot, Codex CLI support
- Extension catalog (online/community installs)
- PolySkill and skills.sh marketplace publishing
- New project detection: "rest-micro" type in `/dai.detect` smart skill
- Agent routing update: simple REST microservices routed to dotnet-architect + api-designer (not command/query architects)

---

## v1.2 — Distributed Patterns & Dapr

**Goal**: Add distributed transaction support, Dapr sidecar integration, real-time communication, and BFF patterns.

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 10 | Saga / Choreography Patterns | High | Very High | MassTransit saga state machines, compensation logic, saga persistence (EF Core, Redis), choreography-based eventual consistency. Works with both CQRS and simple-REST modes. |
| 11 | Dapr Integration | High | High | Dapr sidecar for state, pub/sub, service invocation, secrets, bindings. Dapr .NET SDK, Aspire + Dapr orchestration. Cloud-agnostic alternative to direct broker/database coupling. |
| 12 | SignalR Real-Time | Medium | Medium | Push notifications from services to clients, hub patterns, group management, scaling with Redis backplane |
| 13 | BFF (Backend for Frontend) | Medium | Medium | Separate API layers per client type (web, mobile, admin), field projection, client-specific aggregation |
| 14 | Blazor Server / Hybrid Support | Medium | Medium | Server-side rendering, Blazor United, hybrid rendering modes |

### New Skills for v1.2

| Skill | Category | Agent |
|-------|----------|-------|
| `architecture/saga-patterns` | Architecture | dotnet-architect |
| `architecture/choreography` | Architecture | dotnet-architect |
| `architecture/saga-state-machine` | Architecture | dotnet-architect |
| `microservice/dapr/state-management` | Microservice | dotnet-architect |
| `microservice/dapr/pubsub` | Microservice | processor-architect |
| `microservice/dapr/service-invocation` | Microservice | api-designer |
| `microservice/dapr/secrets` | Microservice | devops-engineer |
| `microservice/dapr/aspire-integration` | Microservice | devops-engineer |
| `api/signalr-hubs` | API | api-designer |
| `api/signalr-scaling` | API | devops-engineer |
| `architecture/bff-pattern` | Architecture | api-designer |
| `api/blazor-server` | API | dotnet-architect |

### New Knowledge Docs for v1.2

| Document | Description |
|----------|-------------|
| `saga-choreography-patterns.md` | Saga orchestration, compensation, state machines, choreography vs orchestration |
| `dapr-patterns.md` | Dapr building blocks, sidecar architecture, .NET SDK, Aspire integration |
| `signalr-patterns.md` | Real-time communication, hub design, scaling, group management |

---

## v1.3 — Operations, Observability & Reliability

**Goal**: Production operations, centralized observability, chaos engineering, secret management, and cost optimization.

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 15 | Centralized Observability | High | High | ELK/Seq/Application Insights aggregation, Jaeger/Zipkin distributed tracing, Prometheus/Grafana dashboards, correlation IDs |
| 16 | Secret Management | Medium | High | Azure Key Vault, HashiCorp Vault patterns, secret rotation, environment-based config |
| 17 | Chaos Engineering | Medium | Medium | Fault injection with Polly/Simmy, resilience verification, failure scenario testing |
| 18 | Infrastructure-as-Code (Terraform/Bicep) | High | High | Azure resource provisioning, environment management |
| 19 | Service Discovery | Medium | Medium | Consul, Eureka integration beyond K8s/Aspire DNS-based discovery |
| 20 | Cost Optimization Skills | Low | Medium | Azure cost analysis, right-sizing, reserved instances, RU budgeting for Cosmos |

### New Skills for v1.3

| Skill | Category | Agent |
|-------|----------|-------|
| `observability/centralized-logging` | Observability | devops-engineer |
| `observability/distributed-tracing` | Observability | devops-engineer |
| `observability/dashboards` | Observability | devops-engineer |
| `observability/cost-optimization` | Observability | devops-engineer |
| `security/secret-management` | Security | devops-engineer |
| `security/secret-rotation` | Security | devops-engineer |
| `testing/chaos-engineering` | Testing | test-engineer |
| `devops/terraform` | DevOps | devops-engineer |
| `devops/bicep` | DevOps | devops-engineer |
| `infra/service-discovery` | Infrastructure | devops-engineer |

### New Knowledge Docs for v1.3

| Document | Description |
|----------|-------------|
| `observability-stack-patterns.md` | ELK, Seq, Application Insights, Jaeger, Prometheus, Grafana integration |
| `secret-management-patterns.md` | Key Vault, Vault, rotation, environment config |

---

## v2.0 — Platform Evolution

**Goal**: Major evolution — alternative architectures, cloud-native, migration patterns, and AI integration.

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 21 | Event Store Alternatives | High | Medium | EventStoreDB, Marten as alternatives to SQL-based event sourcing |
| 22 | GraphQL Support (HotChocolate) | High | Medium | Schema-first, subscriptions, DataLoader, filtering, sorting |
| 23 | Strangler Fig Pattern | Medium | High | Monolith → microservice migration, gradual decomposition, anti-corruption layers |
| 24 | Service Mesh | Medium | Medium | Istio, Linkerd sidecar patterns, mTLS, traffic management |
| 25 | Azure Functions / Serverless | High | Medium | Isolated worker, Durable Functions, event-driven triggers |
| 26 | Antigravity Integration (Phase 16d) | Medium | Medium | When Antigravity defines its extension format |
| 27 | Multi-Cloud Deployment | High | Medium | AWS ECS/EKS + Azure AKS + GCP Cloud Run deployment targets |
| 28 | AI-Assisted Code Review | Medium | High | Custom ML models for pattern detection beyond CodeRabbit |
| 29 | Plugin Marketplace | High | High | Community extensions, version management, dependency resolution |
| 30 | NServiceBus / Wolverine | Medium | Medium | Enterprise service bus patterns as alternative to MassTransit |

### New Skills for v2.0

| Skill | Category | Agent |
|-------|----------|-------|
| `data/eventstoredb` | Data | command-architect |
| `data/marten` | Data | command-architect |
| `api/graphql` | API | api-designer |
| `api/graphql-subscriptions` | API | api-designer |
| `architecture/strangler-fig` | Architecture | dotnet-architect |
| `architecture/anti-corruption-layer` | Architecture | dotnet-architect |
| `infra/service-mesh` | Infrastructure | devops-engineer |
| `infra/azure-functions` | Infrastructure | devops-engineer |
| `devops/aws-deployment` | DevOps | devops-engineer |
| `devops/gcp-deployment` | DevOps | devops-engineer |
| `microservice/messaging/nservicebus` | Microservice | dotnet-architect |
| `microservice/messaging/wolverine` | Microservice | dotnet-architect |

### New Knowledge Docs for v2.0

| Document | Description |
|----------|-------------|
| `graphql-patterns.md` | HotChocolate, schema design, DataLoader, subscriptions |
| `strangler-fig-patterns.md` | Monolith decomposition, anti-corruption layer, gradual migration |
| `service-mesh-patterns.md` | Istio/Linkerd, mTLS, traffic management, observability |

---

## Version Decision Criteria

When deciding which version a feature belongs to:

| Criteria | v1.0 | v1.1 | v1.2 | v1.3 | v2.0 |
|----------|------|------|------|------|------|
| Core SDD lifecycle | Yes | - | - | - | - |
| Multi-tool support | Claude only | +Cursor, Copilot, Codex | - | - | +Antigravity |
| Microservice modes | Event-sourced CQRS only | +Simple REST micro, +MassTransit | +Dapr sidecar | - | +NServiceBus, Wolverine |
| Architecture patterns | Microservice + Generic | +YARP gateway | +Sagas, +BFF, +SignalR | - | +Strangler Fig, +Service Mesh |
| Messaging | Azure Service Bus | +MassTransit (RabbitMQ, Kafka, AWS SQS) | +Dapr pub/sub | - | +NServiceBus, Wolverine |
| Infrastructure | Docker, K8s, GitHub Actions | +Aspire enhanced | +Dapr sidecar | +IaC, Secrets, Discovery | +Serverless, Multi-cloud |
| Observability | OpenTelemetry, Serilog, Health | - | - | +ELK, Jaeger, Prometheus | - |
| Testing | Unit, Integration, TDD, Perf | +Contract testing | - | +Chaos | +AI review |

---

## Migration Notes

- **v1.0 → v1.1**: Non-breaking. Adds new AI tool integrations (Cursor, Copilot, Codex) alongside Claude Code — existing Claude Code setup continues to work. Also adds simple REST microservice mode, MassTransit messaging, and YARP gateway. New "rest-micro" project type added to detection.
- **v1.1 → v1.2**: Non-breaking. Adds Dapr, Sagas, SignalR, BFF. New agent routing for Dapr-based projects. Existing skills unchanged.
- **v1.2 → v1.3**: Non-breaking. Adds operational/observability skills. No changes to core workflow.
- **v1.3 → v2.0**: May include breaking changes to plugin manifest format, config schema, or extension system. Adds GraphQL, Strangler Fig, service mesh. Migration guide provided.

---

## Upgrade Path

```bash
# Check current version
dotnet-ai --version

# Upgrade CLI
uv tool install dotnet-ai-kit --force --from git+https://github.com/{user}/dotnet-ai-kit.git@v1.1

# Upgrade commands in project (re-copies latest files)
dotnet-ai upgrade

# Check what's new
dotnet-ai changelog
```

Each version is tagged in git. The `dotnet-ai upgrade` command detects the installed version and copies only new/changed files.
