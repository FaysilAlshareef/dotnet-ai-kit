# dotnet-ai-kit

AI dev tool plugin for the full .NET development lifecycle. Provides slash commands, rules, skills, agents, and project templates for AI coding assistants.

## Setup

**Requirements**:
- Python 3.10+
- .NET SDK 8.0+
- Git

**Install**:
```bash
uv tool install dotnet-ai-kit --from git+https://github.com/FaysilAlshareef/dotnet-ai-kit.git
```

## Build & Test

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=dotnet_ai_kit

# Lint
ruff check src/ tests/

# Format check
ruff format --check src/ tests/

# Install in development mode
pip install -e ".[dev]"
```

## Architecture Detection

The tool auto-detects project architecture from code patterns:

**Generic .NET**: Vertical Slice Architecture (VSA), Clean Architecture, Domain-Driven Design (DDD), Modular Monolith

**CQRS Microservices**: Command (event-sourced write side), Query (SQL Server read side), Query (Cosmos DB), Processor (background events), Gateway (REST API), Control Panel (Blazor WASM), Hybrid (multi-side)

Detection scans `.csproj` files, folder structure, NuGet packages, and naming patterns to determine the architecture before generating any code.

## Development Workflow

Specification-Driven Development (SDD) lifecycle:

```
specify → clarify → plan → tasks → analyze → implement → review → verify → PR
```

Quick mode (`/dai.do "feature description"`) chains the full lifecycle automatically.

Each step is also available as an independent command for manual control.

## Code Conventions

- **Paths**: Always use `pathlib.Path` — never `os.path.join()` or string concatenation
- **Subprocess**: Use `subprocess.run()` with list args — never `shell=True`
- **Home directory**: Use `Path.home()` — never hardcode `~` or `$HOME`
- **Temp files**: Use `tempfile` module — never hardcode `/tmp`
- **File encoding**: Always specify `encoding="utf-8"`
- **Models**: Pydantic v2 BaseModel with field_validator decorators
- **Token budgets**: Skills ≤ 400 lines, Commands ≤ 200 lines, Rules ≤ 100 lines

## Testing

- Use pytest with `tmp_path` fixture for filesystem tests
- Mock external calls (subprocess, network) — never hit real services
- Test cross-platform path handling (Windows, macOS, Linux)
- Each test file should have 5-10 focused test functions
- Test both success paths and error cases

## Project Structure

```
src/dotnet_ai_kit/       # Python CLI package
skills/                   # 120 skills organized by category
commands/                 # 27 slash command templates
rules/                    # 15 always-loaded convention rules
agents/                   # 13 specialist agent definitions
hooks/                    # 4 safety hooks (bash scripts)
templates/                # 13 project scaffolding templates
knowledge/                # 16 reference documents
config/                   # Permission JSON configs
tests/                    # pytest test suite
planning/                 # Planning documents (not shipped)
```
