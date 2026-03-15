# dotnet-ai-kit - Complete Project Structure

## Source Repository (what we build)

```
dotnet-ai-kit/
│
├── src/                                         # CLI tool source
│   └── dotnet_ai_kit/
│       ├── __init__.py                          # CLI entry point (init, check, extension)
│       ├── agents.py                            # Agent config per AI tool
│       └── extensions.py                        # Extension manager & command registration
│
├── rules/                                       # Always-loaded conventions (~600 lines total)
│   ├── naming.md                                # Company-agnostic naming (uses config)
│   ├── coding-style.md                          # Version-aware C# style
│   ├── localization.md                          # Resource file usage
│   ├── error-handling.md                        # IProblemDetailsProvider, Switch
│   ├── architecture.md                          # Layer boundaries, CQRS
│   └── existing-projects.md                     # Detect, respect, extend rules
│
├── agents/                                      # 13 specialist agents (~3 KB each)
│   │  # Generic .NET
│   ├── dotnet-architect.md                      # .NET architecture patterns
│   ├── api-designer.md                          # REST API design
│   ├── ef-specialist.md                         # EF Core & data access
│   ├── devops-engineer.md                       # CI/CD, Docker, K8s
│   │  # Microservice
│   ├── command-architect.md                     # Event-sourced command side
│   ├── query-architect.md                       # SQL Server query side
│   ├── cosmos-architect.md                      # Cosmos DB query side
│   ├── processor-architect.md                   # Background event processor
│   ├── gateway-architect.md                     # REST API gateway
│   ├── controlpanel-architect.md                # Blazor WASM control panel
│   │  # Cross-cutting
│   ├── test-engineer.md                         # Testing across all types
│   ├── reviewer.md                              # Code review specialist
│   └── docs-engineer.md                         # Documentation specialist
│
├── skills/                                      # ~101 skills (max 400 lines each)
│   ├── core/                                    # Language & style (4)
│   ├── architecture/                            # Architecture patterns (5)
│   ├── api/                                     # Web API (5)
│   ├── data/                                    # Data access (5)
│   ├── cqrs/                                    # Generic CQRS (4)
│   ├── resilience/                              # Error handling & resilience (3)
│   ├── security/                                # Auth & security (3)
│   ├── observability/                           # Logging & monitoring (3)
│   ├── microservice/                            # Microservice patterns (31)
│   │   ├── command/                             # Event sourcing, aggregate, outbox (6)
│   │   ├── query/                               # Entity, event handler, listener (5)
│   │   ├── cosmos/                              # Cosmos entity, repo, batch (4)
│   │   ├── processor/                           # Hosted service, routing, batch (4)
│   │   ├── grpc/                                # Service, interceptors, validation (3)
│   │   ├── gateway/                             # Endpoint, registration, security (4)
│   │   └── controlpanel/                        # Facade, result, blazor, filter (5)
│   ├── testing/                                 # Testing (4)
│   ├── devops/                                  # CI/CD & K8s (5)
│   ├── workflow/                                # SDD workflow (5)
│   ├── infra/                                   # Background jobs & email (3)
│   ├── quality/                                 # Code quality & review (3)
│   └── docs/                                    # Documentation (8)
│
├── commands/                                    # 25 command templates (max 200 lines each)
│   │
│   │  # === SDD Lifecycle ===
│   ├── specify.md                               # dotnet-ai.specify
│   ├── clarify.md                               # dotnet-ai.clarify
│   ├── plan.md                                  # dotnet-ai.plan
│   ├── tasks.md                                 # dotnet-ai.tasks
│   ├── analyze.md                               # dotnet-ai.analyze
│   ├── implement.md                             # dotnet-ai.implement
│   ├── review.md                                # dotnet-ai.review
│   ├── verify.md                                # dotnet-ai.verify
│   ├── pr.md                                    # dotnet-ai.pr
│   │
│   │  # === Project Management ===
│   ├── init.md                                  # dotnet-ai.init
│   ├── configure.md                             # dotnet-ai.configure
│   │
│   │  # === Code Generation ===
│   ├── add-aggregate.md                         # dotnet-ai.add-aggregate
│   ├── add-entity.md                            # dotnet-ai.add-entity
│   ├── add-event.md                             # dotnet-ai.add-event
│   ├── add-endpoint.md                          # dotnet-ai.add-endpoint
│   ├── add-page.md                              # dotnet-ai.add-page
│   ├── add-crud.md                              # dotnet-ai.add-crud
│   ├── add-tests.md                             # dotnet-ai.add-tests
│   │
│   │  # === Documentation ===
│   ├── docs.md                                  # dotnet-ai.docs
│   │
│   │  # === Session Management ===
│   ├── checkpoint.md                            # dotnet-ai.checkpoint
│   ├── wrap-up.md                               # dotnet-ai.wrap-up
│   │
│   │  # === Smart Commands ===
│   ├── do.md                                    # dotnet-ai.do
│   ├── status.md                                # dotnet-ai.status
│   ├── undo.md                                  # dotnet-ai.undo
│   └── explain.md                               # dotnet-ai.explain
│
├── knowledge/                                   # Reference documents
│   ├── event-sourcing-flow.md
│   ├── outbox-pattern.md
│   ├── service-bus-patterns.md
│   ├── grpc-patterns.md
│   ├── cosmos-patterns.md
│   ├── testing-patterns.md
│   ├── deployment-patterns.md
│   ├── dead-letter-reprocessing.md
│   ├── event-versioning.md
│   ├── concurrency-patterns.md
│   └── documentation-standards.md
│
├── templates/                                   # Project scaffolding (for new services)
│   ├── command/
│   ├── query/
│   ├── cosmos-query/
│   ├── processor/
│   ├── gateway-management/
│   ├── gateway-consumer/
│   ├── controlpanel-module/
│   ├── commands/                                # Command file templates per AI tool
│   │   ├── specify.md                           # Template with $ARGUMENTS placeholder
│   │   └── ...
│   └── config-template.yml                      # Default config template
│
├── config/                                      # Permission templates
│   ├── permissions-minimal.json                 # Level 1: build/test only
│   ├── permissions-standard.json                # Level 2: + git/gh CLI
│   ├── permissions-full.json                    # Level 3: all operations
│   └── mcp-permissions.json                     # GitHub MCP permissions
│
├── README.md
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml                               # CLI package definition
│
└── planning/                                    # Planning documents (not shipped, 18 files)
    ├── 01-vision.md                             # Vision, principles, supported tools
    ├── 02-skills-inventory.md                   # 101 skills with descriptions
    ├── 03-agents-design.md                      # 13 agents, routing, orchestration
    ├── 04-commands-design.md                    # 25 commands, SDD lifecycle flows
    ├── 05-rules-design.md                       # 6 always-loaded rules
    ├── 06-build-roadmap.md                      # Build phases and roadmap
    ├── 07-project-structure.md                  # Source repo + user project trees
    ├── 08-multi-repo-orchestration.md           # Multi-repo workspace, dependency chain
    ├── 09-review-and-coderabbit.md              # Review checklist, CodeRabbit
    ├── 10-permissions-config.md                 # Permission levels, safety guards
    ├── 11-expanded-skills-inventory.md          # Full skill inventory with agent mapping
    ├── 12-version-roadmap.md                    # Version releases (v1.0 → v2.0)
    ├── 13-handoff-schemas.md                    # Inter-agent file schemas
    ├── 14-generic-skills-spec.md                # Code patterns for 32 generic skills
    ├── 15-template-content.md                   # 7 project template file structures
    ├── 16-cli-implementation.md                 # CLI detection, config, extensions
    ├── 17-code-generation-flows.md              # 5 code generation command flows
    └── 18-microservice-skills-spec.md           # Code patterns for microservice skills
```

---

## What Gets Created in User's Project (after `dotnet-ai init`)

```
my-project/
│
├── .dotnet-ai-kit/                              # dotnet-ai-kit config directory
│   ├── config.yml                               # Company name, repos, settings
│   ├── memory/                                  # Feature specs & plans
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── features/                                # Feature directories
│   │   └── 001-order-management/
│   │       ├── spec.md
│   │       ├── plan.md
│   │       ├── tasks.md
│   │       ├── review.md
│   │       └── service-map.md
│   └── extensions.yml                           # Extension registry & hooks
│
│  # === AI Tool Integration (depends on --ai flag) ===
│
│  # For Claude Code (--ai claude):
├── .claude/
│   ├── commands/                                # Registered slash commands
│   │   ├── dotnet-ai.specify.md
│   │   ├── dotnet-ai.clarify.md
│   │   ├── dotnet-ai.plan.md
│   │   ├── dotnet-ai.tasks.md
│   │   ├── dotnet-ai.analyze.md
│   │   ├── dotnet-ai.implement.md
│   │   ├── dotnet-ai.review.md
│   │   ├── dotnet-ai.verify.md
│   │   ├── dotnet-ai.pr.md
│   │   ├── dotnet-ai.init.md
│   │   ├── dotnet-ai.configure.md
│   │   ├── dotnet-ai.add-aggregate.md
│   │   ├── dotnet-ai.add-entity.md
│   │   ├── dotnet-ai.add-event.md
│   │   ├── dotnet-ai.add-endpoint.md
│   │   ├── dotnet-ai.add-page.md
│   │   ├── dotnet-ai.docs.md
│   │   ├── dotnet-ai.checkpoint.md
│   │   ├── dotnet-ai.wrap-up.md
│   │   ├── dotnet-ai.add-crud.md
│   │   ├── dotnet-ai.add-tests.md
│   │   ├── dotnet-ai.do.md
│   │   ├── dotnet-ai.status.md
│   │   ├── dotnet-ai.undo.md
│   │   └── dotnet-ai.explain.md
│   └── rules/                                   # Copied rules (always-loaded)
│       ├── naming.md
│       ├── coding-style.md
│       ├── localization.md
│       ├── error-handling.md
│       ├── architecture.md
│       └── existing-projects.md
│
│  # For Cursor (--ai cursor):
├── .cursor/
│   └── rules/                                   # Cursor rules files
│       └── dotnet-ai-kit.mdc                    # Combined rules + commands
│
│  # For GitHub Copilot (--ai copilot):
├── .github/
│   └── agents/
│       └── commands/                            # Copilot agent commands
│           ├── dotnet-ai.specify.agent.md
│           └── ...
│
│  # For Codex CLI (--ai codex):
├── AGENTS.md                                    # Agent routing for Codex
│
└── (existing project files...)
```

---

## AI Tool Agent Configuration

```python
# How the CLI knows where to put files per AI tool
AGENT_CONFIG = {
    "claude": {
        "name": "Claude Code",
        "commands_dir": ".claude/commands",
        "rules_dir": ".claude/rules",
        "command_ext": ".md",
        "command_prefix": "dotnet-ai",       # → dotnet-ai.specify.md
        "args_placeholder": "$ARGUMENTS",
    },
    "cursor": {
        "name": "Cursor",
        "rules_dir": ".cursor/rules",
        "command_ext": ".mdc",
        "command_prefix": "dotnet-ai",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "commands_dir": ".github/agents/commands",
        "command_ext": ".agent.md",
        "command_prefix": "dotnet-ai",
        "args_placeholder": "$ARGUMENTS",
    },
    "codex": {
        "name": "Codex CLI",
        "agents_file": "AGENTS.md",
    },
    "antigravity": {
        "name": "Antigravity",
        # Planned for v1.1 (see 12-version-roadmap.md) — format TBD when Antigravity defines its extension format
    },
}
```

---

## File Count Summary

| Category | Count | Max Lines |
|----------|-------|-----------|
| Rules | 6 | 100 each |
| Agents | 13 | ~3 KB each |
| Skills | 101 | 400 each |
| Commands | 25 | 200 each |
| Knowledge | 11 | Unlimited |
| Templates | 7 | Project scaffolds |
| Config | 4 | Permission templates |
| CLI | 1 | Python package |

---

## How to Install

### 1. Install CLI

```bash
# Persistent install (recommended)
uv tool install dotnet-ai-kit --from git+https://github.com/{user}/dotnet-ai-kit.git

# Or one-time use
uvx --from git+https://github.com/{user}/dotnet-ai-kit.git dotnet-ai init my-project
```

### 2. Initialize in Project

```bash
# New project
dotnet-ai init my-project --ai claude

# Existing project (from inside project directory)
dotnet-ai init . --ai claude

# Multiple AI tools at once
dotnet-ai init . --ai claude --ai cursor

# Check what's installed
dotnet-ai check
```

### 3. What `dotnet-ai init` Does

1. Creates `.dotnet-ai-kit/` config directory
2. Detects which AI tools are present (or uses `--ai` flag)
3. Copies command files to the AI tool's commands directory
4. Copies rules to the AI tool's rules directory
5. Generates default `config.yml` template
6. Reports: "dotnet-ai-kit initialized for Claude Code. Run /dotnet-ai.configure to set up."

---

## How to Use

### First Time Setup
```
/dotnet-ai.configure
> Company name: MyCompany
> GitHub org: mycompany-org
> Architecture mode: Microservices / Generic / Auto-detect
> Permission level: Standard
```

### Work on Existing Repos
```
/dotnet-ai.init                  # Detects project type, .NET version, patterns
/dotnet-ai.specify "Add orders"  # Define feature
/dotnet-ai.plan                  # Plan across services
/dotnet-ai.implement             # Implement in existing repos
/dotnet-ai.review                # Review against standards
/dotnet-ai.pr                    # Create PRs
```

### Create New Service
```
/dotnet-ai.init
> No project detected. Create new?
> Type: Command
> Company: MyCompany (from config)
> Domain: Orders
> .NET version: 10.0
```

### Full Feature Lifecycle (Multi-Repo)
```
/dotnet-ai.specify "Add order management with tracking"
/dotnet-ai.clarify
/dotnet-ai.plan          # Shows: Command(new) + Query(new) + Gateway(existing) + UI(existing)
/dotnet-ai.tasks
/dotnet-ai.analyze       # Cross-service consistency check
/dotnet-ai.implement     # Clones, branches, implements across all repos
/dotnet-ai.review        # Standards + optional CodeRabbit
/dotnet-ai.verify        # Build + test per repo
/dotnet-ai.pr            # Creates linked PRs in all repos
/dotnet-ai.wrap-up       # Session handoff
```

---

## Extension System (spec-kit pattern)

### Install Extension
```bash
dotnet-ai extension add jira          # From catalog
dotnet-ai extension add --dev ./ext   # Local development
```

### Extension Manifest
```yaml
# extension.yml
extension:
  id: "azure-devops"
  name: "Azure DevOps Integration"
  version: "1.0.0"

provides:
  commands:
    - name: "dotnet-ai.ado.sync"
      file: "commands/sync.md"
      description: "Sync work items with Azure DevOps"

hooks:
  after_tasks:
    command: "dotnet-ai.ado.sync"
    optional: true
    prompt: "Sync tasks to Azure DevOps?"
```

### Extension commands auto-register to all detected AI tools.

---

## Upgrade

```bash
# Upgrade CLI
uv tool install dotnet-ai-kit --force --from git+https://github.com/{user}/dotnet-ai-kit.git

# Upgrade commands in project (re-copies latest command files)
dotnet-ai upgrade
```
