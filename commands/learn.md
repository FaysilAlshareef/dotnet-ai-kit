---
description: "Generates a project constitution from detected patterns. Use when persisting project knowledge across sessions."
---

# /dotnet-ai.learn

Generate or update a project-specific constitution file.

## Usage

```
/dotnet-ai.learn $ARGUMENTS
```

**Examples:**
- `clean architecture` — Learn clean architecture patterns with examples
- `--tutorial` — Step-by-step tutorial for new developers

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are generating a persistent project knowledge file at `.dotnet-ai-kit/memory/constitution.md`. This file captures architecture, domain model, naming conventions, key packages, .NET version, and established patterns so future AI sessions start with full project context.

Follow this execution flow:

1. **Check prerequisites**
   - Verify `.dotnet-ai-kit/` directory exists. If not, tell the user to run `/dotnet-ai.init` first.
   - Check if `.dotnet-ai-kit/memory/constitution.md` already exists:
     - If exists and `--update` flag NOT set: Ask "Constitution already exists. Overwrite or update? [overwrite/update]"
     - If exists and `--update` flag set: Proceed to update mode (merge new findings with existing)

2. **Run project detection**
   - Execute the `/dotnet-ai.detect` workflow internally to classify the project
   - If `.dotnet-ai-kit/project.yml` already exists with valid detection, reuse it
   - If not, perform detection and save to `project.yml`

3. **Deep project scan**
   Beyond basic detection, scan for:
   - **Domain model**: Read aggregate, entity, and value object classes. Extract names, key properties, and relationships.
   - **Events**: Find event/data classes. List event names and their data schemas.
   - **Conventions**: Detect namespace patterns, handler naming, DI registration style, error handling approach, logging framework.
   - **Key packages**: Parse all `.csproj` files for PackageReference items. List the significant ones.
   - **Established patterns**: Identify recurring patterns (e.g., outbox, CQRS, repository, specification, factory methods).
   - Read up to 10 representative source files to understand code style.

4. **Generate constitution**
   Create `.dotnet-ai-kit/memory/` directory if needed.
   Write `.dotnet-ai-kit/memory/constitution.md` with this structure:

   ```markdown
   # Project Constitution: {Project Name}

   **Generated**: {DATE}
   **Mode**: {microservice|generic}
   **Type**: {detected project type}

   ## Architecture
   - Mode: {mode}
   - Type: {type}
   - .NET Version: {version}
   - Architecture: {description}

   ## Domain Model
   ### Aggregates
   - {AggregateRoot}: {key properties, factory methods}

   ### Entities
   - {Entity}: {key properties, relationships}

   ### Value Objects
   - {ValueObject}: {fields}

   ### Events
   - {EventName}: {data fields}

   ## Conventions
   - Namespace Pattern: {detected pattern}
   - Handler Naming: {e.g., {Action}{Entity}Handler}
   - DI Registration: {extension methods|module-based|...}
   - Error Handling: {ProblemDetails|Result<T>|gRPC status}
   - Logging: {framework and style}
   - Localization: {yes/no, approach}

   ## Key Packages
   - {Package}: {version} -- {purpose}

   ## Established Patterns
   - {Pattern}: {description of how it's used}
   ```

5. **Report completion**
   ```
   Project constitution generated.
     Path: .dotnet-ai-kit/memory/constitution.md
     Mode: {mode}
     Type: {type}
     Domain: {N} aggregates, {N} entities, {N} events
     Patterns: {N} detected

   Note: Add this file as an always-loaded rule in your AI tool configuration
   for automatic project context in every session.

   Next: Run /dotnet-ai.configure to complete project setup.
   ```

## Update Mode

When `--update` is active:
1. Read existing constitution
2. Perform fresh scan
3. Merge: keep existing sections, add newly detected items, update changed values
4. Mark updated sections with `(updated {DATE})` annotation

## Dry-Run Behavior

When `--dry-run` is active:
- Print all generated content to the terminal
- Show file path that WOULD be created
- Do NOT create any directories or files
- Prefix output with `[DRY-RUN]`

## Error Handling

- **No .NET project files**: Report "No .NET project detected" and create minimal constitution with config values only.
- **Detection fails**: Warn and proceed with manual project type (ask user).
- **Scan finds nothing**: Generate constitution with Architecture and Key Packages sections only.

## Flags

- `--update`: Refresh existing constitution without full overwrite
- `--dry-run`: Show what would be generated without writing files
- `--verbose`: Show detailed scan results and file-by-file analysis
