# dotnet-ai-kit

AI dev tool plugin for the full .NET development lifecycle. Provides slash commands, rules, skills, agents, and project templates for AI coding assistants (Claude Code, Cursor, GitHub Copilot, Codex CLI).

## Tech Stack

- **Language**: Python 3.10+
- **CLI Framework**: typer
- **Config Validation**: pydantic v2
- **Template Rendering**: jinja2
- **Terminal Output**: rich (tables, panels, progress)
- **Config Parsing**: pyyaml
- **Build System**: hatchling (pyproject.toml)
- **Testing**: pytest, pytest-cov
- **Linting**: ruff

## Project Structure

```
src/dotnet_ai_kit/       # Python package
  __init__.py             # Package version (__version__)
  cli.py                  # Typer CLI commands (init, check, upgrade, configure, extension-*)
  models.py               # Pydantic v2 models (DotnetAiConfig, DetectedProject, etc.)
  config.py               # YAML config load/save with pydantic validation
  agents.py               # AGENT_CONFIG per AI tool + detection
  detection.py            # Detection helpers (grep, architecture descriptions)
  copier.py               # File copy + Jinja2 template rendering
  extensions.py           # Extension install/remove/list

.claude-plugin/           # Claude Code plugin manifest (plugin.json)
.mcp.json                 # MCP server config (csharp-ls for C# intelligence)
hooks/                    # Claude Code hooks (bash-guard, edit-format, scaffold-restore, commit-lint)
commands/                 # Slash command templates (max 200 lines each)
rules/                    # Always-loaded convention rules (max 100 lines each)
agents/                   # Specialist agent definitions
skills/                   # 124 skills organized by category (Agent Skills spec compliant)
templates/                # Project scaffolding templates + config-template.yml
config/                   # Permission JSON configs (minimal, standard, full, mcp)
knowledge/                # Reference documents
tests/                    # pytest test suite
planning/                 # Planning documents (not shipped)
```

## Build and Test Commands

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=dotnet_ai_kit

# Run a specific test file
pytest tests/test_detection.py

# Lint
ruff check src/ tests/

# Format check
ruff format --check src/ tests/

# Install in development mode
pip install -e ".[dev]"
```

## Key Conventions

1. **Paths**: Always use `pathlib.Path` -- never `os.path.join()` or string concatenation with `/` or `\\`
2. **Cross-platform**: All code must work on Windows, macOS, and Linux
3. **Subprocess calls**: Use `subprocess.run()` with list args -- never `shell=True`
4. **Home directory**: Use `Path.home()` -- never hardcode `~`, `$HOME`, or `%USERPROFILE%`
5. **Temp files**: Use `tempfile` module -- never hardcode `/tmp` or `%TEMP%`
6. **Config files**: YAML for dotnet-ai-kit config, JSON for Claude Code permission settings
7. **Token budgets**: Rules <= 100 lines, commands <= 200 lines, skills <= 400 lines
8. **File encoding**: Always specify `encoding="utf-8"` when reading/writing files
9. **Models**: Use pydantic v2 BaseModel with field_validator decorators
10. **Type hints**: Use `from __future__ import annotations` for modern syntax in Python 3.10+

## Commands (27 total)

| Full Name | Short Alias | Category |
|-----------|-------------|----------|
| `/dotnet-ai.do` | `/dai.do` | Smart |
| `/dotnet-ai.detect` | `/dai.detect` | Project |
| `/dotnet-ai.learn` | `/dai.learn` | Project |
| `/dotnet-ai.specify` | `/dai.spec` | SDD Lifecycle |
| `/dotnet-ai.clarify` | `/dai.clarify` | SDD Lifecycle |
| `/dotnet-ai.plan` | `/dai.plan` | SDD Lifecycle |
| `/dotnet-ai.tasks` | `/dai.tasks` | SDD Lifecycle |
| `/dotnet-ai.analyze` | `/dai.check` | SDD Lifecycle |
| `/dotnet-ai.implement` | `/dai.go` | SDD Lifecycle |
| `/dotnet-ai.review` | `/dai.review` | SDD Lifecycle |
| `/dotnet-ai.verify` | `/dai.verify` | SDD Lifecycle |
| `/dotnet-ai.pr` | `/dai.pr` | SDD Lifecycle |
| `/dotnet-ai.init` | `/dai.init` | Project |
| `/dotnet-ai.configure` | `/dai.config` | Project |
| `/dotnet-ai.add-aggregate` | `/dai.agg` | Code Gen |
| `/dotnet-ai.add-entity` | `/dai.entity` | Code Gen |
| `/dotnet-ai.add-event` | `/dai.event` | Code Gen |
| `/dotnet-ai.add-endpoint` | `/dai.ep` | Code Gen |
| `/dotnet-ai.add-page` | `/dai.page` | Code Gen |
| `/dotnet-ai.add-crud` | `/dai.crud` | Code Gen |
| `/dotnet-ai.add-tests` | `/dai.tests` | Code Gen |
| `/dotnet-ai.docs [sub]` | `/dai.docs` | Documentation (readme, api, adr, deploy, release, service, code, feature, all) |
| `/dotnet-ai.status` | `/dai.status` | Smart |
| `/dotnet-ai.undo` | `/dai.undo` | Smart |
| `/dotnet-ai.explain` | `/dai.explain` | Smart |
| `/dotnet-ai.checkpoint` | `/dai.save` | Session |
| `/dotnet-ai.wrap-up` | `/dai.done` | Session |

## CLI Entry Point

The CLI is registered as `dotnet-ai` in pyproject.toml:
```
[project.scripts]
dotnet-ai = "dotnet_ai_kit.cli:app"
```

## Testing Guidelines

- Use pytest with `tmp_path` fixture for filesystem tests
- Mock external calls (subprocess, network) -- never hit real services
- Test cross-platform path handling
- Each test file should have 5-10 focused test functions
- Test both success paths and error cases
