---
description: "Detects project architecture, .NET version, and patterns. Use when initializing or learning project structure."
---

# /dotnet-ai.detect

AI-powered project type detection for the current .NET project.

## Usage

```
/dotnet-ai.detect $ARGUMENTS
```

**Examples:**
- (no args) — Detect project type and architecture
- `--verbose` — Show detection signals and confidence breakdown

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may specify a path, override type, or provide hints about their architecture.

## Outline

You are detecting the project type and saving results to `.dotnet-ai-kit/project.yml`. This replaces manual Python-based detection with AI analysis that can understand architectural patterns in context.

Follow this execution flow:

1. **Check prerequisites**
   - Verify `.dotnet-ai-kit/` directory exists. If not, tell the user to run `/dotnet-ai.init` first.
   - Check for `.sln`, `.slnx`, or `.csproj` files. If none found, report "No .NET project detected" and exit.

2. **Gather project context**
   Read the following files (skip any that don't exist):
   - All `*.csproj` files — extract TargetFramework, NuGet packages, project references
   - `*.sln` or `*.slnx` — understand solution structure
   - `Program.cs` or `Startup.cs` — startup configuration
   - Up to 5 representative handler/service/controller files (prioritize by directory):
     1. `**/Features/**/*Handler.cs` or `**/Application/**/Handlers/**/*.cs`
     2. `**/Controllers/**/*.cs`
     3. `**/Services/**/*Service.cs`
     4. `**/Domain/**/Aggregate*.cs` or `**/Domain/**/Core/*.cs`
     5. `**/Endpoints/**/*.cs` or `**/Modules/**/*.cs`
   - Check directory structure: list top-level directories and key subdirectories

3. **Apply smart detection**
   Use the classification rules from the smart-detect skill to determine:
   - **Project type**: command, query-sql, query-cosmos, processor, gateway, controlpanel, hybrid, vsa, clean-arch, ddd, modular-monolith, or generic
   - **Mode**: microservice (CQRS types) or generic (architectural pattern types)
   - **Confidence**: high, medium, or low
   - **Evidence**: top 3 signals that support the classification
   - **Architecture description**: human-readable summary

4. **Present results to user**
   Display the detection results clearly:
   ```
   Detection Results:
     Mode:         {microservice|generic}
     Project Type: {type}
     Architecture: {description}
     .NET Version: {version}
     Confidence:   {high|medium|low}

     Evidence:
       1. {evidence_1}
       2. {evidence_2}
       3. {evidence_3}

     Reasoning: {explanation}
   ```

5. **Confirm with user**
   Ask: "Is this correct? [Y/n/change]"
   - **Y** (default): accept and save
   - **n**: abort without saving
   - **change**: show all valid project types and let user pick:
     ```
     Microservice types:
       1. command          - Event-sourced Command service (CQRS write side)
       2. query-sql        - SQL Server Query service (CQRS read side)
       3. query-cosmos     - Cosmos DB Query service (CQRS read side)
       4. processor        - Background event Processor service
       5. gateway          - REST API Gateway with gRPC backends
       6. controlpanel     - Blazor WASM Control Panel
       7. hybrid           - Hybrid CQRS service (command + query)

     Generic types:
       8. vsa              - Vertical Slice Architecture
       9. clean-arch       - Clean Architecture
      10. ddd              - Domain-Driven Design
      11. modular-monolith - Modular Monolith
      12. generic          - Generic .NET project
     ```

6. **Save results**
   Write the detection results to `.dotnet-ai-kit/project.yml`:
   ```yaml
   mode: {mode}
   project_type: {type}
   dotnet_version: "{version}"
   architecture: "{description}"
   namespace_format: "{detected namespace pattern}"
   packages:
     - {package1}
     - {package2}
   confidence: {confidence}
   confidence_score: {0.0-1.0}
   user_override: {null or user-selected type}
   top_signals:
     - pattern_name: "{signal}"
       signal_type: "{structural|code-pattern|build-config|naming}"
       confidence: "{high|medium|low}"
       evidence: "{detail}"
       is_negative: false
   ```

6b. **Sibling repo scan** (optional)

   Scan `../` for sibling directories that are git repos (contain `.git/`) with `.sln`, `.slnx`, or `.csproj` files. Report as "Sibling repos found:" with detected type if classifiable (command, query, gateway, controlpanel, processor, or unclassified). This feeds context into `/dotnet-ai.configure`.

7. **Report completion**
   ```
   Project detection saved to .dotnet-ai-kit/project.yml

   Next: Run /dotnet-ai.configure to set company name and repo paths.
   ```

## Re-detection

If `.dotnet-ai-kit/project.yml` already exists, show the current detection first:
```
Current detection:
  Type: {current_type} ({current_architecture})
  Confidence: {current_confidence}

Re-running detection...
```

Then proceed with steps 2-7. The new results overwrite the old file.

## Error Handling

- **No .NET project files**: Report clearly and suggest creating a project first
- **Ambiguous detection**: Show top 2-3 candidates with their evidence and let user choose
- **Low confidence**: Warn the user and recommend manual override

## Flags

Pass these as part of `$ARGUMENTS`:
- `--path <dir>`: Detect in a specific directory (default: current directory)
- `--type <type>`: Skip detection and set type directly
- `--json`: Output results as JSON instead of interactive display
