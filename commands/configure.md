---
description: "Opens interactive configuration wizard. Use when changing company name, repos, permissions, command style, or any setting."
---

# /dotnet-ai.configure

Configure dotnet-ai-kit settings for this project.

## User Input

```text
$ARGUMENTS
```

## Instructions

**Quick update mode**: If `$ARGUMENTS` names a specific setting, skip the full wizard and update only that setting:
- `style` or `style=short` → jump to Step 5 (command style)
- `permissions` or `permissions=full` → jump to Step 4 (permission level)
- `repos` → jump to Step 3 (repository paths)
- `company` → jump to Step 2 (company settings)
- `tools` → jump to Step 5 (AI tools)
- `show` → show current config and exit (no prompts)

If `$ARGUMENTS` contains `key=value`, apply the value directly without prompting:
- `style=short` → set command_style to "short", save, run CLI, report
- `permissions=full` → set permissions_level to "full", save, run CLI, report

If `$ARGUMENTS` is empty or `--reset`: run the full wizard (all steps).

### Step 1: Load existing config

Read `.dotnet-ai-kit/config.yml`. If it exists, show current values as defaults. If it does not exist, run `/dotnet-ai.init` first.

### Step 2: Company settings (required)

Prompt for company name if not already set:
- **Company name**: Must be a valid C# identifier (letters, digits, underscores; starts with letter or underscore)
- **GitHub org**: Optional, used for `github:org/repo` references
- **Default branch**: main/master/develop (default: main)

### Step 3: Repository paths (microservice mode only)

If detected mode is NOT microservice (check `.dotnet-ai-kit/project.yml`), skip this step entirely.

**Step 3a — Auto-detect sibling repos**: Scan `../` for directories that contain `.git/` and at least one `.sln`, `.slnx`, or `.csproj` file. For each found repo, attempt quick classification:
- `AggregateRoot` or `EventSourcedAggregate` in `*.cs` → **command**
- `IRequestHandler<Event<` or event handler projection patterns → **query**
- `Blazor` in `.csproj` or `*.razor` files → **controlpanel**
- gRPC `Protos/` dir + client registrations → **gateway**
- `IHostedService` + event listener patterns → **processor**
- None matched → **unclassified**

Present detected repos with classified types. Ask: "Accept detected repos? [Y/n/edit]"

**Step 3b — Prompt per role**: For each role (command, query, processor, gateway, controlpanel): if auto-detected, show as default. If not, prompt with three input options:
1. Local path (e.g., `../sibling-repo`)
2. GitHub URL (e.g., `https://github.com/org/repo`) — normalized to `github:org/repo`
3. Skip (press Enter)

Also accepts git SSH URLs (`git@github.com:org/repo.git`) — normalized to `github:org/repo`.

**Step 3c — Validate**: For local paths: check directory exists, contains `.git/`, contains `.sln`/`.slnx`/`.csproj`. For GitHub URLs: optionally verify with `gh repo view org/repo --json name`. If validation fails, warn but allow user to proceed.

**Step 3d — Save** validated repos to `config.yml` repos section.

### Step 4: Permission level

```
Choose a permission level:
  1. Minimal   - Only build/test (ask for everything else)
  2. Standard  - Build, test, git, gh CLI (recommended)
  3. Full      - All operations in working directory
```

### Step 5: AI tools and command style

**AI tools**: Select which AI tools to configure (v1.0: Claude Code only).

**Command style**:
```
Command style:
  1. Full   - Full command names only (/dotnet-ai.specify)
  2. Short  - Short aliases only (/dai.spec)
  3. Both   - Both full names and short aliases (default)
```

**Plugin mode behavior**: When installed as a Claude Code plugin, `dotnet-ai-kit:*` commands are always served by the plugin system. Style changes only affect which local command files are written:
- `full` in plugin mode: no files copied (plugin serves full commands)
- `short` or `both` in plugin mode: only `dai.*.md` short aliases are copied
- Style changes always clean up old command files before writing new ones

### Step 6: Integrations (optional)

- **CodeRabbit**: Enable automated code review integration?
- **MCP Permissions**: Do you use GitHub MCP server? Add MCP permissions?

### Step 7: Save and apply

Save configuration to `.dotnet-ai-kit/config.yml`, then apply permissions and copy commands by running:

```bash
dotnet-ai configure --no-input --company {company} --permissions {level} --style {style}
```

This updates `.claude/settings.json` with the selected permission level and re-copies commands with the selected style.

**Do NOT skip this step.** Writing to config.yml alone does NOT update settings.json or command files. The CLI call is required.

### Step 8: Verify and report

```
Configuration saved:
  Company: {name}
  GitHub Org: {org}
  Default Branch: {branch}
  Permission Level: {level}
  Command Style: {style}
  AI Tools: {tools}
  Repos: {N} of 5 configured
  Permissions: applied to .claude/settings.json
```

## Just-in-Time Prompting

When other commands need config values that are not yet set:
1. Check if the required value exists in config
2. If missing, prompt the user inline
3. Save the updated config
4. Continue with the original command

## Flags

- `--minimal`: Quick setup (company name only)
- `--reset`: Reset to defaults and reconfigure all settings
- `--dry-run`: Show what would be configured without writing config file
- `--verbose`: Show all current config values and what would change

## Error Handling

- **Invalid company name**: Re-prompt with explanation of valid C# identifier rules
- **Invalid repo path**: Warn that path does not exist, allow user to proceed anyway
- **Config not initialized**: Suggest running `/dotnet-ai.init` first
