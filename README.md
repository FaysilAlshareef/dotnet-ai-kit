# dotnet-ai-kit

AI dev tool plugin for the **full .NET development lifecycle** — from feature specification to pull request.

Works with any .NET project: Vertical Slice, Clean Architecture, DDD, Modular Monolith, or CQRS Microservices.

## Quick Start

```bash
# Install
uv tool install dotnet-ai-kit --from git+https://github.com/FaysilAlshareef/dotnet-ai-kit.git

# Init (auto-detects your project)
dotnet-ai init . --ai claude

# Build a feature
/dotnet-ai.do "Add order management with tracking"

# That's it. spec → plan → code → test → review → PR
```

No configuration needed. The tool auto-detects your company name, architecture, and .NET version.

## Plugin Installation

### Claude Code Plugin (recommended)

```bash
# Add the marketplace
/plugin marketplace add FaysilAlshareef/dotnet-ai-kit

# Install the plugin
/plugin install dotnet-ai-kit
```

All 26 commands, 104 skills, 13 agents, 6 rules, and 4 safety hooks are available immediately.

### Optional: C# Language Intelligence

```bash
dotnet tool install -g csharp-ls
```

Enables semantic code navigation (go-to-definition, find references, diagnostics) via MCP — ~10x fewer tokens than grep-based analysis.

### Alternative: pip install

```bash
uv tool install dotnet-ai-kit --from git+https://github.com/FaysilAlshareef/dotnet-ai-kit.git
dotnet-ai init . --ai claude
```

## How dotnet-ai-kit Differs

| Feature | dotnet-ai-kit | Microsoft dotnet/skills | dotnet-claude-kit |
|---------|--------------|------------------------|-------------------|
| **Skills** | 104 | ~30 | 47 |
| **Commands** | 26 slash commands | — | 16 |
| **Agents** | 13 specialists | 5 | 10 |
| **SDD Lifecycle** | Full (specify → plan → implement → PR) | No | No |
| **Code Gen Commands** | 7 (add-crud, add-entity, add-event, etc.) | No | `/scaffold` only |
| **AI Project Detection** | 12 types (VSA, Clean Arch, DDD, CQRS, etc.) | No | Convention detector |
| **CLI Tool** | `dotnet-ai init/check/upgrade/configure` | No | No |
| **Hooks** | 4 (bash-guard, format, restore, lint) | No | 7 |
| **MCP** | C# LSP (csharp-ls) | No | 15 Roslyn tools |

**Unique to dotnet-ai-kit:**
- Full Specification-Driven Development lifecycle (one command: `/dotnet-ai.do`)
- 7 code generation commands for any architecture
- AI-powered project type detection for 12 .NET project types
- Python CLI for project management (`init`, `check`, `upgrade`, `configure`)
- Extension system with manifest validation

## Core 5 Commands

| Command | What it does |
|---------|-------------|
| `/dotnet-ai.do "description"` | Build a feature — one command, full lifecycle |
| `/dotnet-ai.add-crud Entity` | Generate complete CRUD (entity, handlers, endpoint, tests) |
| `/dotnet-ai.status` | See feature progress and what to do next |
| `/dotnet-ai.undo` | Revert the last step safely |
| `/dotnet-ai.explain topic` | Learn any pattern with examples |

These 5 commands cover 90% of daily work. The remaining 20 commands give you step-by-step control when you need it.

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
├── Resume from yesterday          → /dotnet-ai.status → follow "Next:" suggestion
└── Preview before doing anything  → Add --dry-run to any command
```

## Supported Projects

### Generic .NET
- Vertical Slice Architecture
- Clean Architecture
- Domain-Driven Design
- Modular Monolith

### Microservices (CQRS + Event Sourcing)
- Command (event-sourced write side)
- Query (SQL Server / Cosmos DB read side)
- Processor (background event processing)
- Gateway (REST API with Scalar docs)
- Control Panel (Blazor WASM)

## How It Works

### Quick Mode (default)

```
/dotnet-ai.do "Add order management"
```

One command chains: specify → plan → implement → review → verify → PR.
- Simple features (<10 tasks): fully automatic
- Complex features (multi-repo): pauses after plan for confirmation
- Always supports `--dry-run` to preview first

### Full Lifecycle (when you need control)

**Single repo:**
```
/dotnet-ai.specify "Add orders" → /dotnet-ai.plan → /dotnet-ai.implement → /dotnet-ai.pr
```

**Multi-repo microservices:**
```
/dotnet-ai.specify → /dotnet-ai.plan → /dotnet-ai.tasks → /dotnet-ai.analyze → /dotnet-ai.implement → /dotnet-ai.pr
```

## Supported AI Tools

| Tool | Status |
|------|--------|
| **Claude Code** | v1.0 (supported) |
| **Cursor** | v1.1 (planned) |
| **GitHub Copilot** | v1.1 (planned) |
| **Codex CLI** | v1.1 (planned) |

The core knowledge (rules, skills, agents, commands) is portable across AI tools.

## All 26 Commands

### SDD Lifecycle
`specify` · `clarify` · `plan` · `tasks` · `analyze` · `implement` · `review` · `verify` · `pr`

### Code Generation
`add-aggregate` · `add-entity` · `add-event` · `add-endpoint` · `add-page` · `add-crud` · `add-tests`

### Smart Commands
`do` · `status` · `undo` · `explain`

### Project & Session
`init` · `detect` · `configure` · `docs` · `checkpoint` · `wrap-up`

All commands support short aliases: `/dai.do`, `/dai.spec`, `/dai.go`, `/dai.crud`, etc.

## Platform Support

Works on **Windows**, **macOS**, and **Linux** — anywhere .NET and Python run.

**Prerequisites:** Python 3.10+, .NET SDK 8.0+, Git

## .NET Version Support

The tool respects your existing .NET version. It:
- Detects version from `.csproj` TargetFramework
- Uses version-appropriate patterns (primary constructors for .NET 8+, etc.)
- Never force-upgrades syntax
- New projects default to latest stable .NET

## What's Inside

| Component | Count | Purpose |
|-----------|-------|---------|
| Rules | 6 | Always-loaded coding conventions |
| Agents | 13 | Specialist agents per project type |
| Skills | 104 | Code patterns and knowledge |
| Commands | 26 | Developer workflow commands |
| Knowledge Docs | 11 | Reference patterns from real projects |
| Templates | 11 | New project scaffolds (7 microservice + 4 generic) |

## Project Status

**Status: v1.0 Implementation Complete**

All components built from 18 planning documents. The tool is installable
via `uv tool install` and ready for use with Claude Code.

| Component | Count | Status |
|-----------|-------|--------|
| Rules | 6 | Complete |
| Agents | 13 | Complete |
| Skills | 104 | Complete |
| Commands | 26 | Complete |
| Knowledge Docs | 11 | Complete |
| Templates | 11 | Complete |
| Permission Configs | 4 | Complete |
| CLI Modules | 8 | Complete |
| CLI Tests | 108 functions | Complete |

See [`planning/`](planning/) for design documentation.

## License

MIT
