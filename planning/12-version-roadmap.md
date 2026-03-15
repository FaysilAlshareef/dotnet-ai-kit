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
| 3 | Knowledge (11 reference documents) | Planned |
| 4 | Core + Workflow Skills (8 core + 3 workflow + 9 gap-analysis) | Planned |
| 5 | SDD Planning Commands (specify, clarify, plan, tasks, analyze) | Planned |
| 6 | Command Skills (6 command-side skills + agent) | Planned |
| 7 | Query Skills (5 query + 4 cosmos skills + agents) | Planned |
| 8 | Other Skills (processor, gateway, controlpanel, testing) | Planned |
| 9 | Implementation (implement command + multi-repo orchestration) | Planned |
| 10 | Review System (review + CodeRabbit + verify) | Planned |
| 11 | Code Generation (add-aggregate, add-entity, add-event, etc.) | Planned |
| 12 | PR & Session (pr, checkpoint, wrap-up) | Planned |
| 13 | Templates (7 project scaffolds) | Planned |
| 14 | Permissions (permission configs) | Planned |
| 15 | Documentation System (8 docs skills + agent + command) | Planned |

### v1.0 Deliverables Summary

| Component | Count |
|-----------|-------|
| Rules | 6 |
| Agents | 13 |
| Skills | 101 |
| Commands | 25 |
| Knowledge Docs | 11 |
| Templates | 7 |
| Permission Configs | 4 |

### v1.0 Scope Boundaries

**In scope**: Claude Code plugin, full SDD lifecycle, microservice + generic .NET, single-repo and multi-repo, CodeRabbit integration.

**Out of scope**: Other AI tool integrations (Cursor, Copilot, Codex, Antigravity), advanced orchestration (sagas), alternative event stores, GraphQL, serverless.

---

## v1.1 — Multi-Tool & Quick Wins

**Goal**: Expand beyond Claude Code and add high-value, low-effort features.

**Timeline**: After v1.0 stabilization.

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 1 | Cursor Integration (Phase 16a) | Medium | High | .cursorrules generation, rules + commands in Cursor format |
| 2 | GitHub Copilot Integration (Phase 16b) | Medium | High | Copilot Extensions, .agent.md command format |
| 3 | Codex CLI Integration (Phase 16c) | Low | Medium | AGENTS.md generation, instruction format |
| 4 | gRPC-Web for Blazor WASM | Low | Medium | Browser-side gRPC calls from control panel, replaces REST facade |
| 5 | API Contract Testing (Pact) | Low | Medium | Consumer-driven contract tests for gRPC and REST |
| 6 | .NET Aspire Enhanced Orchestration | Low | Medium | Deeper Aspire service defaults, resource provisioning, dashboard configuration |

### New Skills for v1.1

| Skill | Category | Agent |
|-------|----------|-------|
| `integration/cursor` | Workflow | N/A (CLI) |
| `integration/copilot` | Workflow | N/A (CLI) |
| `integration/codex` | Workflow | N/A (CLI) |
| `microservice/grpc-web` | gRPC | controlpanel-architect |
| `testing/contract-testing` | Testing | test-engineer |
| `devops/aspire-advanced` | DevOps | devops-engineer |

---

## v1.2 — Architecture Expansion

**Goal**: Support more architecture patterns and infrastructure options.

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 7 | Saga / Choreography Patterns | High | High | Distributed transaction coordination, compensation, saga state machines |
| 8 | Message Broker Abstraction | Medium | High | Support RabbitMQ, AWS SNS/SQS alongside Azure Service Bus |
| 9 | API Gateway Patterns (YARP/Ocelot) | Medium | Medium | Reverse proxy, rate limiting, load balancing, service discovery |
| 10 | Blazor Server / Hybrid Support | Medium | Medium | Server-side rendering, Blazor United, hybrid rendering modes |
| 11 | Database-per-Service Patterns | Medium | Medium | Data isolation, cross-service queries, eventual consistency |

### New Skills for v1.2

| Skill | Category | Agent |
|-------|----------|-------|
| `architecture/saga-patterns` | Architecture | dotnet-architect |
| `architecture/choreography` | Architecture | dotnet-architect |
| `infra/rabbitmq` | Infrastructure | devops-engineer |
| `infra/aws-messaging` | Infrastructure | devops-engineer |
| `api/yarp-gateway` | API | api-designer |
| `api/blazor-server` | API | dotnet-architect |
| `data/database-per-service` | Data | ef-specialist |

---

## v1.3 — Operations & Reliability

**Goal**: Production operations, chaos engineering, and cost optimization.

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 12 | Chaos Engineering | Medium | Medium | Fault injection, resilience verification, Polly chaos policies |
| 13 | Infrastructure-as-Code (Terraform/Bicep) | High | High | Azure resource provisioning, environment management |
| 14 | Cost Optimization Skills | Low | Medium | Azure cost analysis, right-sizing, reserved instances, RU budgeting for Cosmos |
| 15 | Real-time Monitoring Dashboards | Medium | Medium | Grafana/Aspire dashboard templates, alerting rules |

### New Skills for v1.3

| Skill | Category | Agent |
|-------|----------|-------|
| `testing/chaos-engineering` | Testing | test-engineer |
| `devops/terraform` | DevOps | devops-engineer |
| `devops/bicep` | DevOps | devops-engineer |
| `observability/cost-optimization` | Observability | devops-engineer |
| `observability/dashboards` | Observability | devops-engineer |

---

## v2.0 — Platform Evolution

**Goal**: Major evolution — alternative architectures, cloud-native, and AI integration.

| # | Feature | Effort | Value | Details |
|---|---------|--------|-------|---------|
| 16 | Event Store Alternatives | High | Medium | EventStoreDB, Marten as alternatives to SQL-based event sourcing |
| 17 | GraphQL Support | High | Medium | HotChocolate, schema-first, subscriptions, DataLoader |
| 18 | Azure Functions / Serverless | High | Medium | Isolated worker, Durable Functions, event-driven triggers |
| 19 | Antigravity Integration (Phase 16d) | Medium | Medium | When Antigravity defines its extension format |
| 20 | Multi-Cloud Deployment | High | Medium | AWS ECS/EKS + Azure AKS deployment targets |
| 21 | AI-Assisted Code Review | Medium | High | Custom ML models for pattern detection beyond CodeRabbit |
| 22 | Plugin Marketplace | High | High | Community extensions, version management, dependency resolution |

### New Skills for v2.0

| Skill | Category | Agent |
|-------|----------|-------|
| `data/eventstoredb` | Data | command-architect |
| `data/marten` | Data | command-architect |
| `api/graphql` | API | api-designer |
| `infra/azure-functions` | Infrastructure | devops-engineer |
| `devops/aws-deployment` | DevOps | devops-engineer |

---

## Version Decision Criteria

When deciding which version a feature belongs to:

| Criteria | v1.0 | v1.1 | v1.2 | v1.3 | v2.0 |
|----------|------|------|------|------|------|
| Core SDD lifecycle | Yes | - | - | - | - |
| Multi-tool support | Claude only | +Cursor, Copilot, Codex | - | - | +Antigravity |
| Architecture patterns | Microservice + Generic | - | +Sagas, +Broker abstraction | - | +Event store alternatives |
| Infrastructure | Docker, K8s, GitHub Actions | +Aspire enhanced | +YARP | +IaC, Chaos | +Serverless, Multi-cloud |
| Testing | Unit, Integration, TDD, Perf | +Contract testing | - | +Chaos | +AI review |

---

## Migration Notes

- **v1.0 → v1.1**: Non-breaking. Adds new AI tool integrations alongside Claude Code. Existing Claude Code setup continues to work.
- **v1.1 → v1.2**: Non-breaking. Adds new skills and agents. Existing skills unchanged.
- **v1.2 → v1.3**: Non-breaking. Adds operational skills. No changes to core workflow.
- **v1.3 → v2.0**: May include breaking changes to plugin manifest format, config schema, or extension system. Migration guide provided.

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
