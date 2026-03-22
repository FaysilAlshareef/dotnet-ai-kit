# Research: dotnet-ai-kit v1.0 — Foundation Release

## Research Summary

All technical decisions for v1.0 are pre-resolved by 18 planning documents.
This research phase consolidates the key decisions and validates them against
current best practices.

## Decision 1: CLI Framework

**Decision**: Use **typer** (built on click) as the CLI framework.
**Rationale**: Typer provides type-hint-based argument parsing, automatic
`--help` generation, auto-completion support, and integrates cleanly with
rich for terminal output. It reduces boilerplate compared to raw click
while maintaining full compatibility.
**Alternatives considered**:
- `click`: More mature but more verbose. Typer wraps click anyway.
- `argparse`: Standard library but poor UX, no auto-completion.
- `fire`: Too implicit — magic argument parsing causes confusion.

## Decision 2: Config Validation

**Decision**: Use **pydantic v2** for config schema validation.
**Rationale**: Pydantic provides declarative schema definition, automatic
validation with clear error messages, YAML/JSON serialization support,
and is the standard for Python config models.
**Alternatives considered**:
- `dataclasses` + manual validation: More code, worse error messages.
- `attrs`: Good but less ecosystem support than pydantic.
- `marshmallow`: Schema-first, but heavier for config files.

## Decision 3: Template Rendering

**Decision**: Use **jinja2** for placeholder substitution in command
files and project templates.
**Rationale**: Jinja2 handles `{Company}`, `{Domain}`, `$ARGUMENTS` and
other placeholders. It supports conditional sections (for mode-specific
content), loops (for generating multiple files), and is the de facto
Python template engine.
**Alternatives considered**:
- String `.format()`: No conditionals, no loops, error-prone with braces.
- `mako`: Less popular, overkill for simple substitution.
- `chevron` (mustache): Too limited for conditional sections.

## Decision 4: Project Detection Approach

**Decision**: Pattern-based detection using file scanning and grep.
**Rationale**: Detect project type by scanning for specific code patterns
(Aggregate<T> = Command, IContainerDocument = Cosmos, etc.) as defined
in `planning/16-cli-implementation.md`. This is reliable because each
microservice type has distinctive marker patterns.
**Alternatives considered**:
- AST parsing: Too slow, requires Roslyn/language server.
- Config-only: Misses the zero-config goal.
- Convention-only (folder names): Too fragile, many projects diverge.

## Decision 5: Cross-Platform Strategy

**Decision**: pathlib.Path everywhere, subprocess with list args, no
shell-specific commands.
**Rationale**: Planning doc 16 defines 8 cross-platform rules. Using
pathlib.Path eliminates all path separator issues. Subprocess with list
args avoids shell interpretation differences.
**Alternatives considered**:
- Platform-specific code paths: Maintenance burden, bug surface.
- Docker-based execution: Adds dependency, slower for simple tasks.

## Decision 6: Content Organization

**Decision**: Flat markdown files organized by function (rules/, agents/,
skills/, commands/, knowledge/, templates/).
**Rationale**: This matches the AI tool integration model — files are
copied to user projects as-is. Directory structure maps directly to the
AGENT_CONFIG per tool. Skills have YAML frontmatter for metadata.
**Alternatives considered**:
- Database-backed content: Adds runtime dependency, complicates AI tool integration.
- Single large file per category: Violates token discipline (overloads context).
- JSON/YAML content: Markdown is more readable and matches AI tool formats.

## Decision 7: Skill File Format

**Decision**: SKILL.md with YAML frontmatter (name, description,
category, agent) followed by markdown content.
**Rationale**: YAML frontmatter enables programmatic discovery (which
skills belong to which agent). Markdown body contains patterns, code
examples, and guidance. Max 400 lines enforces focus.
**Alternatives considered**:
- Separate metadata file: More files to manage, harder to keep in sync.
- Frontmatter-free markdown: No programmatic discovery of skill-agent mapping.

## Decision 8: Multi-Repo Workspace Model

**Decision**: No central workspace required. Hub project owns config;
repos can live anywhere on disk.
**Rationale**: Developers already have repos cloned in various locations.
Requiring a central workspace would force reorganization. Config stores
absolute paths or GitHub URLs. Per-feature overrides stored in plan.md.
**Alternatives considered**:
- Central workspace with symlinks: Fragile, platform-specific.
- Git submodules: Too rigid, requires specific structure.
- Monorepo: Contradicts the multi-repo microservice model.

## Decision 9: Command Alias Implementation

**Decision**: Short alias files contain an `$INCLUDE` directive pointing
to the full command. For AI tools without include support, the CLI
duplicates the full content.
**Rationale**: Avoids content duplication for tools that support includes
(Claude Code). Falls back to full copy for tools that don't.
**Alternatives considered**:
- Symlinks: Not supported on all platforms/AI tools.
- Only full names: Slower to type, worse developer experience.
- Only short names: Less discoverable for new users.

## All NEEDS CLARIFICATION Items: Resolved

No technical unknowns remain. All clarifications were resolved in the
spec (session 2026-03-16: --verbose flag, centralized config, template
customization). The 18 planning documents provide comprehensive detail
for every implementation decision.
