# dotnet-ai-kit - Build Roadmap

## Phase Overview

| Phase | Focus | Deliverables | Priority |
|-------|-------|-------------|----------|
| 1 | Foundation | Plugin structure, rules, AGENTS.md, config model | Critical |
| 2 | Configuration | /dotnet-ai.configure, config.yml, permissions | Critical |
| 3 | Knowledge | All knowledge docs from project scans | Critical |
| 4 | Core Skills | 8 core + 3 workflow + 9 gap-analysis skills | Critical |
| 5 | SDD Planning Commands | specify, clarify, plan, tasks, analyze + smart commands (do, status, undo, explain) | Critical |
| 6 | Command Skills | 6 command-side skills + agent | High |
| 7 | Query Skills | 5 query + 4 cosmos skills + agents | High |
| 8 | Other Skills | Processor, gateway, controlpanel, testing | High |
| 9 | Implementation | implement command + multi-repo orchestration | Critical |
| 10 | Review System | review command + CodeRabbit + verify | High |
| 11 | Code Gen | add-aggregate, add-entity, add-event, add-endpoint, add-page, add-crud | High |
| 12 | PR & Session | pr, checkpoint, wrap-up commands | High |
| 13 | Templates | 13 project templates (for new projects) | Medium |
| 14 | Permissions | Permission configs | Medium |
| 15 | Documentation System | 8 docs skills + docs-engineer agent + /dotnet-ai.docs command | Medium |

> **Version Mapping**: Phases 1-15 = v1.0 (Foundation Release). Phase 16 (Multi-Tool) = v1.1. See `12-version-roadmap.md` for full version plan.

---

## Phase 1: Foundation (Start Here)

### 1.1 Plugin Structure
```
dotnet-ai-kit/
├── .claude-plugin/plugin.json
├── .claude/rules/ (15 rules)
├── CLAUDE.md
├── AGENTS.md
└── LICENSE
```

### 1.2 Rules (15 files, ~900 lines total)
1. `naming.md` - Naming conventions (company-agnostic, uses config)
2. `coding-style.md` - C# style (version-aware, not version-forcing)
3. `localization.md` - Resource files, never plain strings
4. `error-handling.md` - IProblemDetailsProvider, Switch pattern
5. `architecture.md` - Layer boundaries, CQRS, event sourcing
6. `existing-projects.md` - Rules for working with existing code
   - Detect before generate
   - Respect existing version
   - Follow existing patterns
   - Never refactor during implementation

### 1.3 AGENTS.md
- 13 agents with routing table
- Multi-repo orchestration rules
- Existing project detection logic

---

## Phase 2: Configuration System

### 2.1 `/dotnet-ai.configure` command
- Interactive questionnaire
- Generates `.dotnet-ai-kit/config.yml`
- Permission configuration
- Integration setup (CodeRabbit)

### 2.2 Config Schema (simplified — see `16-cli-implementation.md` for full schema + validation rules)
```yaml
# .dotnet-ai-kit/config.yml
company:
  name: ""              # Required. Used in namespaces
  github_org: ""        # For cloning
  default_branch: ""    # main/develop

naming:
  solution: "{Company}.{Domain}.{Side}"
  topic: "{company}-{domain}-{side}"

repos: {}               # Repo paths/URLs per type

integrations:
  coderabbit:
    enabled: false

permissions:
  level: "standard"     # minimal/standard/full
```

### 2.3 Permission Templates
- `.claude/settings.local.json` templates per level
- MCP permission templates
- Hook-based safety guards

---

## Phase 3: Knowledge Documents

10 knowledge files capturing actual patterns from scanned projects (+ 6 added during development = 16 total):
1. `event-sourcing-flow.md` - From competition-commands
2. `outbox-pattern.md` - CommitEventService + ServiceBusPublisher
3. `service-bus-patterns.md` - Listeners, session processors, batch
4. `grpc-patterns.md` - Proto, services, mapping, interceptors
5. `cosmos-patterns.md` - IContainerDocument, partitions, batch
6. `testing-patterns.md` - Fakers, assertions, WebApplicationFactory
7. `deployment-patterns.md` - Docker, K8s, GitHub Actions
8. `dead-letter-reprocessing.md` - DLQ listener pattern (from competition-queries)
9. `event-versioning.md` - Event schema evolution and versioned handlers
10. `concurrency-patterns.md` - Row version, concurrency tokens, sequence-based idempotency

---

## Phase 4: Core + Workflow Skills

### Microservice Foundation Skills (8 + 3 new)
event-structure, grpc-service, grpc-interceptors, fluent-validation, serilog-logging, localization, program-setup, options-pattern

These are the shared microservice skills loaded by multiple agents. Generic .NET skills (modern-csharp, coding-conventions, dependency-injection, configuration) are loaded implicitly via rules.

### Additional Foundation Skills (from gap analysis)
event-versioning, event-catalogue, rate-limiting, db-migrations, cors-configuration, real-time, performance-testing, feature-flags, multi-tenancy

### Workflow Skills (3)
1. `workflow/multi-repo/SKILL.md` - Multi-repo coordination patterns
2. `workflow/existing-project/SKILL.md` - Detection, convention learning
3. `workflow/feature-lifecycle/SKILL.md` - SDD phases for microservices

---

## Phase 5: SDD Lifecycle Commands

Build the 5 spec-driven development commands adapted for microservices:
1. `commands/specify.md` - Feature spec with service map
2. `commands/clarify.md` - Resolve ambiguities
3. `commands/plan.md` - Plan across repos
4. `commands/tasks.md` - Tasks per repo with dependencies
5. `commands/analyze.md` - Cross-service consistency

These are the CORE of the tool's value proposition.

> **Note**: Phase 5 also includes the smart commands: `/dotnet-ai.do` (lifecycle shortcut), `/dotnet-ai.status` (progress dashboard), `/dotnet-ai.undo` (revert last action), `/dotnet-ai.explain` (pattern learning).

---

## Phase 6-8: Domain Skills + Agents

Every skill must:
- Include version-aware code examples
- Show how to detect existing patterns
- Include "adding to existing project" section
- NOT assume greenfield

---

## Phase 9: Implementation Command + Multi-Repo

The most complex phase:
1. `commands/implement.md` - Multi-repo implementation
2. GitHub integration (clone, branch, push)
3. Dependency-ordered execution across repos
4. Existing project detection and pattern matching
5. New project creation when needed

---

## Phase 10: Review System

1. `commands/review.md` - Standards review
2. `agents/reviewer.md` - Review specialist agent
3. CodeRabbit CLI integration
4. Auto-fix capability
5. `commands/verify.md` - Build/test/format pipeline

---

## Phase 11-16: Remaining Features

- Phase 11: Code generation commands (add-aggregate, add-entity, add-event, add-endpoint, add-page, add-crud)
- Phase 12: PR & session commands (pr, checkpoint, wrap-up)
- Phase 13: 13 project templates for new projects
- Phase 14: Permission configs
### Phase 15: Documentation System

#### 15.1 Documentation Skills (8 skills)
1. `docs/readme-generator` - README generation from project analysis
2. `docs/api-documentation` - OpenAPI enrichment + Markdown API reference
3. `docs/adr` - Architecture Decision Records (MADR format)
4. `docs/code-documentation` - XML doc comments, per-layer README
5. `docs/deployment-guide` - Deployment runbooks per environment
6. `docs/release-notes` - Changelog + release notes from git history
7. `docs/feature-spec` - User-facing feature docs + business specs
8. `docs/service-documentation` - Service catalogue, Mermaid diagrams, SLA/SLO

#### 15.2 Documentation Agent
- `agents/docs-engineer.md` - Agent #13 (Documentation Specialist)

#### 15.3 Documentation Command
- `commands/docs.md` - `/dotnet-ai.docs` with subcommands (readme, api, adr, deploy, release, service, code, feature, all)

#### 15.4 Knowledge Document
- `knowledge/documentation-standards.md` - Templates, conventions, tool integration

- Phase 16 (v1.1): Multi-tool integration — see `12-version-roadmap.md`

---

## What We Get From References

### From spec-kit:
- **Full SDD lifecycle**: specify → clarify → plan → tasks → analyze → implement
- Feature directory structure (.dotnet-ai-kit/features/NNN-name/)
- Quality checklists pattern
- Incremental clarification (one question at a time)
- Read-only analyze with severity levels
- Phase-based task execution

### From dotnet-claude-kit:
- Plugin manifest (.claude-plugin/plugin.json)
- Skill/agent/command/rule format standards
- Token budgets (400/200/100)
- Hook system (hooks.json)
- Checkpoint and wrap-up patterns
- Verify pipeline (7-phase)
- Code review with structured output
- Build-fix autonomous loop
- Convention detection from existing code

### From dotnet-clean-architecture-skills:
- Skill organization and content structure
- Sample project as reference pattern

### Our Innovation:
- **Multi-repo orchestration** for microservice features
- **Service map** showing distributed feature flow
- **Cross-service analyze** checking consistency across repos
- **Existing project detection** with pattern learning
- **Company-agnostic** configuration model
- **CodeRabbit integration** for optional AI review
- **Permission templates** for workflow automation
- **Dependency-ordered implementation** (Command → Query → Gateway → UI)
- **Multi-tool support** - Portable across Claude Code, Cursor, Copilot, Codex, Antigravity
- **Event versioning** with versioned handlers and schema evolution
- **Event catalogue** per service for cross-service documentation
- **Performance testing** with Test.Live projects and BenchmarkDotNet
- **Multi-tenancy support** as an architecture mode

---

## Planning Document Index

| Doc | File | Purpose |
|-----|------|---------|
| 01 | `01-vision.md` | Vision, principles, supported tools |
| 02 | `02-skills-inventory.md` | 116 skills with detailed descriptions |
| 03 | `03-agents-design.md` | 13 agents, routing tables, orchestration |
| 04 | `04-commands-design.md` | 27 commands, SDD lifecycle flows |
| 05 | `05-rules-design.md` | 9 always-loaded rules |
| 06 | `06-build-roadmap.md` | Build phases and roadmap (this file) |
| 07 | `07-project-structure.md` | Source repo + user project file trees |
| 08 | `08-multi-repo-orchestration.md` | Multi-repo workspace, dependency chain |
| 09 | `09-review-and-coderabbit.md` | Review checklist, CodeRabbit integration |
| 10 | `10-permissions-config.md` | Permission levels, safety guards |
| 11 | `11-expanded-skills-inventory.md` | Full skill inventory with agent mapping |
| 12 | `12-version-roadmap.md` | Version releases (v1.0 → v2.0) |
| 13 | `13-handoff-schemas.md` | Inter-agent file schemas (spec, plan, tasks, etc.) |
| 14 | `14-generic-skills-spec.md` | Code patterns for 32 generic .NET skills |
| 15 | `15-template-content.md` | 13 project template file structures |
| 16 | `16-cli-implementation.md` | CLI detection, config, extension system |
| 17 | `17-code-generation-flows.md` | 5 code generation command flows |
| 18 | `18-microservice-skills-spec.md` | Code patterns for microservice skills |

---

## Post-v1.0 Additions

The following were added after the initial build phases:
- Phase 14: Plugin Ecosystem — `.claude-plugin/plugin.json`, Agent Skills spec compliance, 4 hooks, `.mcp.json` for C# LSP
- Phase 15 (v1.1): Roslyn MCP tools for semantic .NET analysis
