---
description: "Opens interactive configuration wizard. Use when changing company name, naming patterns, or permission levels."
---

# /dotnet-ai.configure

Configure dotnet-ai-kit settings for this project.

## Instructions

Run the interactive configuration wizard. This command uses just-in-time prompting -- only ask for information that is currently missing or when the user explicitly requests a reset.

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

Present detected repos: "Found sibling repos: ../company-query → query (detected), ../company-gateway → gateway (detected)". Ask: "Accept detected repos? [Y/n/edit]"

**Step 3b — Prompt per role**: For each role (command, query, processor, gateway, controlpanel): if auto-detected, show as default. If not, prompt with three input options:
1. Local path (e.g., `../sibling-repo`)
2. GitHub URL (e.g., `https://github.com/org/repo`) — normalized to `github:org/repo`
3. Skip (press Enter)

Also accepts git SSH URLs (`git@github.com:org/repo.git`) — normalized to `github:org/repo`.

**Step 3c — Validate**: For local paths: check directory exists, contains `.git/`, contains `.sln`/`.slnx`/`.csproj`. For GitHub URLs: optionally verify with `gh repo view org/repo --json name`. If validation fails, warn but allow user to proceed.

**Step 3d — Save** validated repos to `config.yml` repos section.

### Step 4: Permission level

```
Permission Configuration:

  Choose a permission level:
  1. Minimal   - Only build/test (ask for everything else)
  2. Standard  - Build, test, git, gh CLI (recommended)
  3. Full      - All operations in working directory

  > _
```

After selection, generate the appropriate permission config file.

### Step 5: Integrations (optional)

Ask about optional integrations:
- **CodeRabbit**: Enable automated code review integration?
- **MCP Permissions**: Do you use GitHub MCP server? Add MCP permissions?

### Flags

- `--minimal`: Only prompt for required fields (company name)
- `--reset`: Reset all configuration to defaults before prompting

### Step 6: Save and apply permissions

Save the configuration to `.dotnet-ai-kit/config.yml`, then **apply permissions to settings.json** by running the CLI:

```bash
dotnet-ai configure --no-input --company {company} --permissions {level} --style {style}
```

This ensures `.claude/settings.json` is updated to match the selected permission level. The CLI:
- Loads the config.yml you just saved (preserving repos, integrations)
- Applies the correct permission template to `.claude/settings.json`
- For **full** mode: writes `"defaultMode": "bypassPermissions"` and 100+ permission entries
- For **standard** mode: writes ~43 common dev permission entries
- For **minimal** mode: writes ~8 build/test-only entries

**Do NOT skip this step.** Writing `permissions_level` to config.yml alone does NOT update settings.json. The CLI call is required.

### Step 7: Verify and report

After the CLI runs, verify that `.claude/settings.json` exists and matches the expected level:
- For **full**: confirm `"defaultMode": "bypassPermissions"` is present
- For **standard/minimal**: confirm `"defaultMode"` is absent

Report:

```
Configuration saved:
  Company: {name}
  GitHub Org: {org}
  Default Branch: {branch}
  Permission Level: {level}
  Repos: {N} of 5 configured
  Permissions: applied to .claude/settings.json
```

## Just-in-Time Prompting

When other commands need config values that are not yet set:
1. Check if the required value exists in config
2. If missing, prompt the user inline
3. Save the updated config
4. Continue with the original command

Example: if `/dotnet-ai.specify` needs the company name and it is empty, prompt for it before proceeding.

## Flags

- `--minimal`: Quick setup (company name only)
- `--reset`: Reset to defaults and reconfigure all settings
- `--dry-run`: Show what would be configured without writing config file
- `--verbose`: Show all current config values and what would change

## Error Handling

- **Invalid company name**: Re-prompt with explanation of valid C# identifier rules
- **Invalid repo path**: Warn that path does not exist, allow user to proceed anyway
- **Config not initialized**: Suggest running `/dotnet-ai.init` first
