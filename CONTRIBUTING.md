# Contributing to dotnet-ai-kit

## Project Structure

```
dotnet-ai-kit/
├── planning/          # 18 planning documents (design specs)
├── src/               # CLI tool (Python 3.10+, typer + pydantic + jinja2 + rich)
├── rules/             # 6 always-loaded convention files
├── agents/            # 13 specialist agents
├── skills/            # 101 skills by domain
├── commands/          # 25 command templates
├── knowledge/         # 11 reference documents
├── templates/         # 11 project scaffolds (7 microservice + 4 generic)
└── config/            # Permission templates
```

## Build Phases

Implementation follows 15 phases defined in `planning/06-build-roadmap.md`:

| Phase | Focus | Priority |
|-------|-------|----------|
| 1 | Foundation (rules, agents, plugin structure) | Critical |
| 2 | Configuration (config.yml, permissions) | Critical |
| 3 | Knowledge documents | Critical |
| 4 | Core + workflow skills | Critical |
| 5 | SDD lifecycle commands | Critical |
| 6-8 | Domain-specific skills | High |
| 9 | Multi-repo implementation | Critical |
| 10 | Review system | High |
| 11 | Code generation commands | High |
| 12-15 | PR, templates, permissions, docs | Medium |

## Planning Documents

All design decisions are documented in `planning/` (18 files). Read these before contributing:

- `01-vision.md` — What this tool is and why
- `04-commands-design.md` — All 25 commands with flows
- `05-rules-design.md` — 6 coding convention rules
- `06-build-roadmap.md` — Build phases and doc index

## How to Contribute

1. Check `planning/06-build-roadmap.md` for what's being built
2. Read the relevant planning doc for the area you want to work on
3. Follow existing patterns in the codebase
4. Submit a PR with a clear description

## Skill File Format

Skills are `SKILL.md` files (max 400 lines) with YAML frontmatter:

```markdown
---
name: skill-name
description: One-line description
category: category-name
agent: agent-that-loads-this
---

# Skill content here (patterns, code examples, rules)
```

## Command File Format

Commands are `.md` files (max 200 lines) with YAML frontmatter:

```markdown
---
description: One-line description
---

# Command instructions here
```

## Rule File Format

Rules are `.md` files (max 100 lines) with:

```markdown
---
alwaysApply: true
description: One-line description
---

# Rule content here
```
