# Contributing to dotnet-ai-kit

## Project Structure

```
dotnet-ai-kit/
├── .claude-plugin/           # Claude Code plugin manifest
├── .codex-plugin/            # Codex CLI plugin manifest
├── .cursor-plugin/           # Cursor plugin manifest
├── .mcp.json                 # MCP server config (codebase-memory-mcp)
├── src/                      # CLI tool (Python 3.10+, typer + pydantic + jinja2 + rich)
├── hooks/                    # 7 hooks (bash-guard, edit-format, scaffold-restore,
│                             #   commit-lint, session-start, pretooluse-arch-profile,
│                             #   + hooks.json config)
├── rules/
│   ├── conventions/          # 5 universal rules (always active, ≤100 lines each)
│   ├── domain/               # 11 path-scoped rules (≤100 lines each, carry paths:)
│   └── cursor/               # Cursor-format .mdc copies (auto-generated)
├── agents-source/            # 14 source-of-truth agent definitions
├── agents-claude/            # 13 Claude-rendered agents (with allow-lists)
├── agents-copilot-templates/ # Jinja2 templates for Copilot agent render
├── agents/                   # 14 Cursor sub-agent files (A-005 PASS branch)
├── skills/                   # 124 skills by domain (≤400 lines each)
├── commands/                 # 27 command templates (≤200 lines each)
├── knowledge/                # 16 reference documents
├── templates/                # 12 architecture profiles (7 microservice + 5 generic)
├── config/                   # 4 permission config templates
├── tests/                    # pytest test suite
└── planning/                 # Design specs (not shipped)
```

## Development Setup

```bash
# Clone the repo
git clone https://github.com/FaysilAlshareef/dotnet-ai-kit.git
cd dotnet-ai-kit

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=dotnet_ai_kit

# Lint
ruff check src/ tests/

# Format check
ruff format --check src/ tests/
```

## File Formats

### Skills (`skills/{category}/{name}/SKILL.md`, max 400 lines)

```markdown
---
name: dotnet-ai-skill-name
description: One-line description
category: category-name
agent: agent-that-loads-this
---

# Skill content (patterns, code examples, anti-patterns)
```

**Note**: All skill `name` fields must start with `dotnet-ai-` prefix per the [Agent Skills specification](https://agentskills.io/specification).

### Commands (`commands/{name}.md`, max 200 lines)

```markdown
---
description: One-line description
---

# Command instructions
```

### Rules

Rules live in two directories (constitution v1.0.8):

- `rules/conventions/<name>.md` — 5 universal rules, max 100 lines each.
  Always active; no `paths:` field.
- `rules/domain/<name>.md` — 11 path-scoped rules, max 100 lines each.
  Carry a top-level `paths:` list so they load only when a matching file
  is touched.

```markdown
---
description: One-line description
paths:                   # path-scoped rules only; omit for universal
  - "**/*.cs"
---

# Rule content
```

Cursor-format copies live in `rules/cursor/*.mdc` (universal rules carry
`alwaysApply: true`; path-scoped rules carry `globs:` instead).

## How to Contribute

1. Read the relevant planning doc in `planning/` for the area you want to work on
2. Follow existing patterns in the codebase
3. Run `pytest --cov=dotnet_ai_kit` and `ruff check src/ tests/` before submitting
4. Maintain overall test coverage at 90% or above; new modules should target 95%+
5. Submit a PR with a clear description of what changed and why

## Key Conventions

- Use `pathlib.Path` for all file paths (never `os.path.join`)
- Use `encoding="utf-8"` for all file reads/writes
- All code must work cross-platform (Windows, macOS, Linux)
- Use `subprocess.run()` with list args (never `shell=True`)
- Use pydantic v2 BaseModel with field_validator decorators
