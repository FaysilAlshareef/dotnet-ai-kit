# Research: Fix All 25 Identified Tool Issues

**Feature**: 007-fix-tool-issues | **Date**: 2026-03-23

## R1: Skill/Agent Copying Strategy

**Decision**: Add `copy_skills()` and `copy_agents()` functions to `copier.py`, following the exact pattern of existing `copy_commands()` and `copy_rules()`. Call them from `init()` and `upgrade()` in `cli.py`.

**Rationale**: The existing `copy_commands()` (lines 56-129) and `copy_rules()` (lines 132-165) in `copier.py` establish a clear pattern: glob source directory for `*.md` files, read content, write to destination preserving structure. Skills need recursive directory copying (category/subcategory), agents are flat (13 files).

**Alternatives considered**:
- Store package path in config and resolve at runtime — rejected because it breaks when tool is uninstalled or upgraded
- Symlinks — rejected because Windows requires admin privileges for symlinks

## R2: Jinja2 StrictUndefined

**Decision**: Change `jinja2.Undefined` to `jinja2.StrictUndefined` in `copier.py` `render_template()` function (line 30).

**Rationale**: `jinja2.StrictUndefined` raises `UndefinedError` when a template variable is missing, catching misconfiguration early. The current `jinja2.Undefined` silently renders empty strings.

**Alternatives considered**:
- `jinja2.DebugUndefined` — shows debug string but doesn't raise error, still silent in production
- Custom undefined class — over-engineering for this use case

## R3: File Locking for Extension Registry

**Decision**: Use `filelock` package (already widely used, MIT license, cross-platform) for extension registry locking. Add to `[project.optional-dependencies]` under `dev` group.

**Rationale**: `filelock` provides cross-platform file locking with context manager support. It's the de facto standard for Python file locking (used by pip, virtualenv, tox).

**Alternatives considered**:
- `fcntl`/`msvcrt` — platform-specific, requires conditional imports
- Database-backed locking — overkill for a YAML file
- No locking with retry — doesn't prevent corruption, only reduces window

## R4: Config Template Fix

**Decision**: Change `permissions: { level: "standard" }` to `permissions_level: "standard"` in `config-template.yml` (line 54). Also update AI tools comment to list only `claude`.

**Rationale**: `models.py` line 205 defines `permissions_level: str = "standard"` as a flat field, not a nested object. The template must match the model schema exactly.

**Alternatives considered**:
- Change the model to accept nested YAML — rejected because it would break existing configs
- Add a migration/compatibility layer — over-engineering for a template fix

## R5: Command-Side Entity Prevention

**Decision**: Add explicit constraint text to `commands/tasks.md` in the Phase 2 (Command Side) section: "CONSTRAINT: Command side is event-sourced. Generate ONLY aggregates, events, value objects, enums, and domain exceptions. NEVER create entities, projections, read models, or lookup tables. If the command side needs to query external state, add a gRPC client call (tracked in Infrastructure tasks)."

**Rationale**: The tool generated a `PrimaryCurrentProjection` table on the command side in a real project because no constraint existed. The command side uses event sourcing where all state is derived from events.

**Alternatives considered**:
- Validate at runtime in Python code — commands are Markdown templates read by AI, not executed by Python
- Add to rules instead of commands — rules are general guidance; commands need explicit task-generation constraints

## R6: Agent Loading in Commands

**Decision**: Add agent loading directives to `commands/implement.md` in Step 2 (Load Skills on Demand). Map repo type to agent file:
- command → `agents/command-architect.md`
- query → `agents/query-architect.md`
- processor → `agents/processor-architect.md`
- gateway → `agents/gateway-architect.md`
- controlpanel → `agents/controlpanel-architect.md`

**Rationale**: 13 agents exist but no command references them. Adding them to `implement.md` provides architectural guidance during code generation without changing the command execution model.

**Alternatives considered**:
- Multi-agent swarm delegation — too complex; current model is single AI reading commands
- Add to every command — only `implement.md` generates code; other commands read/analyze

## R7: Feature Numbering Enforcement

**Decision**: Add clarifying text to `commands/specify.md` Step 3: "Feature numbers are per-repo. Scan ONLY the current repo's `.dotnet-ai-kit/features/` directory. Do not inherit or reference numbers from other repos. If no features exist, start at 001."

**Rationale**: The current text says "scan for highest NNN, increment" but doesn't specify scope. A multi-repo project could confuse cross-repo feature numbers.

**Alternatives considered**:
- Global feature registry — requires shared state between repos, adds complexity
- UUID-based naming — loses the ordered numbering that aids human readability

## R8: New Rules Content Strategy

**Decision**: Create two new rules following existing patterns (under 100 lines each):

1. `rules/configuration.md`: Enforce Options pattern (`IOptions<T>`), `ValidateOnStart()`, no raw `IConfiguration` in services. Reference `skills/core/configuration/SKILL.md` for details.

2. `rules/testing.md`: Enforce test structure (arrange-act-assert), test naming (`{Method}_{Scenario}_{ExpectedResult}`), aggregate testing patterns, event handler testing patterns.

**Rationale**: Rules are always-loaded (max 100 lines). They provide the guardrails that prevent the tool from generating anti-patterns. The configuration rule directly addresses the IConfiguration issue found in production.

**Alternatives considered**:
- Add to existing `architecture.md` rule — already near 100-line budget; separate concerns are clearer
- Skills only (no rules) — skills are loaded on-demand and may be missed; rules are always active

## R9: New Skills Content Strategy

**Decision**: Create two new skills (under 400 lines each):

1. `skills/core/error-handling/SKILL.md`: Domain exceptions inheriting `IProblemDetailsProvider`, gRPC `RpcException` mapping via interceptors, structured error responses.

2. `skills/microservice/command/event-versioning/SKILL.md`: Event schema evolution patterns — upcasting, versioned event data classes, backward-compatible field additions.

**Rationale**: These represent the two most impactful knowledge gaps identified in the skill scan. Error handling was not covered by any existing skill. Event versioning is critical for event-sourced systems but had no guidance.

**Alternatives considered**:
- Saga pattern skill — useful but lower priority than error handling and event versioning
- Pagination skill — partially covered in query-handler skill already

## R10: Extension Cleanup Strategy

**Decision**: Wrap the extension install in a try/except block. On failure after `copytree`, call `shutil.rmtree()` on the destination directory. Add `filelock.FileLock` around registry read-modify-write.

**Rationale**: Current code does `rmtree(dest)` then `copytree(source, dest)` without protection. If `copytree` fails midway, partial files exist with no registry entry.

**Alternatives considered**:
- Copy to temp directory first, then atomic rename — more robust but `shutil.move` across filesystems is not atomic on all platforms
- Database-backed registry — overkill
