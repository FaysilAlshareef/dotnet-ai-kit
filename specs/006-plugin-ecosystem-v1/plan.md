# Implementation Plan: Plugin Ecosystem v1.0

**Branch**: `006-plugin-ecosystem-v1` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-plugin-ecosystem-v1/spec.md`

## Summary

Transform dotnet-ai-kit from a pip-only CLI tool into a Claude Code plugin with Agent Skills compliance, 4 safety/quality hooks, C# LSP MCP integration, and marketplace-ready metadata. This unlocks distribution via the 9,000+ plugin ecosystem, cross-agent compatibility with 16+ tools, and competitive parity with dotnet-claude-kit and claude-forge.

## Technical Context

**Language/Version**: Python 3.10+ (CLI), Markdown (skills/commands/rules), JSON (plugin manifest, MCP config), Bash/PowerShell (hooks)
**Primary Dependencies**: typer, pydantic v2, jinja2, rich, pyyaml, questionary (CLI); csharp-ls (optional MCP)
**Storage**: YAML config files, JSON manifests, Markdown skill files
**Testing**: pytest, pytest-cov, ruff
**Target Platform**: Windows, macOS, Linux (cross-platform)
**Project Type**: Claude Code plugin + Python CLI tool (dual distribution)
**Performance Goals**: N/A (configuration/metadata, not runtime service)
**Constraints**: Skills ≤400 lines, Commands ≤200 lines, Rules ≤100 lines. Token budget: <5,000 tokens for all skill indexes at startup.
**Scale/Scope**: 104 SKILL.md files to migrate, 26 commands, 13 agents, 6 rules, 4 new hooks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Detect-First, Respect-Existing | **PASS** | Feature adds plugin infrastructure; does not generate code for target projects. No existing code is refactored. |
| II. Pattern Fidelity | **PASS** | No target project code generation involved. Hook scripts follow platform conventions (bash/PowerShell). |
| III. Architecture & Platform Agnostic | **PASS** | Hooks are cross-platform (Claude Code handles bash/PowerShell selection). MCP config is platform-neutral. Plugin format is portable. |
| IV. Best Practices & Quality | **PASS** | Hooks enforce quality (format, lint, restore). Bash-guard enforces safety. All hooks check for prerequisites before executing. |
| V. Safety & Token Discipline | **PASS** | Hooks are safety features. Agent Skills progressive disclosure keeps token usage under 5,000 for all skill indexes. Skills remain ≤400 lines. |

**Result**: All gates pass. No violations to track.

## Project Structure

### Documentation (this feature)

```text
specs/006-plugin-ecosystem-v1/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── plugin-json.md   # plugin.json schema contract
│   ├── mcp-json.md      # .mcp.json schema contract
│   └── hooks-config.md  # Hook settings contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
# NEW files/directories (this feature)
.claude-plugin/
└── plugin.json          # Plugin manifest (FR-001)

.mcp.json                # MCP server config for csharp-ls (FR-008)

hooks/
├── pre-bash-guard.sh    # Dangerous command blocker (FR-004)
├── post-edit-format.sh  # Auto-format .cs files (FR-005)
├── post-scaffold-restore.sh  # Auto dotnet restore (FR-006)
└── pre-commit-lint.sh   # Format verification before commit (FR-007)

# MODIFIED files (this feature)
skills/**/**/SKILL.md    # Add dotnet-ai- prefix to name field (104 files, FR-002)
README.md                # Add marketplace/differentiation section (FR-010)

# UNCHANGED (existing structure)
src/dotnet_ai_kit/       # Python CLI package (FR-013 — continues working)
commands/                # 26 slash commands
agents/                  # 13 agent definitions
rules/                   # 6 convention rules
templates/               # 11 project scaffolds
knowledge/               # 11 reference documents
config/                  # 4 permission configs
tests/                   # pytest test suite
```

**Structure Decision**: Flat additions at repo root following Claude Code plugin conventions. `.claude-plugin/` contains only the manifest. `hooks/` is a new top-level directory. All existing directories remain unchanged.

## Complexity Tracking

> No constitution violations. Table empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | —          | —                                   |
