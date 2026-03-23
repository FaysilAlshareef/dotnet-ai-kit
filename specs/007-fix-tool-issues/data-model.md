# Data Model: Fix All 25 Identified Tool Issues

**Feature**: 007-fix-tool-issues | **Date**: 2026-03-23

## Entities

### Skill File (existing, newly copied during init)

- **Location**: `skills/{category}/{subcategory}/SKILL.md`
- **Identity**: File path (unique by category + subcategory)
- **Attributes**: Markdown content, max 400 lines
- **Categories**: api, architecture, core, cqrs, data, detection, devops, docs, infra, microservice, observability, quality, resilience, security, testing, workflow
- **Lifecycle**: Created in package repo → Copied to project during init → Updated during upgrade → Overwritten on upgrade (no user merge)
- **Relationships**: Referenced by commands (on-demand loading), listed in agents (skills loaded)

### Agent File (existing, newly copied during init)

- **Location**: `agents/{name}.md`
- **Identity**: File name (unique)
- **Attributes**: Role description, skills list, responsibilities, boundaries, routing rules
- **Count**: 13 agents
- **Lifecycle**: Created in package repo → Copied to project during init → Updated during upgrade
- **Relationships**: Referenced by `implement.md` command (per repo type); references skills by path

### Rule File (existing + 2 new)

- **Location**: `rules/{name}.md`
- **Identity**: File name (unique)
- **Attributes**: Markdown content, max 100 lines, always loaded by AI tool
- **Existing**: architecture.md, coding-style.md, error-handling.md, existing-projects.md, localization.md, naming.md, tool-calls.md
- **New**: configuration.md, testing.md
- **Lifecycle**: Created in package repo → Copied to project during init → Always active during AI sessions

### Config Template (existing, modified)

- **Location**: `templates/config-template.yml`
- **Identity**: Single file
- **Key fields**: version, company, naming, repos, integrations, permissions_level (flat string), ai_tools, command_style
- **Validation**: Must pass `DotnetAiConfig` pydantic model validation

### Spec Link (new entity)

- **Location**: `.dotnet-ai-kit/features/{feature-name}/spec-link.md`
- **Identity**: Feature name + repo
- **Attributes**: Feature name, source repo path, primary spec path, creation date
- **Lifecycle**: Created by `tasks.md` command in secondary repos → Read-only reference → Deleted when feature is complete

### Extension Registry (existing, modified for locking)

- **Location**: `.dotnet-ai-kit/extensions.yml`
- **Identity**: Single file per project
- **Attributes**: List of installed extensions with id, name, version, files
- **State transitions**: Empty → Extension added → Extension updated → Extension removed
- **Concurrency**: Protected by file lock during read-modify-write

## Validation Rules

| Entity | Rule | Enforcement |
|--------|------|-------------|
| Skill File | Max 400 lines | Manual (token budget convention) |
| Rule File | Max 100 lines | Manual (token budget convention) |
| Config Template | `permissions_level` must be flat string | Pydantic `DotnetAiConfig` model |
| Repo paths | Must match `github:org/repo` or be valid local path | New pydantic field_validator |
| Feature number | 3-digit zero-padded, starts at 001 per repo | `specify.md` command logic |
| Extension registry | Atomic read-modify-write | `filelock.FileLock` |
