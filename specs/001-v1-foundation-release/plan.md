# Implementation Plan: dotnet-ai-kit v1.0 — Foundation Release

**Branch**: `001-v1-foundation-release` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-v1-foundation-release/spec.md`

## Summary

Build dotnet-ai-kit v1.0: an AI dev tool plugin (Python CLI + knowledge base)
covering the full .NET development lifecycle. The tool auto-detects project
properties, provides 25 slash commands via Claude Code, and orchestrates
single-repo and multi-repo feature development from specification to PR.

The implementation is primarily a content-generation project (170+ markdown
files) plus a lightweight Python CLI (6 modules). Content is derived from
18 planning documents; the CLI handles initialization, detection, and file
management.

## Technical Context

**Language/Version**: Python 3.10+ (CLI tool); targets .NET 8.0/9.0/10.0 projects
**Primary Dependencies**: typer (CLI framework), pydantic (config validation), jinja2 (template rendering), rich (terminal output), pyyaml (config parsing)
**Storage**: File-based only — YAML (config), Markdown (knowledge base, feature artifacts), JSON (permissions)
**Testing**: pytest (CLI unit/integration tests)
**Target Platform**: Windows, macOS, Linux (cross-platform via pathlib.Path, subprocess with list args)
**Project Type**: CLI tool + knowledge base (rules, skills, agents, commands, templates, knowledge docs)
**Performance Goals**: Install + init < 2 minutes (SC-010); simple feature lifecycle < 15 minutes (SC-001)
**Constraints**: Token budgets (rules ≤100 lines, commands ≤200 lines, skills ≤400 lines); cross-platform (no OS-specific shell commands); company-agnostic ({Company}/{Domain} placeholders)
**Scale/Scope**: 6 rules + 13 agents + 101 skills + 25 commands + 11 knowledge docs + 11 templates + 4 permission configs + Python CLI (8 modules)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Detect-First, Respect-Existing | PASS | This IS the principle being built. FR-002 (auto-detect), FR-005 (match existing), FR-023 (version respect). The tool itself is new code, not modifying existing projects. |
| II. Pattern Fidelity | PASS | FR-005 mandates generated code matches existing patterns. Skills contain version-aware code examples. |
| III. Architecture & Platform Agnostic | PASS | FR-004 (generic + microservice), FR-009 (cross-platform), FR-024 (Claude Code first, portable). CLI uses pathlib.Path everywhere. |
| IV. Best Practices & Quality | PASS | Rules enforce TDD, SOLID, check-docs-first. CLI tested with pytest. Knowledge base content reviewed against official docs. |
| V. Safety & Token Discipline | PASS | FR-006 (--dry-run), FR-007 (undo), no deploy capability. Token budgets enforced per file type. Skills loaded on-demand. |

No violations. Complexity Tracking table not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-v1-foundation-release/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli-commands.md  # CLI command interface contracts
│   └── handoff-schemas.md  # Inter-command artifact schemas
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
dotnet-ai-kit/
├── src/dotnet_ai_kit/              # Python CLI tool
│   ├── __init__.py                 # Package init + version
│   ├── cli.py                      # CLI command definitions (typer)
│   ├── agents.py                   # AGENT_CONFIG per AI tool
│   ├── config.py                   # Pydantic config schema + validation
│   ├── detection.py                # Project type detection algorithm
│   ├── copier.py                   # File copy + Jinja2 template rendering
│   ├── extensions.py               # Extension manager + manifest parsing
│   └── models.py                   # Pydantic models (config, project)
│
├── rules/                          # 6 always-loaded convention files
│   ├── naming.md                   # ~80 lines
│   ├── coding-style.md             # ~60 lines
│   ├── localization.md             # ~40 lines
│   ├── error-handling.md           # ~55 lines
│   ├── architecture.md             # ~80 lines
│   └── existing-projects.md        # ~65 lines
│
├── agents/                         # 13 specialist agent definitions
│   ├── dotnet-architect.md         # Generic: architecture patterns
│   ├── api-designer.md             # Generic: REST API design
│   ├── ef-specialist.md            # Generic: EF Core & data access
│   ├── devops-engineer.md          # Cross-cutting: CI/CD, Docker, K8s
│   ├── command-architect.md        # Microservice: event-sourced commands
│   ├── query-architect.md          # Microservice: SQL query side
│   ├── cosmos-architect.md         # Microservice: Cosmos DB query side
│   ├── processor-architect.md      # Microservice: background processing
│   ├── gateway-architect.md        # Microservice: REST gateway
│   ├── controlpanel-architect.md   # Microservice: Blazor WASM
│   ├── test-engineer.md            # Cross-cutting: testing patterns
│   ├── reviewer.md                 # Cross-cutting: code review
│   └── docs-engineer.md            # Cross-cutting: documentation
│
├── skills/                         # 101 skill files in 22 subdirectories
│   ├── core/                       # 4 skills
│   ├── architecture/               # 5 skills
│   ├── api/                        # 5 skills
│   ├── data/                       # 5 skills
│   ├── cqrs/                       # 4 skills
│   ├── resilience/                 # 3 skills
│   ├── security/                   # 3 skills
│   ├── observability/              # 3 skills
│   ├── microservice/               # 31 skills (6 subdirectories)
│   │   ├── command/                # 6 skills
│   │   ├── query/                  # 5 skills
│   │   ├── cosmos/                 # 4 skills
│   │   ├── processor/              # 4 skills
│   │   ├── grpc/                   # 3 skills
│   │   ├── gateway/                # 4 skills
│   │   └── controlpanel/           # 5 skills
│   ├── testing/                    # 4 skills
│   ├── devops/                     # 5 skills
│   ├── workflow/                   # 5 skills
│   ├── infra/                      # 3 skills
│   ├── quality/                    # 3 skills
│   └── docs/                       # 8 skills
│
├── commands/                       # 25 command templates
│   ├── specify.md                  # SDD lifecycle
│   ├── clarify.md
│   ├── plan.md
│   ├── tasks.md
│   ├── analyze.md
│   ├── implement.md
│   ├── review.md
│   ├── verify.md
│   ├── pr.md
│   ├── init.md                     # Project management
│   ├── configure.md
│   ├── add-aggregate.md            # Code generation
│   ├── add-entity.md
│   ├── add-event.md
│   ├── add-endpoint.md
│   ├── add-page.md
│   ├── add-crud.md
│   ├── add-tests.md
│   ├── docs.md                     # Documentation
│   ├── checkpoint.md               # Session management
│   ├── wrap-up.md
│   ├── do.md                       # Smart commands
│   ├── status.md
│   ├── undo.md
│   └── explain.md
│
├── knowledge/                      # 11 reference documents
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
├── templates/                      # 11 project scaffolds + config
│   ├── command/                    # Microservice templates (7)
│   ├── query/
│   ├── cosmos-query/
│   ├── processor/
│   ├── gateway-management/
│   ├── gateway-consumer/
│   ├── controlpanel-module/
│   ├── generic-vsa/                # Generic templates (4)
│   ├── generic-clean-arch/
│   ├── generic-ddd/
│   ├── generic-modular-monolith/
│   ├── commands/                   # Command file templates per AI tool
│   └── config-template.yml         # Default config template
│
├── config/                         # 4 permission configs
│   ├── permissions-minimal.json
│   ├── permissions-standard.json
│   ├── permissions-full.json
│   └── mcp-permissions.json
│
├── tests/                          # CLI tests
│   ├── test_cli.py
│   ├── test_detection.py
│   ├── test_config.py
│   ├── test_copier.py
│   └── test_extensions.py
│
├── pyproject.toml                  # Python package definition
├── CLAUDE.md                       # Project context for Claude Code
├── README.md                       # Already exists
├── CONTRIBUTING.md                 # Already exists
├── CHANGELOG.md                    # Already exists
└── LICENSE                         # Already exists
```

**Structure Decision**: Single project — Python CLI + flat knowledge base
directories. No frontend/backend split. The CLI is the only executable;
all other content is markdown files copied to user projects.

## Content Source Mapping

Each output directory maps to specific planning documents:

| Output | Source Planning Docs | File Count |
|--------|---------------------|------------|
| `rules/` | `05-rules-design.md` | 6 |
| `agents/` | `03-agents-design.md` | 13 |
| `skills/core/` through `skills/docs/` | `02-skills-inventory.md`, `11-expanded-skills-inventory.md`, `14-generic-skills-spec.md`, `18-microservice-skills-spec.md` | 101 |
| `commands/` | `04-commands-design.md`, `17-code-generation-flows.md` | 25 |
| `knowledge/` | `14-generic-skills-spec.md`, `18-microservice-skills-spec.md` | 11 |
| `templates/` | `15-template-content.md` | 11 dirs |
| `config/` | `10-permissions-config.md` | 4 |
| `src/dotnet_ai_kit/` | `16-cli-implementation.md`, `07-project-structure.md` | 8 |
| `CLAUDE.md` | `01-vision.md`, all planning docs | 1 |
| `pyproject.toml` | `16-cli-implementation.md` | 1 |

## Implementation Phases

| Phase | Focus | Dependencies | Output Files |
|-------|-------|-------------|-------------|
| 1 | Foundation: rules, agents, pyproject.toml, CLI entry, CLAUDE.md | None | 6 + 13 + 3 = 22 |
| 2 | Configuration: config, detection, models, config template | Phase 1 | 4 + 1 = 5 |
| 3 | Knowledge: 11 reference documents | None (parallel with Phase 2) | 11 |
| 4 | Skills: 101 skill files across 22 categories | Phase 1 (agents define skill assignments) | 101 |
| 5 | Commands: 13 SDD + smart commands | Phase 4 (commands reference skills) | 13 |
| 6-8 | Domain skills validation: verify skill content has full patterns | Phase 4 | 0 (updates to existing) |
| 9 | Multi-repo: enhance implement.md with orchestration | Phase 5 | 1 (update) |
| 10 | Review: review.md, verify.md with CodeRabbit integration | Phase 5 | 2 (updates) |
| 11 | Code generation: 7 add-* commands | Phase 4 | 7 |
| 12 | PR & session: pr.md, checkpoint.md, wrap-up.md, init.md, configure.md, docs.md | Phase 5 | 6 |
| 13 | Templates: 11 project scaffolds | Phase 4 (templates use skill patterns) | 11 dirs |
| 14 | Permissions: 4 JSON configs | Phase 2 (config schema) | 4 |
| 15 | Docs: docs.md command, docs-engineer agent validation | Phase 12 | 1 (update) |
| CLI | File copy, extensions, copier, tests | Phase 2 | 4 + 5 = 9 |

### Parallel Opportunities

- Phase 3 (knowledge) can run in parallel with Phase 2 (configuration)
- Within Phase 4, skill categories can be written in parallel (different subdirectories)
- Phase 14 (permissions) can run in parallel with Phases 11-13
- CLI tests can be written alongside CLI modules

### Critical Path

```
Phase 1 (foundation)
  → Phase 2 (config) + Phase 3 (knowledge) [parallel]
    → Phase 4 (skills)
      → Phase 5 (SDD commands)
        → Phases 9-12 [can overlap]
          → Phase 13 (templates)
            → Phase 15 (docs command)
```

## Risks & Decisions

| # | Decision/Risk | Resolution |
|---|--------------|------------|
| 1 | CLI framework: click vs typer | Use **typer** — better type hints, auto-completion, less boilerplate. Both work with rich. |
| 2 | 101 skill files = large content volume | Use planning docs 14 and 18 as primary source. Generate skill YAML frontmatter consistently. Validate line counts post-generation. |
| 3 | Token budget enforcement | Post-generation validation: count lines per file, flag violations. Build a simple line-count checker script. |
| 4 | Cross-platform path handling | Python CLI uses pathlib.Path exclusively. All templates use forward slashes. Tests run on all 3 platforms via GitHub Actions. |
| 5 | Skill content quality | Each skill must include version-aware C# examples, "detect existing patterns" section, and "adding to existing project" guidance. Review against official docs before finalizing. |
| 6 | Command file size (200-line limit) | Commands that need more space delegate to skill reading. Command files contain flow logic; skills contain code patterns. |
| 7 | Multi-repo config centralization | Configuration lives in hub project only (per clarification). Individual repos get commands + rules, no config. |
| 8 | Template customization | `.dotnet-ai-kit/templates/` in hub project overrides built-in templates by name (per clarification). |
| 9 | CLI diagnostics | `--verbose` flag on all commands outputs detection, config, skills loaded (per clarification FR-025). |

## Post-Design Constitution Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First | PASS | Detection algorithm in `detection.py`, rules enforce respect-existing |
| II. Pattern Fidelity | PASS | Skills contain version-aware code examples per planning/14 and planning/18 |
| III. Agnostic | PASS | 4 generic + 6 microservice architectures, cross-platform CLI, company placeholders |
| IV. Quality | PASS | pytest for CLI, TDD embedded in rules and test-engineer agent |
| V. Safety & Token | PASS | --dry-run + --verbose on all commands, token budgets in plan, no deploy capability |
