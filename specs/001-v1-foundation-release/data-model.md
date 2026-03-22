# Data Model: dotnet-ai-kit v1.0

## Overview

dotnet-ai-kit is entirely file-based — no database. All entities are
represented as files on disk in well-defined locations with structured
formats.

## Entity: Configuration

**Location**: `.dotnet-ai-kit/config.yml` (in hub project)
**Format**: YAML
**Created by**: `dotnet-ai init`, `dotnet-ai configure`
**Read by**: All commands

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| version | string | yes | "1.0" | Config schema version |
| company.name | string | yes | (detected) | Company name, valid C# identifier |
| company.github_org | string | no | null | GitHub organization name |
| company.default_branch | string | no | "main" | Default branch for PRs |
| naming.solution | string | no | "{Company}.{Domain}.{Side}" | Solution naming pattern |
| naming.topic | string | no | "{company}-{domain}-{side}" | Service bus topic pattern |
| naming.namespace | string | no | "{Company}.{Domain}.{Side}.{Layer}" | Namespace pattern |
| repos.command | string | no | null | Path or github:org/repo |
| repos.query | string | no | null | Path or github:org/repo |
| repos.processor | string | no | null | Path or github:org/repo |
| repos.gateway | string | no | null | Path or github:org/repo |
| repos.controlpanel | string | no | null | Path or github:org/repo |
| integrations.coderabbit.enabled | bool | no | false | CodeRabbit CLI integration |
| integrations.coderabbit.auto_fix | bool | no | false | Auto-apply safe fixes |
| integrations.coderabbit.severity_threshold | string | no | "warning" | Minimum severity |
| permissions.level | enum | no | "standard" | minimal/standard/full |
| ai_tools | list[string] | yes | ["claude"] | Configured AI tools |
| command_style | enum | no | "both" | full/short/both |

**Validation**: company.name must be a valid C# identifier. repos values
must be null, an existing local path, or `github:{org}/{repo}` format.

## Entity: Project Detection Result

**Location**: `.dotnet-ai-kit/project.yml` (in target project)
**Format**: YAML
**Created by**: `dotnet-ai init`
**Read by**: All commands (cached detection)

| Field | Type | Description |
|-------|------|-------------|
| detected.mode | enum | microservice / generic |
| detected.project_type | enum | command / query-sql / query-cosmos / processor / gateway / controlpanel / vsa / clean-arch / ddd / modular-monolith |
| detected.dotnet_version | string | e.g., "10.0" |
| detected.architecture | string | Detected or configured architecture |
| detected.namespace_format | string | Detected namespace pattern |
| detected.packages | list[string] | NuGet packages found |

## Entity: Feature

**Location**: `.dotnet-ai-kit/features/{NNN}-{short-name}/`
**Format**: Directory containing markdown files
**Created by**: `/dotnet-ai.specify`
**Read by**: All SDD lifecycle commands

| Artifact | File | Created by | Read by |
|----------|------|-----------|---------|
| Specification | spec.md | /specify | /clarify, /plan, /analyze, /review, /pr |
| Plan | plan.md | /plan | /tasks, /implement, /analyze |
| Service Map | service-map.md | /plan (microservice only) | /implement, /analyze |
| Tasks | tasks.md | /tasks | /implement, /status |
| Analysis | analysis.md | /analyze | /implement (warnings), /review |
| Review | review.md | /review | /pr |
| Handoff | handoff.md | /checkpoint, /wrap-up | Next session /specify resume |
| Event Catalogue | event-catalogue/ | /plan (microservice only) | /analyze |
| Undo Log | undo-log.md | /implement, code gen commands | /undo |

**Lifecycle**: draft → clarified → planned → in-progress → completed

## Entity: Rule

**Location**: `rules/{name}.md` (source repo) → `.claude/rules/{name}.md` (user project)
**Format**: Markdown with YAML frontmatter
**Max size**: 100 lines

| Frontmatter Field | Type | Description |
|-------------------|------|-------------|
| alwaysApply | bool | Always true for rules |
| description | string | One-line description |

**Instances** (6):
naming, coding-style, localization, error-handling, architecture, existing-projects

## Entity: Skill

**Location**: `skills/{category}/{name}/SKILL.md` (source repo)
**Format**: Markdown with YAML frontmatter
**Max size**: 400 lines

| Frontmatter Field | Type | Description |
|-------------------|------|-------------|
| name | string | Skill identifier |
| description | string | One-line description |
| category | string | Skill category |
| agent | string | Primary agent that loads this skill |

**Categories** (22): core, architecture, api, data, cqrs, resilience,
security, observability, microservice/command, microservice/query,
microservice/cosmos, microservice/processor, microservice/grpc,
microservice/gateway, microservice/controlpanel, testing, devops,
workflow, infra, quality, docs

## Entity: Agent

**Location**: `agents/{name}.md` (source repo)
**Format**: Markdown (~2-4 KB)
**Structure**: Role, Skills Loaded (numbered list), Responsibilities
(bullet list), Boundaries (what NOT to handle)

**Instances** (13):
dotnet-architect, api-designer, ef-specialist, devops-engineer,
command-architect, query-architect, cosmos-architect,
processor-architect, gateway-architect, controlpanel-architect,
test-engineer, reviewer, docs-engineer

## Entity: Command

**Location**: `commands/{name}.md` (source repo) → `.claude/commands/dotnet-ai.{name}.md` (user project)
**Format**: Markdown with YAML frontmatter
**Max size**: 200 lines

| Frontmatter Field | Type | Description |
|-------------------|------|-------------|
| description | string | One-line command description |

**Instances** (25): specify, clarify, plan, tasks, analyze, implement,
review, verify, pr, init, configure, add-aggregate, add-entity,
add-event, add-endpoint, add-page, add-crud, add-tests, docs,
checkpoint, wrap-up, do, status, undo, explain

## Entity: Template

**Location**: `templates/{type}/` (source repo)
**Format**: Directory with .NET project files (Jinja2 placeholders)
**Override**: `.dotnet-ai-kit/templates/{type}/` in hub project

**Instances** (11):
Microservice: command, query, cosmos-query, processor,
gateway-management, gateway-consumer, controlpanel-module
Generic: generic-vsa, generic-clean-arch, generic-ddd,
generic-modular-monolith

## Entity: Knowledge Document

**Location**: `knowledge/{name}.md` (source repo)
**Format**: Markdown (unlimited length)
**Read by**: `/dotnet-ai.explain`, commands that need reference patterns

**Instances** (11):
event-sourcing-flow, outbox-pattern, service-bus-patterns,
grpc-patterns, cosmos-patterns, testing-patterns,
deployment-patterns, dead-letter-reprocessing, event-versioning,
concurrency-patterns, documentation-standards

## Entity: Permission Config

**Location**: `config/{name}.json` (source repo)
**Format**: JSON (Claude Code settings format)
**Copied to**: `.claude/settings.local.json` in user project

**Instances** (4):
permissions-minimal, permissions-standard, permissions-full,
mcp-permissions

## Relationships

```
Configuration ──owns──→ Feature (1:N, features tracked per hub project)
Feature ──contains──→ spec.md, plan.md, tasks.md, etc. (1:N artifacts)
Agent ──loads──→ Skill (1:N, each agent loads 5-14 skills)
Command ──reads──→ Skill (N:N, commands read relevant skills on demand)
Command ──produces──→ Feature artifacts (each command writes specific artifacts)
Template ──overridden-by──→ Custom Template (1:1, by name match)
```
