---
description: Initialize dotnet-ai-kit in a .NET project. Detects project type, copies commands/rules, creates config.
---

# /dotnet-ai.init

Initialize dotnet-ai-kit in the current project directory.

## Instructions

Run the `dotnet-ai init` CLI command to set up dotnet-ai-kit for this project. Follow these steps:

### Step 1: Check for existing initialization

Check if `.dotnet-ai-kit/` directory already exists. If it does, report the current state and ask if the user wants to reinitialize with `--force`.

### Step 2: Detect or create project

**Existing project detected** (`.sln` or `.csproj` files found):

```
dotnet-ai init . --ai claude $ARGUMENTS
```

Report the detection results:
- Solution/project file found
- .NET version detected
- Project type (Command, Query, Processor, Gateway, ControlPanel, or generic architecture)
- Architecture mode (Microservice or Generic)

**No project detected**:

Ask the user what they want to create:
1. What project type? (Command, Query-SQL, Query-Cosmos, Processor, Gateway, ControlPanel, or generic: VSA, Clean Architecture, DDD, Modular Monolith)
2. Company name (for namespace)
3. Domain name (for namespace)
4. .NET version (default: latest)

Then run:
```
dotnet-ai init . --ai claude --type <selected-type> $ARGUMENTS
```

### Step 3: Report results

After initialization, report:
- Number of commands copied
- Number of rules copied
- Config file location
- Next steps: suggest running `/dotnet-ai.configure` to set company name and repo paths

### Step 4: Verify

Confirm the following files/directories exist:
- `.dotnet-ai-kit/config.yml`
- `.dotnet-ai-kit/version.txt`
- AI tool command directory (e.g., `.claude/commands/`)
- AI tool rules directory (e.g., `.claude/rules/`)

## Error Handling

- **No .NET project found**: Offer to create a new project from a template
- **AI tool not detected**: Ask the user to specify with `--ai` flag
- **Already initialized**: Show current state and offer `--force` reinit
- **Detection ambiguous**: Show all matches and ask user to pick with `--type`

## Output Format

Use clear, structured output:
```
dotnet-ai-kit v1.0.0

Scanning project...
  Found: {solution_name}.sln
  .NET Version: {version}
  Project Type: {type}
  Architecture: {architecture}

Initializing for {AI tool}...
  Created: .dotnet-ai-kit/config.yml
  Copied: {N} commands
  Copied: {N} rules

Done. Run /dotnet-ai.configure to complete setup.
```

## Flags

- `--force`: Reinitialize even if already configured
- `--dry-run`: Show what would be detected and copied without writing any files
- `--verbose`: Show detailed detection results and file operations
