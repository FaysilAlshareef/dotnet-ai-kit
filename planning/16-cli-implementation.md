# dotnet-ai-kit - CLI Implementation Specification

## Overview

The `dotnet-ai` CLI is a Python tool that initializes dotnet-ai-kit into .NET projects, manages configuration, and handles extensions. It bridges the gap between the knowledge base (rules, skills, agents, commands) and the user's AI dev tool.

---

## Architecture

### Package Structure
```
src/dotnet_ai_kit/
├── __init__.py              # CLI entry point (click/typer)
├── cli.py                   # Command definitions
├── agents.py                # AGENT_CONFIG per AI tool
├── extensions.py            # Extension manager
├── detection.py             # Project type detection
├── config.py                # Config schema + validation
├── copier.py                # File copy + template rendering
└── models.py                # Pydantic models for config
```

### Dependencies
- `click` or `typer` — CLI framework
- `pyyaml` — config file parsing
- `pydantic` — config validation
- `jinja2` — template rendering (for {Company}, {Domain} placeholders)
- `rich` — terminal output formatting

### Cross-Platform Requirements

The CLI runs on **Windows, macOS, and Linux**. All code must follow these rules:

1. **File paths**: Always use `pathlib.Path` — never `os.path.join()` or string concatenation with `/` or `\\`
2. **Path storage**: Config files store paths as OS-native format. When reading, normalize with `Path()`:
   ```python
   # Writing config
   config["repos"]["command"] = str(Path(user_input))

   # Reading config
   repo_path = Path(config["repos"]["command"])
   ```
3. **Line endings**: All template files use `.gitattributes` (`* text=auto`). Python writes files in text mode (auto line-ending conversion)
4. **Shell execution**: Use `subprocess.run()` with list args (not shell strings):
   ```python
   # Correct — cross-platform
   subprocess.run(["dotnet", "build"], cwd=repo_path)

   # Wrong — breaks on Windows
   subprocess.run("dotnet build", shell=True, cwd=str(repo_path))
   ```
5. **Home directory**: Use `Path.home()` — never hardcode `~`, `$HOME`, or `%USERPROFILE%`
6. **Environment variables**: Use `os.environ.get()` — never shell-specific expansion
7. **Temp files**: Use `tempfile` module — never hardcode `/tmp` or `%TEMP%`
8. **External tools**: Only invoke cross-platform commands: `dotnet`, `git`, `gh`, `docker`. No `bash`, `sh`, `cmd`, or `powershell` calls

---

## CLI Commands

### `dotnet-ai init [path] [--ai tool]`

Initializes dotnet-ai-kit in a .NET project directory.

**Arguments:**
- `path` — Target directory (default: `.`)
- `--ai` — AI tool(s) to configure. Repeatable. Values: `claude`, `cursor`, `copilot`, `codex`, `antigravity`
- `--force` — Reinitialize even if already configured

**Behavior:**
1. Detect or create the target directory
2. Run project type detection algorithm (see below)
3. Auto-detect installed AI tools if `--ai` not provided
4. Create `.dotnet-ai-kit/` config directory
5. Copy command files to the AI tool's commands directory
6. Copy rules to the AI tool's rules directory
7. Generate default `config.yml` and `project.yml`
8. Report summary

### `dotnet-ai check`

Reports the current state of dotnet-ai-kit in the project.

**Behavior:**
1. Read `.dotnet-ai-kit/config.yml` and `project.yml`
2. Verify all expected command files exist
3. Verify all expected rule files exist
4. Check extension status
5. Report config completeness (company name, repos, etc.)
6. Report version (installed CLI vs. project version)

### `dotnet-ai upgrade`

Upgrades command and rule files to the latest CLI version.

**Behavior:**
1. Compare CLI version with `.dotnet-ai-kit/version.txt`
2. If different: back up, re-copy, update version file
3. Extension files are NOT overwritten
4. See **Upgrade Logic** section for details

### `dotnet-ai configure`

Interactive configuration wizard.

**Behavior:**
1. Prompt for company name, GitHub org, default branch
2. Prompt for repo paths (optional)
3. Prompt for permission level
4. Validate all inputs
5. Write to `.dotnet-ai-kit/config.yml`

### `dotnet-ai extension add|remove|list`

Manages extensions.

**Subcommands:**
- `add <name>` — Install from catalog (GitHub-based)
- `add --dev <path>` — Install from local directory
- `remove <name>` — Uninstall extension
- `list` — Show installed extensions with status

See **Extension System** section for details.

---

## Project Type Detection Algorithm

The detection algorithm runs during `dotnet-ai init .` on existing projects:

### Step 1: Find .NET Projects
- Scan for `*.sln`, `*.slnx`, `*.csproj` files
- Read `<TargetFramework>` from .csproj files
- Determine .NET version

### Step 2: Detect Architecture Mode
Check for microservice patterns first (more specific), then generic:

**Microservice Detection** (check in order):
| Pattern | Detection Method | Project Type |
|---------|-----------------|--------------|
| `Aggregate<T>` base class | Grep for `class.*:.*Aggregate<` | Command |
| `Event<TData>` + OutboxMessage | Grep for `Event<` + `OutboxMessage` | Command |
| `IRequestHandler<Event<` | Grep for handler pattern | Query (SQL or Cosmos) |
| `IContainerDocument` | Grep for interface | Query (Cosmos) |
| Private setters + sequence field | Grep pattern | Query (SQL) |
| `IHostedService` + `ServiceBusSessionProcessor` | Grep | Processor |
| REST Controllers + `AddGrpcClient<` | Grep | Gateway |
| Blazor + `ResponseResult<T>` | Grep for patterns | ControlPanel |

**Generic Detection** (if no microservice patterns):
| Pattern | Detection Method | Architecture |
|---------|-----------------|-------------|
| Feature folders with handlers | Directory structure | Vertical Slice |
| Domain/Application/Infrastructure/API layers | Directory structure | Clean Architecture |
| Bounded context folders | Directory + namespace | DDD |
| Multiple project modules | .sln analysis | Modular Monolith |

### Step 3: Learn Conventions
- Namespace format (from existing files)
- Folder structure
- Naming patterns (from class names)
- NuGet packages (from .csproj)
- DI registration style (from Program.cs)
- Existing service bus topics (from appsettings)
- Existing gRPC service names (from .proto files)

### Detection Error Handling
- **No .NET project found**: "No .sln or .csproj found. Create new project or run in a .NET project directory."
- **Ambiguous detection** (multiple microservice patterns match): Pick the most specific match. Priority: Command > Processor > Query > Gateway > ControlPanel. Report: "Detected {type} (also matches {other}). Override with `dotnet-ai init . --type {type}`."
- **No pattern match** (generic, but unknown architecture): Default to generic mode. Report: "No specific architecture detected. Mode set to generic. Configure architecture in `/dotnet-ai.configure`."
- **Multiple .csproj with different versions**: Use the highest version. Warn: "Multiple .NET versions found ({list}). Using {highest}."

Detection runs on `dotnet-ai init` only. Subsequent commands read from `.dotnet-ai-kit/project.yml` (cached detection result).

### Step 4: Generate Project Config
Write `.dotnet-ai-kit/project.yml`:
```yaml
detected:
  mode: microservice | generic
  project_type: command | query-sql | query-cosmos | processor | gateway | controlpanel | vsa | clean-arch | ddd | modular-monolith
  dotnet_version: "10.0"
  architecture: {detected or configured}
  namespace_format: "{Company}.{Domain}.{Side}.{Layer}"
  packages:
    - MediatR
    - FluentValidation
    - ...
```

---

## File Copy Logic

### Command Registration
For each AI tool, commands are copied to tool-specific directories:

```python
AGENT_CONFIG = {
    "claude": {
        "name": "Claude Code",
        "commands_dir": ".claude/commands",
        "rules_dir": ".claude/rules",
        "command_ext": ".md",
        "command_prefix": "dotnet-ai",
        "args_placeholder": "$ARGUMENTS",
    },
    "cursor": {
        "name": "Cursor",
        "rules_dir": ".cursor/rules",
        "command_ext": ".mdc",
        "command_prefix": "dotnet-ai",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "commands_dir": ".github/agents/commands",
        "command_ext": ".agent.md",
        "command_prefix": "dotnet-ai",
        "args_placeholder": "$ARGUMENTS",
    },
    "codex": {
        "name": "Codex CLI",
        "agents_file": "AGENTS.md",
    },
    "antigravity": {
        "name": "Antigravity",
        # Planned for v1.1 — format TBD when Antigravity defines its extension format
    },
}
```

### Copy Process
1. Read command template from `commands/{name}.md`
2. Replace `$ARGUMENTS` with tool-specific placeholder
3. Write to `{commands_dir}/{prefix}.{name}{ext}`
4. For Cursor: combine all commands + rules into single `.mdc` file
5. For Codex: generate `AGENTS.md` with all agent routing
6. If config `command_style` is "short" or "both": generate short alias files (e.g., `dai.spec.md` → includes `dotnet-ai.specify.md`)

### Rules Copy
1. Copy each rule file from `rules/` to `{rules_dir}/`
2. Preserve YAML frontmatter
3. For Cursor: embed in `.cursor/rules/dotnet-ai-kit.mdc`

---

## Config Schema

```yaml
# .dotnet-ai-kit/config.yml
version: "1.0"

company:
  name: ""                    # Required. Used in namespaces
  github_org: ""              # For cloning repos
  default_branch: "main"     # main/master/develop

naming:
  solution: "{Company}.{Domain}.{Side}"
  topic: "{company}-{domain}-{side}"
  namespace: "{Company}.{Domain}.{Side}.{Layer}"

repos:                        # Optional, can be set per-feature
  command: null               # Path or github:org/repo
  query: null
  processor: null
  gateway: null
  controlpanel: null

integrations:
  coderabbit:
    enabled: false
    auto_fix: false
    severity_threshold: "warning"

permissions:
  level: "standard"           # minimal/standard/full

ai_tools:                     # Detected or configured
  - claude

command_style: "both"           # full | short | both
```

### Validation Rules (Pydantic)
- `company.name`: Required, non-empty, valid C# identifier
- `company.github_org`: Optional, valid GitHub org name
- `company.default_branch`: Default "main"
- `repos.*`: Either null, local path (exists), or `github:{org}/{repo}`
- `permissions.level`: One of minimal/standard/full
- `ai_tools`: At least one tool

---

## Extension System

### Extension Discovery
```bash
dotnet-ai extension add jira          # From catalog (GitHub-based)
dotnet-ai extension add --dev ./ext   # Local development
dotnet-ai extension list              # Show installed
dotnet-ai extension remove jira       # Uninstall
```

### Extension Manifest (extension.yml)
```yaml
extension:
  id: "azure-devops"
  name: "Azure DevOps Integration"
  version: "1.0.0"
  min_cli_version: "1.0.0"

provides:
  commands:
    - name: "dotnet-ai.ado.sync"
      file: "commands/sync.md"
      description: "Sync work items with Azure DevOps"
  rules:
    - file: "rules/ado-conventions.md"

hooks:
  after_tasks:
    command: "dotnet-ai.ado.sync"
    optional: true
    prompt: "Sync tasks to Azure DevOps?"
```

### Extension Installation Process
1. Clone extension repo (or copy from local path)
2. Validate extension.yml manifest
3. Copy command files to detected AI tool's command directory
4. Copy rule files to detected AI tool's rules directory
5. Register hooks in `.dotnet-ai-kit/extensions.yml`
6. Report: "Extension {name} installed. {N} commands, {N} rules added."

### Extensions Registry (.dotnet-ai-kit/extensions.yml)
```yaml
extensions:
  - id: "azure-devops"
    version: "1.0.0"
    source: "github:dotnet-ai-kit/ext-azure-devops"
    installed: "2026-03-14"
    commands: ["dotnet-ai.ado.sync"]
    rules: ["ado-conventions.md"]
    hooks:
      after_tasks: "dotnet-ai.ado.sync"
```

---

## Upgrade Logic

### `dotnet-ai upgrade`

1. Read current CLI version from package
2. Read installed version from `.dotnet-ai-kit/version.txt`
3. If versions differ:
   a. Back up current commands/rules directories
   b. Re-copy all command files (overwrite)
   c. Re-copy all rule files (overwrite)
   d. Re-register extension commands (extension files are NOT overwritten)
   e. Update `.dotnet-ai-kit/version.txt`
   f. Report: "Upgraded from {old} to {new}. {N} commands updated, {N} rules updated."
4. If versions match: "Already up to date."

### Version File
`.dotnet-ai-kit/version.txt` contains the CLI version that last initialized the project.

### Backward Compatibility
- New commands added in later versions are automatically copied
- Removed commands are NOT deleted (user may have customized them)
- Changed commands are overwritten (backup created first)
- Config schema changes: new fields get defaults, removed fields are ignored

---

## Error Handling

| Error | Message | Resolution |
|-------|---------|------------|
| No .NET project found | "No .sln or .csproj files found in {path}" | Run in a .NET project directory |
| AI tool not detected | "No AI tool detected. Use --ai flag" | Specify --ai claude/cursor/copilot/codex |
| Config already exists | "dotnet-ai-kit already initialized. Use --force to reinitialize" | Use --force or dotnet-ai upgrade |
| Invalid company name | "Company name must be a valid C# identifier" | Use letters, digits, underscore |
| Repo not found | "Repo path {path} does not exist" | Check path or use github: prefix |
| Extension conflict | "Command {name} already exists from extension {ext}" | Remove conflicting extension first |

---

## CLI Output Examples

### `dotnet-ai init . --ai claude`
```
dotnet-ai-kit v1.0.0

Scanning project...
  Found: Acme.Order.Commands.sln
  .NET Version: 10.0
  Project Type: Command (Event Sourced)
  Architecture: Microservice

Initializing for Claude Code...
  Created: .dotnet-ai-kit/config.yml
  Created: .dotnet-ai-kit/project.yml
  Copied: 27 commands → .claude/commands/
  Copied: 9 rules → .claude/rules/

✓ dotnet-ai-kit initialized for Claude Code
  Run /dotnet-ai.configure to set up company name and repos
```

### `dotnet-ai check`
```
dotnet-ai-kit v1.0.0

Project: Acme.Order.Commands
Mode: Microservice (Command)
.NET: 10.0

AI Tools:
  ✓ Claude Code — 27 commands, 9 rules
  ✗ Cursor — not configured

Extensions:
  ✓ azure-devops v1.0.0 — 1 command

Config:
  ✓ Company: Acme
  ✓ GitHub Org: acme-corp
  ⚠ Repos: 3 of 5 configured
```
