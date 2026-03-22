# Changelog

All notable changes to dotnet-ai-kit will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Claude Code plugin format (`.claude-plugin/plugin.json`) for marketplace distribution
- Agent Skills specification compliance — all 104 SKILL.md files have `dotnet-ai-` prefixed names for cross-agent compatibility (16+ tools)
- 4 safety/quality hooks: pre-bash-guard (blocks dangerous commands), post-edit-format (auto-format .cs), post-scaffold-restore (auto dotnet restore), pre-commit-lint (format verification)
- C# LSP MCP configuration (`.mcp.json`) pointing to csharp-ls for semantic code intelligence
- Plugin installation section and competitive differentiation table in README
- Hook toggleability — each hook can be independently enabled/disabled via settings

## [1.0.0] - 2026-03-17

### Added
- 26 slash commands for the full SDD lifecycle, code generation, smart workflows, and session management
- 104 skills across 21 categories covering core .NET, architecture, API, data, CQRS, microservices, testing, DevOps, docs, and more
- 13 specialist agents with skill routing tables (dotnet-architect, api-designer, ef-specialist, etc.)
- 6 always-loaded coding convention rules (architecture, coding-style, error-handling, existing-projects, localization, naming)
- 11 project scaffold templates (7 microservice + 4 generic: Clean Arch, DDD, Modular Monolith, VSA)
- 11 knowledge reference documents (event sourcing, outbox, service bus, gRPC, Cosmos DB, deployment, testing, etc.)
- 4 permission config templates (minimal, standard, full, MCP)
- Python CLI (`dotnet-ai`) with `--version` flag, init, check, upgrade, configure, and extension management commands
- AI-powered project detection via `/dotnet-ai.detect` smart skill
- 108 test functions across 6 test files (90% coverage)
- Cross-platform support (Windows, macOS, Linux)
- `--type` flag validation against all 12 known project types
- Support for Claude Code (v1.0)
- 18 planning documents covering full tool design

### Known Limitations (v1.0)
- Only Claude Code is supported as AI tool; Cursor, GitHub Copilot, and Codex CLI are planned for v1.1
- Extension catalog install is not yet available; only `--dev` local path installs work
- Project detection requires the `/dotnet-ai.detect` command (AI-driven); there is no built-in Python fallback
