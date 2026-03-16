# CLI Command Contracts: dotnet-ai-kit v1.0

## `dotnet-ai init [path] [--ai tool] [--type type] [--force]`

**Input**: Target directory path, AI tool name(s), optional project type
**Output**: `.dotnet-ai-kit/` config directory, AI tool files (commands, rules)
**Exit codes**: 0 = success, 1 = no .NET project found, 2 = already initialized

## `dotnet-ai check`

**Input**: None (reads from current project's `.dotnet-ai-kit/`)
**Output**: Status report (version, project type, AI tools, extensions, config completeness)
**Exit codes**: 0 = all good, 1 = issues found

## `dotnet-ai upgrade`

**Input**: None (compares CLI version with project version)
**Output**: Updated command/rule files, version.txt
**Exit codes**: 0 = upgraded or already current, 1 = error

## `dotnet-ai configure [--minimal] [--reset]`

**Input**: Interactive prompts (company, org, branch, repos, permissions)
**Output**: `.dotnet-ai-kit/config.yml`, optionally `.claude/settings.local.json`
**Exit codes**: 0 = success

## `dotnet-ai extension add|remove|list [name] [--dev path]`

**Input**: Extension name or local path
**Output**: Installed extension files, updated `.dotnet-ai-kit/extensions.yml`
**Exit codes**: 0 = success, 1 = extension not found, 2 = conflict

## Common Flags (all commands)

| Flag | Description |
|------|-------------|
| `--verbose` | Output diagnostic info (detection, config, operations) |
| `--version` | Show CLI version |
| `--help` | Show command help |
