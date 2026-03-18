# Contributing to dotnet-ai-kit

## Project Structure

```
dotnet-ai-kit/
├── src/               # CLI tool (Python 3.10+, typer + pydantic + jinja2 + rich)
├── rules/             # 6 always-loaded convention files (≤100 lines each)
├── agents/            # 13 specialist agents
├── skills/            # 101 skills by domain (≤400 lines each)
├── commands/          # 25 command templates (≤200 lines each)
├── knowledge/         # 11 reference documents
├── templates/         # 11 project scaffolds (7 microservice + 4 generic)
├── config/            # 4 permission config templates
├── tests/             # pytest test suite (62 test functions)
└── planning/          # 18 planning documents (design specs, not shipped)
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
name: skill-name
description: One-line description
category: category-name
agent: agent-that-loads-this
---

# Skill content (patterns, code examples, anti-patterns)
```

### Commands (`commands/{name}.md`, max 200 lines)

```markdown
---
description: One-line description
---

# Command instructions
```

### Rules (`rules/{name}.md`, max 100 lines)

```markdown
---
alwaysApply: true
description: One-line description
---

# Rule content
```

## How to Contribute

1. Read the relevant planning doc in `planning/` for the area you want to work on
2. Follow existing patterns in the codebase
3. Run `pytest` and `ruff check src/ tests/` before submitting
4. Submit a PR with a clear description of what changed and why

## Key Conventions

- Use `pathlib.Path` for all file paths (never `os.path.join`)
- Use `encoding="utf-8"` for all file reads/writes
- All code must work cross-platform (Windows, macOS, Linux)
- Use `subprocess.run()` with list args (never `shell=True`)
- Use pydantic v2 BaseModel with field_validator decorators
