# dotnet-ai-kit - Vision & Architecture

---

## Getting Started (15 seconds)

```bash
# 1. Install
uv tool install dotnet-ai-kit --from git+https://github.com/{user}/dotnet-ai-kit.git

# 2. Init (auto-detects your project)
dotnet-ai init . --ai claude

# 3. Build a feature
/dotnet-ai.do "Add user management with roles"

# That's it. The tool handles: spec → plan → code → test → review → PR
```

No configuration needed. The tool auto-detects your company name, architecture, and .NET version.

---

## Core 5 Commands (what you'll use daily)

| Command | What it does |
|---------|-------------|
| `/dotnet-ai.do "description"` | Build a feature — one command, full lifecycle |
| `/dotnet-ai.add-crud Entity` | Generate complete CRUD (entity, handlers, endpoint, tests) |
| `/dotnet-ai.status` | See feature progress and what to do next |
| `/dotnet-ai.undo` | Revert the last step safely |
| `/dotnet-ai.explain topic` | Learn any pattern with examples |

These 5 commands cover 90% of daily work. The remaining 22 commands give you step-by-step control when you need it (see `04-commands-design.md`).

---

## Which command do I use?

```
I want to...
├── Build a feature fast           → /dotnet-ai.do "description"
├── Build a feature step-by-step   → /dotnet-ai.specify → plan → implement
├── Add CRUD for an entity         → /dotnet-ai.add-crud Order
├── Add tests to existing code     → /dotnet-ai.add-tests
├── Add one endpoint/event/page    → /dotnet-ai.add-endpoint, add-event, add-page
├── Check my progress              → /dotnet-ai.status
├── Undo a mistake                 → /dotnet-ai.undo
├── Learn a pattern                → /dotnet-ai.explain "clean architecture"
├── I'm new, show me how           → /dotnet-ai.explain --tutorial
├── Resume from yesterday          → /dotnet-ai.status → follow the "Next:" suggestion
└── Preview before doing anything  → Add --dry-run to any command
```

---

## What is dotnet-ai-kit?

An **AI dev tool plugin** that covers the **full development lifecycle** for any .NET project — from a single Clean Architecture API to event-sourced CQRS microservices spanning 6 repositories, simple REST microservices with database-per-service, or MassTransit-based distributed systems. It knows your team's patterns, generates code that looks hand-written, and handles everything from feature specification to pull request creation.

**One command to build a feature:**
```
/dotnet-ai.do "Add order management with tracking"
```

Works with **any .NET project**: Vertical Slice Architecture, Clean Architecture, DDD, Modular Monolith, CQRS Microservices (event-sourced), Simple REST Microservices (database-per-service), or MassTransit/Dapr-based distributed systems. Detects your patterns automatically — no configuration required for basic use.

### Supported AI Dev Tools

| Tool | Status | Integration |
|------|--------|-------------|
| **Claude Code** | First target | Rules + Commands + Skills (read on demand) |
| **Cursor** | Planned (v1.1) | Rules (.cursorrules), commands |
| **GitHub Copilot** | Planned (v1.1) | Copilot Extensions |
| **Codex CLI** | Planned (v1.1) | AGENTS.md, instructions |
| **Antigravity** | Planned (v1.1) | TBD |

### How It Works in Claude Code

The tool uses Claude Code's native features — no custom plugin system:

```
.claude/
├── commands/       ← 27 slash commands (each reads relevant skills on demand)
├── rules/          ← 9 always-loaded coding conventions
CLAUDE.md           ← Project context
skills/             ← 120 skill files (read by commands when needed)
knowledge/          ← 16 reference docs (read by commands when needed)
```

Each command includes routing logic: it detects the project type, reads the relevant skill files, and follows those patterns. The 13 "agents" from the planning docs become the routing logic inside commands — not separate files.

## Problem Statement

**For any .NET team:**
1. AI assistants generate generic code that doesn't match team conventions
2. No single source of truth for "how we build things"
3. New developers need weeks to learn all the patterns
4. Adding a simple CRUD feature still requires boilerplate in multiple layers
5. Code reviews catch the same pattern violations repeatedly

**For microservice teams (additional):**
6. Features span 3-6 repositories (command, query, processor, gateway, control panel)
7. Manual coordination across repos is error-prone and slow
8. Event consistency across services is hard to verify

## Solution

An AI dev tool plugin (starting with Claude Code) that:
1. **One command for simple features** - `/dotnet-ai.do "Add orders"` chains the full lifecycle automatically
2. **Full lifecycle when you need control** - specify → plan → implement → review → PR (each step individually)
3. **Works with existing projects** - detects patterns, respects .NET version, learns conventions
4. **Quick code generation** - `/dotnet-ai.crud Order` for instant CRUD, or add-aggregate/entity/endpoint for specific components
5. **Orchestrates multi-repo features** - clone repos, create branches, implement across services, create linked PRs
6. **Reviews against company standards** - with optional CodeRabbit CLI integration
7. **Is company-agnostic** - company name, repo URLs, topics are all configurable
8. **Preview before generating** - `--dry-run` on any command to see what will happen

## Core Design Principles

1. **Simple by Default, Powerful When Needed** - `/dotnet-ai.do` for quick work, full lifecycle for complex features
2. **Any .NET Project** - Generic (VSA, Clean Arch, DDD) and Microservices (CQRS + Event Sourcing, Simple REST, MassTransit, Dapr)
3. **Existing Projects First** - Most work is on existing code, not greenfield
4. **Multi-Repo When Needed** - Features can span repos. The tool thinks in distributed systems
5. **Version Tolerant** - Works with .NET 8, 9, 10. Detects and respects what exists
6. **Pattern Fidelity** - Generated code is indistinguishable from hand-written code
7. **Company Agnostic** - No hardcoded company names. Everything is configurable
8. **Token Conscious** - Skills max 400 lines, commands max 200 lines, rules max 100 lines
9. **Tool Agnostic** - Core knowledge is portable. Start with Claude Code, expand to Cursor, Copilot, Codex, Antigravity
10. **Cross-Platform** - Works on Windows, macOS, and Linux. No OS-specific assumptions
11. **Best Practices First** - Clean code, SOLID, TDD (red-green-refactor). Always check official docs before using a package or framework
12. **Latest .NET for New Projects** - New projects default to latest stable .NET (currently .NET 10). Existing projects keep their version

## Architecture Overview

The tool is a **CLI + knowledge base** that initializes into any project and registers
commands with the user's AI dev tool (Claude Code, Cursor, Copilot, Codex, Antigravity).

```
dotnet-ai-kit/                       # Source repository
├── src/                             # CLI tool (dotnet-ai init/check/upgrade)
├── rules/                           # 9 always-loaded convention files
├── agents/                          # 13 specialist agents
├── skills/                          # 120 skills by domain
├── commands/                        # 27 command templates
├── knowledge/                       # Reference documents
├── templates/                       # Project scaffolding
└── config/                          # Permission templates
```

After `dotnet-ai init . --ai claude`:
```
my-project/
├── .dotnet-ai-kit/                  # Config, features, memory
│   ├── config.yml
│   └── features/
├── .claude/
│   ├── commands/                    # dotnet-ai.specify.md, dotnet-ai.plan.md, ...
│   └── rules/                      # naming.md, coding-style.md, ...
└── (existing project files...)
```

See `07-project-structure.md` for the full directory trees.

## Configuration Model

### Quick Start (zero-config)
```
dotnet-ai init . --ai claude
> Detected: MyCompany.Orders (Clean Architecture, .NET 10)
> ✓ Ready to use. Run /dotnet-ai.do "your feature" to start.
```

The tool works immediately by auto-detecting company name from namespaces, architecture from folder structure, and .NET version from .csproj. No configuration required for basic use.

### Full Configuration: `/dotnet-ai.configure`

Configuration is **just-in-time** — the tool only asks questions when the feature that needs them is first used:

| When | What's asked | Why |
|------|-------------|-----|
| First run (`init`) | Company name (auto-detected from namespace, confirm) | Required for code generation |
| First multi-repo feature | GitHub org, repo URLs | Needed to clone repos |
| First `/dotnet-ai.review` with CodeRabbit | "CodeRabbit CLI detected. Enable?" | Optional integration |
| First `/dotnet-ai.pr` | Default branch name | Needed for PR base branch |
| Anytime via `/dotnet-ai.configure` | All settings at once | For power users who want to set everything up front |

**You never need to run `/dotnet-ai.configure` to start using the tool.** It will ask what it needs, when it needs it.

Saved to `.dotnet-ai-kit/config.yml` in the workspace.

### Command Aliases

All commands have short aliases for faster typing:

| Full | Short | Purpose |
|------|-------|---------|
| `/dotnet-ai.do` | `/dai.do` | One-command feature builder |
| `/dotnet-ai.specify` | `/dai.spec` | Feature specification |
| `/dotnet-ai.plan` | `/dai.plan` | Implementation plan |
| `/dotnet-ai.implement` | `/dai.go` | Execute implementation |
| `/dotnet-ai.status` | `/dai.status` | Feature status |
| `/dotnet-ai.add-crud` | `/dai.crud` | Full CRUD generation |

Full alias table in `04-commands-design.md` Section G.

## Supported Project Types

### Generic .NET
| Type | Description | Existing Support | Create New |
|------|-------------|-----------------|------------|
| VSA | Vertical Slice Architecture | Detect & work with | Yes |
| Clean Architecture | 4-layer pattern | Detect & work with | Yes |
| DDD | Domain-Driven Design | Detect & work with | Yes |
| Modular Monolith | Multi-module single deployment | Detect & work with | Yes |

### Microservices (CQRS + Event Sourcing) — v1.0
| Type | Description | Existing Support | Create New |
|------|-------------|-----------------|------------|
| Command | Event-sourced write side | Detect & work with | Scaffold from template |
| Query (SQL) | Read side with SQL Server | Detect & work with | Scaffold from template |
| Query (Cosmos) | Read side with Cosmos DB | Detect & work with | Scaffold from template |
| Processor | Background event processor | Detect & work with | Scaffold from template |
| Gateway | REST gateway with Scalar | Detect & work with | Scaffold from template |
| Control Panel | Blazor WASM module | Detect & work with | Scaffold from template |

### Simple REST Microservices (database-per-service) — v1.1
| Type | Description | Existing Support | Create New |
|------|-------------|-----------------|------------|
| REST Micro | API + EF Core + own database | Planned v1.1 | Scaffold from template |
| YARP Gateway | Reverse proxy gateway | Planned v1.1 | Scaffold from template |

### Messaging & Distributed Patterns — v1.1+
| Pattern | Description | Version |
|---------|-------------|---------|
| MassTransit | Broker abstraction (RabbitMQ, Kafka, Azure SB, AWS SQS) | v1.1 |
| Saga / Choreography | Distributed transactions, compensation | v1.2 |
| Dapr | Sidecar for state, pub/sub, invocation, secrets | v1.2 |
| SignalR | Real-time push from services to clients | v1.2 |
| BFF | Backend for Frontend per client type | v1.2 |

## Cross-Platform Support

| OS | Status | Notes |
|----|--------|-------|
| **Windows** | Supported | PowerShell and CMD |
| **macOS** | Supported | zsh / bash |
| **Linux** | Supported | bash / zsh |

The CLI and all generated files work identically across operating systems:
- **File paths**: CLI uses Python `pathlib.Path` everywhere — never string concatenation. Forward slashes in config, OS-native at runtime
- **Line endings**: All templates include `.gitattributes` with `* text=auto` for consistent line ending normalization
- **Config paths**: Stored as OS-native format in `.dotnet-ai-kit/config.yml`. Repo paths accept both `/` and `\`
- **Shell commands**: Only calls cross-platform tools (`dotnet`, `git`, `gh`) — no OS-specific shell commands
- **AI tool paths**: Each AI tool's config directory (`.claude/`, `.cursor/`, etc.) uses the same relative paths on all platforms

Prerequisites (all cross-platform):
- Python 3.10+ (for the CLI)
- .NET SDK 8.0+ (for the projects)
- Git (for version control and multi-repo)

## .NET Version Support

The tool does NOT force a specific .NET version on existing projects. It:
1. Detects the version from `.csproj` TargetFramework
2. Respects existing version (net8.0, net9.0, net10.0)
3. Uses version-appropriate patterns (e.g., primary constructors for .NET 8+)
4. Only suggests upgrades when explicitly asked
5. **New projects** default to latest stable .NET (currently .NET 10)

## Quick Mode (Most Common — use this by default)

```
/dotnet-ai.do "Add order management with tracking"
```
One command. Chains specify → plan → implement → review → verify → PR automatically.

**When does it pause?**
- **Never pauses** for simple features (1 repo, <10 tasks) — fully automatic
- **Pauses after plan** for complex features (multi-repo or >10 tasks) — shows plan, asks "Proceed? [Y/n]"
- **Pauses on ambiguity** — asks max 3 clarifying questions inline, then continues

**Use `/dotnet-ai.do` for everything.** It's smart enough to pause when needed. You only need the full lifecycle commands if you want to manually edit the spec or plan before implementing.

## Full Lifecycle (When You Need Control)

### Generic .NET (single repo)
```
/dotnet-ai.specify "Add order management"
    ↓
/dotnet-ai.plan                ← Plan by layers (Domain → Application → Infrastructure → API)
    ↓
/dotnet-ai.implement           ← Implement in single repo
    ↓
/dotnet-ai.review → verify → pr → wrap-up
```

### Microservices (multi-repo)
```
/dotnet-ai.specify "Add order management"
    ↓
/dotnet-ai.plan                ← Plans across all affected repos
    ↓
/dotnet-ai.tasks               ← Tasks per repo with dependencies
    ↓
/dotnet-ai.analyze             ← Cross-service consistency check
    ↓
/dotnet-ai.implement           ← Clone → Branch → Code → Build → Test (per repo)
    ↓
/dotnet-ai.review → verify → pr → wrap-up
```

### Check progress anytime
```
/dotnet-ai.status              ← Where am I? What's next?
```

## v1.0 Additions (March 2026)

- Claude Code plugin format (`.claude-plugin/plugin.json`) for marketplace distribution
- Agent Skills specification compliance — all 120 SKILL.md files prefixed with `dotnet-ai-`
- 4 safety/quality hooks: pre-bash-guard, post-edit-format, post-scaffold-restore, pre-commit-lint
- C# LSP MCP configuration (`.mcp.json`) pointing to csharp-ls
- AI-powered project detection via `/dotnet-ai.detect` smart skill (replaced Python-based detection)
- `--version` flag on CLI
- `--type` flag validation against 12 known project types
- Claude-only for v1.0 (other AI tools planned for v1.1)

## v1.1 Planned Features

- Roslyn MCP tools for semantic .NET code analysis (find_symbol, find_references, get_diagnostics, detect_antipatterns, find_dead_code, detect_circular_dependencies)
- Cursor, GitHub Copilot, and Codex CLI support
- Extension catalog for online/community extension installs
- PolySkill and skills.sh marketplace publishing
