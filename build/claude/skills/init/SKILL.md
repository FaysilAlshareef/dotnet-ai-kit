---
name: init
description: "Initializes dotnet-ai-kit in a .NET project. Use when setting up a new project for AI-assisted development. Do NOT use to change settings on an already-initialized project (use configure)."
disable-model-invocation: true
---
# /dotnet-ai.init

Initialize dotnet-ai-kit in the current project directory.

## Usage

```
/dotnet-ai.init $ARGUMENTS
```

**Examples:**
- `. --ai claude` — Initialize current directory for Claude Code
- `. --ai claude --type command` — Force command-service project type
- `. --ai claude --permissions standard` — Apply standard permissions during init

## Instructions

### Step 1: Check for existing initialization

Check if `.dotnet-ai-kit/` directory already exists. If it does, report the current state and ask if the user wants to reinitialize with `--force`.

Also check if `.dotnet-ai-kit/briefs/` exists with content. If it does, warn: "This repo has linked features from other repos (in .dotnet-ai-kit/briefs/). They will be preserved." Init and reinit (`--force`) MUST never delete, modify, or overwrite the `briefs/` directory or its contents.

### Step 2: Run the CLI init

```
dotnet-ai init . --ai claude $ARGUMENTS
```

This creates `.dotnet-ai-kit/` per-solution files (config.yml, project.yml, manifest.json, version.txt) and applies permissions to `.claude/settings.json`. Commands, skills, agents, and rules are served by the plugin install path (per feature 019 FR-004/FR-005) — no per-solution copies for plugin-native hosts (Claude/Codex/Cursor).

After the command completes, verify:
1. Exit code was 0 (if non-zero, report the error and stop)
2. `.dotnet-ai-kit/config.yml` exists
3. `.dotnet-ai-kit/version.txt` exists
4. `.claude/settings.json` exists and has permission entries

If `dotnet-ai` is not installed, tell the user: "dotnet-ai CLI not found. Install: `pip install dotnet-ai-kit`"

**Plugin-native mode (feature 019)**: For Claude/Codex/Cursor, commands/skills/agents/rules are served entirely by the plugin install path. The per-solution `.claude/`, `.codex/`, and `.cursor/` directories receive ONLY the manifest-tracked metadata files (settings.json for Claude). Copilot is the lone render-only host: it gets `.github/copilot-instructions.md` + `.github/instructions/*.instructions.md` + `.github/agents/*.agent.md` rendered into the repo per FR-007.

### Step 3: Detect project type using AI

After the CLI init completes, run project detection using the `/dotnet-ai.detect` command workflow:

1. Check for `.sln`, `.slnx`, or `.csproj` files
2. If .NET files exist, read project files and apply the smart-detect skill classification
3. Present detection results to the user for confirmation
4. Save results to `.dotnet-ai-kit/project.yml`

**If detection fails** (no .NET files found, ambiguous results, or any error): skip detection silently and continue. The user can always run `/dotnet-ai.detect` later to detect or re-detect their project.

### Step 4: Report results

After initialization, report:
- Per-solution file list created (config.yml, project.yml, manifest.json, version.txt, settings.json)
- Config file location
- Detection results (if successful):
  - Project type and architecture
  - .NET version
  - Confidence level
- Next steps:
  - If detection was skipped: suggest running `/dotnet-ai.detect` to classify the project
  - Always suggest running `/dotnet-ai.configure` to set company name and repo paths

### Step 5: Verify

Confirm the following per-solution files exist (feature 019 — these are the ONLY files written by init for plugin-native hosts):
- `.dotnet-ai-kit/config.yml`     (UserConfig per data-model § 3)
- `.dotnet-ai-kit/version.txt`    (plugin version stamp)
- `.dotnet-ai-kit/project.yml`    (ProjectMetadata; only if detection / --type provided)
- `.dotnet-ai-kit/manifest.json`  (generated-file inventory, FR-032)
- `.claude/settings.json`         (Claude only — permission merge target)

### Step 6: Detect codebase-memory-mcp (FR-019)

After deployment, the CLI runs `codebase-memory-mcp --version` and records the outcome under `.dotnet-ai-kit/mcp-state.yml :: mcp.codebase-memory-mcp`:

- `accepted` — version `>= 0.6.1`, ready to use.
- `below-minimum` — present but below `0.6.1`; falls back to csharp-ls + grep.
- `unavailable` — not on PATH; offer three install paths:
  1. `pip install "codebase-memory-mcp>=0.6.1"`
  2. Windows: download the latest `codebase-memory-mcp-windows-amd64.zip` release and unzip onto PATH.
  3. From source: `git clone … && pip install -e .`

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
  (No commands/rules/skills/agents copied — served by plugin)

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
  (No commands/rules/skills/agents copied — served by plugin)

  Note: Project type detection skipped. Run /dotnet-ai.detect to classify your project.

Done. Run /dotnet-ai.configure to complete setup.
```

## Flags

- `--force`: Reinitialize even if already configured
- `--type <type>`: Set project type directly (skip AI detection)
- `--dry-run`: Show what would be detected and copied without writing any files
- `--verbose`: Show detailed detection results and file operations
