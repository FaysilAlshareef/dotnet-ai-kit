---
description: "Initializes dotnet-ai-kit in a .NET project. Use when setting up a new project for AI-assisted development."
---

# /dotnet-ai.init

Initialize dotnet-ai-kit in the current project directory.

## Instructions

### Step 1: Check for existing initialization

Check if `.dotnet-ai-kit/` directory already exists. If it does, report the current state and ask if the user wants to reinitialize with `--force`.

Also check if `.dotnet-ai-kit/briefs/` exists with content. If it does, warn: "This repo has linked features from other repos (in .dotnet-ai-kit/briefs/). They will be preserved." Init and reinit (`--force`) MUST never delete, modify, or overwrite the `briefs/` directory or its contents.

### Step 2: Run the CLI init

```
dotnet-ai init . --ai claude $ARGUMENTS
```

This creates the config directory, copies commands/rules, and applies permissions to `.claude/settings.json`.

After the command completes, verify:
1. Exit code was 0 (if non-zero, report the error and stop)
2. `.dotnet-ai-kit/config.yml` exists
3. `.dotnet-ai-kit/version.txt` exists
4. `.claude/settings.json` exists and has permission entries

If `dotnet-ai` is not installed, tell the user: "dotnet-ai CLI not found. Install: `pip install dotnet-ai-kit`"

**Plugin mode**: When running as a plugin, full-prefix commands (`dotnet-ai.*.md`) are NOT copied to `.claude/commands/` because the plugin system already serves them as `dotnet-ai-kit:*`. Only short aliases (`dai.*.md`) are copied when the command style includes "short".

### Step 3: Detect project type using AI

After the CLI init completes, run project detection using the `/dotnet-ai.detect` command workflow:

1. Check for `.sln`, `.slnx`, or `.csproj` files
2. If .NET files exist, read project files and apply the smart-detect skill classification
3. Present detection results to the user for confirmation
4. Save results to `.dotnet-ai-kit/project.yml`

**If detection fails** (no .NET files found, ambiguous results, or any error): skip detection silently and continue. The user can always run `/dotnet-ai.detect` later to detect or re-detect their project.

### Step 4: Report results

After initialization, report:
- Number of commands copied
- Number of rules copied
- Config file location
- Detection results (if successful):
  - Project type and architecture
  - .NET version
  - Confidence level
- Next steps:
  - If detection was skipped: suggest running `/dotnet-ai.detect` to classify the project
  - Always suggest running `/dotnet-ai.configure` to set company name and repo paths

### Step 5: Verify

Confirm the following files/directories exist:
- `.dotnet-ai-kit/config.yml`
- `.dotnet-ai-kit/version.txt`
- AI tool command directory (e.g., `.claude/commands/`)
- AI tool rules directory (e.g., `.claude/rules/`)
- `.dotnet-ai-kit/project.yml` (only if detection succeeded)

## Error Handling

- **No .NET project found**: Skip detection, complete init without project type. Suggest running `/dotnet-ai.detect` later.
- **AI tool not detected**: Ask the user to specify with `--ai` flag
- **Already initialized**: Show current state and offer `--force` reinit
- **Detection fails for any reason**: Log a note and continue with init. Detection is not blocking.

## Output Format

```
dotnet-ai-kit v1.0.0

Initializing for Claude Code...
  Created: .dotnet-ai-kit/config.yml
  Copied: {N} commands
  Copied: {N} rules

Detecting project type...
  Mode: {mode}
  Project Type: {type}
  Architecture: {architecture}
  .NET Version: {version}
  Confidence: {confidence}
  Saved: .dotnet-ai-kit/project.yml

Done. Run /dotnet-ai.configure to complete setup.
```

Or if detection was skipped:

```
dotnet-ai-kit v1.0.0

Initializing for Claude Code...
  Created: .dotnet-ai-kit/config.yml
  Copied: {N} commands
  Copied: {N} rules

  Note: Project type detection skipped. Run /dotnet-ai.detect to classify your project.

Done. Run /dotnet-ai.configure to complete setup.
```

## Flags

- `--force`: Reinitialize even if already configured
- `--type <type>`: Set project type directly (skip AI detection)
- `--dry-run`: Show what would be detected and copied without writing any files
- `--verbose`: Show detailed detection results and file operations
