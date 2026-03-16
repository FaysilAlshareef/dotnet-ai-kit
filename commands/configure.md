---
description: Interactive configuration wizard for dotnet-ai-kit. Sets company name, repos, permissions, and integrations.
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

### Step 3: Repository paths (optional)

If this is a microservice project, prompt for repo paths:
- Command service repo
- Query service repo
- Processor service repo
- Gateway service repo
- Control Panel repo

Each can be:
- Local path: `/path/to/repo` or `../sibling-repo`
- GitHub reference: `github:org/repo-name`
- Skip (null): press Enter to skip

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

### Step 6: Save and report

Save the configuration to `.dotnet-ai-kit/config.yml` and report:

```
Configuration saved:
  Company: {name}
  GitHub Org: {org}
  Default Branch: {branch}
  Permission Level: {level}
  Repos: {N} of 5 configured
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
