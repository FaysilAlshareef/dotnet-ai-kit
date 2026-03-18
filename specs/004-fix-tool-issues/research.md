# Research: Fix Tool Quality Issues

**Branch**: `004-fix-tool-issues` | **Date**: 2026-03-18

## R1: Detection System — Current State Analysis

**Decision**: Rewrite detection to use a multi-signal scoring system instead of name-first classification.

**Rationale**: Current detection uses a two-phase approach where name-based detection (Phase 1) is the "strongest signal" and overrides code pattern analysis. This means a project named `Foo.Bar` with clear command-handler patterns gets classified as `generic` instead of `command`. The spec requires code patterns to be the primary signal with naming as a confidence booster.

**Current implementation issues**:
- `_MICROSERVICE_PATTERNS` checks limited regex patterns (e.g., `Aggregate<T>` for command, `IRequestHandler<Event` for query-sql)
- Name-based detection in `_detect_microservice_by_name()` overrides code pattern results
- `grep_file()` / `grep_files()` scan individual files but don't aggregate signals across the project
- No confidence scoring — first match wins
- No `hybrid` type support
- No detection summary output to the user
- No user override mechanism after detection

**New approach — Signal scoring**:
1. Scan all `.cs` files for code pattern signals (each signal has a type and weight)
2. Scan naming conventions as supplementary signals (lower weight)
3. Scan project references and NuGet packages for structural signals
4. Aggregate all signals per project type, compute confidence score
5. Classify based on highest-scoring type (or `hybrid` if multiple types score above threshold)
6. Display summary with signals and confidence
7. Allow user override via interactive prompt

**Alternatives considered**:
- AST-based analysis (Roslyn): Too heavy, requires .NET SDK for analysis, adds complexity
- AI-based classification (LLM call): Adds latency and cost, not deterministic
- Keep name-first with expanded patterns: Doesn't solve the core problem (naming isn't reliable)

## R2: Detection — Code Pattern Signals for CQRS Microservices

**Decision**: Define comprehensive signal patterns for each project type based on real-world .NET CQRS patterns.

**Command-side signals** (positive):
- Classes inheriting from `Aggregate<T>` or `AggregateRoot`
- Classes implementing `ICommandHandler<T>` or `IRequestHandler<TCommand, TResponse>` where T is a command
- Domain event classes (inheriting `DomainEvent`, `Event<T>`, `INotification`)
- Event publishing (calls to `IMediator.Publish`, `IEventBus`, `OutboxMessage`)
- Event store usage (`IEventStore`, `EventStoreClient`)

**Command-side signals** (negative — reduce confidence):
- Query handler implementations
- Read model classes

**Query-side signals** (positive):
- Classes implementing `IQueryHandler<T>` or `IRequestHandler<TQuery, TResult>` for read operations
- Read model / projection classes
- Event handlers subscribed via `IHostedService`, `BackgroundService`
- Message subscription (`ServiceBusProcessor`, `IConsumer<T>`, queue listeners)
- No aggregate roots or domain events defined

**Query-side signals** (negative):
- Command handlers
- Aggregate classes
- Event publishing

**Processor signals** (positive):
- `IHostedService` or `BackgroundService` implementations
- `ServiceBusProcessor`, `ServiceBusSessionProcessor` usage
- Event routing logic (forwarding to different topics/queues)
- No domain logic (no aggregates, no query handlers)

**Gateway signals** (positive):
- `ApiController` or `ControllerBase` with route attributes
- gRPC client registrations (`AddGrpcClient<T>`)
- HTTP client factory usage (`IHttpClientFactory`, `AddHttpClient`)
- Reverse proxy configuration (YARP)
- No direct database access

**Hybrid signals**:
- Both command handlers AND query handlers present above threshold
- Both event publishing AND event subscription present

**Alternatives considered**:
- Checking only NuGet packages: Not specific enough (MediatR used in both command and query)
- Checking only base classes: Misses projects using custom abstractions

## R3: Permission System — Claude Code Settings Format

**Decision**: Fix permission JSON syntax from colon to space format, add `$schema`, add pre-flight tool validation.

**Rationale**: Two separate issues were identified:

1. **Wrong syntax**: Our permission files use `Bash(dotnet build:*)` with colon separator, but Claude Code's official documentation (https://code.claude.com/docs/en/settings) specifies space syntax: `Bash(dotnet build *)`. The colon format may not match at all, causing all commands to trigger permission prompts.

2. **PATH issue**: The `gh: command not found` error (exit code 127) means the `gh` binary isn't in PATH on Windows when using Git Bash. This is separate from permissions.

**Root cause analysis from official Claude Code docs**:
- Permission rules follow format `Tool` or `Tool(specifier)` with `*` as wildcard
- `Bash(npm run *)` matches commands starting with `npm run`
- Rules evaluated in order: deny first, then ask, then allow — first match wins
- Our files use `Bash(dotnet build:*)` — the `:` is likely treated as literal character, not a separator
- Official docs also recommend `$schema` reference for editor validation

**Correct format** (from Claude Code documentation):
```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(dotnet build *)",
      "Bash(git push *)",
      "Bash(gh pr *)"
    ],
    "deny": [
      "Read(./.env)"
    ]
  }
}
```

**Approach**:
1. Fix all permission JSON files: replace colon syntax with space syntax
2. Add `$schema` reference to all permission JSON files
3. Add pre-flight check that validates external tools are available in PATH
4. Add AI guidance rule to use sequential tool calls instead of `&&` chains
5. Provide clear error messages when tools are missing with installation URLs

**Alternatives considered**:
- Modifying Claude Code's permission engine: Not possible, it's external software
- Keep colon format: Doesn't match official docs, likely broken

## R4: Interactive Configure — Library Choice

**Decision**: Use `rich` library's `Prompt.ask` with choices and `questionary` for multi-select.

**Rationale**: The project already depends on `rich` for terminal output. `rich.prompt.Prompt.ask()` supports choices parameter for single-select. For multi-select checkboxes, `questionary` (or `InquirerPy`) provides the toggle-based selection UI. `questionary` is lightweight, well-maintained, and works cross-platform.

**Configure options to convert to interactive**:
1. Permission level → Single-select (Minimal / Standard / Full)
2. AI tools → Multi-select checklist (Claude Code, Cursor, GitHub Copilot, Codex, Antigravity)
3. Command style → Single-select (Full / Short / Both)
4. Default branch → Text input with default value
5. Company name → Text input with validation
6. GitHub org → Text input with validation

**Alternatives considered**:
- `typer.prompt()` with validation: Current approach, no selection UI
- `click.Choice`: Typer wraps Click but doesn't expose rich selection UI
- `InquirerPy`: Similar to questionary but heavier dependency
- `rich` only: Supports single-select choices but no multi-select checkbox
- `bullet`: Lightweight but unmaintained

## R5: Plan Generation Completeness

**Decision**: Update plan command templates and workflow to conditionally produce supporting artifacts based on feature complexity.

**Rationale**: Plan generation is driven by speckit templates (`.specify/templates/plan-template.md`), not by Python code. The plan command is a slash command that AI agents execute. The fix is to update the plan command/skill instructions to:
1. Analyze the spec for complexity indicators (entities, integrations, multi-repo)
2. For complex features: generate research.md, data-model.md, contracts/, quickstart.md
3. For simple features: generate only plan.md with lightweight content

**Complexity indicators** (feature is complex if any are true):
- Spec mentions 3+ entities or data models
- Spec mentions external service integrations
- Feature spans multiple repositories
- Spec has 5+ functional requirements
- Feature involves data migrations or state transitions

**Alternatives considered**:
- Always generate all artifacts: Overhead for simple tasks
- Let user choose: Adds friction, AI should be smart enough to decide
- Only generate plan.md always: Misses critical design decisions for complex features

## R6: CLI UX Best Practices — Industry Research

**Decision**: Follow clig.dev guidelines and dotnet scaffold patterns for CLI UX polish.

**Sources researched**:
- clig.dev (Command Line Interface Guidelines) — comprehensive CLI UX reference
- Microsoft dotnet scaffold — interactive .NET scaffolding tool
- dotnet/skills — Microsoft's AI agent plugin system for .NET
- Multiple community CLI UX articles (Evil Martians, Lucas Costa, etc.)

**Key patterns to adopt**:

1. **Progress indicators**: Show spinner during detection scanning. clig.dev: "Responsive is more important than fast — print something within 100ms." dotnet scaffold uses spinners during scaffolding.

2. **Next-command suggestions**: After completing an operation, suggest what to do next. clig.dev: "Suggest commands users should run next in conversational workflows."

3. **`--json` flag**: Machine-readable output for scripting. clig.dev: "Provide `--json` flag for structured, machine-parseable output."

4. **`NO_COLOR` support**: Respect `NO_COLOR` environment variable. clig.dev: "Disable colors if NO_COLOR env var is set." Rich library supports this via `force_terminal=False` when `NO_COLOR` is detected.

5. **`--no-input` flag**: Fully non-interactive mode for CI/CD. clig.dev: "Pass `--no-input` flag to disable all prompts." Different from `--minimal` which still prompts for company name.

6. **Error output to stderr**: clig.dev: "Output primary data to stdout, send log messages and errors to stderr."

7. **Ctrl-C handling**: clig.dev: "Exit as quickly as possible when Ctrl-C received. Say something immediately before cleanup."

8. **Exit code mapping**: clig.dev: "Return 0 on success, non-zero on failure. Map non-zero codes to important failure modes."

9. **`$schema` in JSON files**: Claude Code docs recommend adding `$schema` for editor autocomplete in settings.json.

**dotnet scaffold patterns worth adopting**:
- Hierarchical menu navigation (category → item → configure)
- Arrow key navigation with "Back" option
- Spinner/progress during long operations
- All params can be passed non-interactively for automation

**dotnet/skills insight**:
- Microsoft publishes official AI agent skills via `/plugin marketplace add dotnet/skills`
- 9 specialized plugins (dotnet, dotnet-data, dotnet-diag, etc.)
- Future opportunity: publish dotnet-ai-kit skills to this marketplace

**Alternatives considered**:
- Skip UX polish: Functional but feels unprofessional
- Full TUI framework (textual, urwid): Overkill for a CLI tool, adds heavy dependencies
