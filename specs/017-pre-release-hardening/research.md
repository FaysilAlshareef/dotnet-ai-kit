# Research: Pre-Release v1.0.0 Hardening

**Phase**: 0 — Unknowns resolution
**Date**: 2026-04-04

All implementation decisions below were confirmed by reading the existing codebase. No external unknowns require external research. This document records design decisions and alternatives considered for each non-trivial change.

---

## R-01: Catalog Install Error — `ExtensionError` vs `typer.BadParameter`

**Decision**: Introduce a `CatalogInstallError(ExtensionError)` subclass in `extensions.py`. Update `extension_add()` in `cli.py` to catch it separately and print as `[yellow]Note:[/yellow]` rather than `[red]Error:[/red]`.

**Rationale**: The spec says "raise a user-friendly error." Importing `typer` into `extensions.py` would couple a framework-agnostic module to the CLI framework — undesirable. A subclass allows the CLI layer to discriminate without touching the library layer. The CLI still exits non-zero (required by FR-005), but the output looks like a hint rather than an error.

**Alternatives considered**:
- `raise typer.BadParameter(...)` directly from `extensions.py` — rejected (couples library to CLI framework)
- Update message text only, keep `ExtensionError` — rejected (output still looks like a crash to the user; red color and "Error:" prefix remain)
- `raise SystemExit(1)` with print — rejected (bypasses CLI output layer)

---

## R-02: `DotnetAiConfig` model_validator for unknown keys

**Decision**: Use `@model_validator(mode="before")` on `DotnetAiConfig`. Compare incoming dict keys against a `_KNOWN_CONFIG_KEYS` frozenset. Log warnings via `logging.getLogger(__name__).warning(...)`. Keep `extra="ignore"` in `ConfigDict`.

**Rationale**: `mode="before"` receives the raw dict before field parsing, making key inspection straightforward. This mirrors the existing `validate_detected_paths` pattern added in spec-016. `extra="ignore"` is retained so old configs with removed fields don't break.

**Known top-level keys** (frozenset):
`version`, `company`, `naming`, `repos`, `permissions_level`, `ai_tools`, `command_style`, `linked_from`

**Alternatives considered**:
- `extra="forbid"` — rejected (breaks backward compat; old config.yml files could contain removed fields)
- `extra="allow"` — rejected (no warning, still silent)
- Field-level validators — rejected (can't inspect key names not declared as fields)

---

## R-03: Atomic Writes (`Path.replace()`)

**Decision**: Write to `path.with_suffix(".tmp")`, then call `tmp.replace(path)`.

**Rationale**: Python's `Path.replace()` maps to `os.rename()` on all platforms. On Windows NTFS, `MoveFileEx` with `MOVEFILE_REPLACE_EXISTING` is atomic within the same filesystem. On POSIX it maps to `rename(2)` which is atomic by POSIX specification. The `.tmp` extension is conventional and distinguishable from real YAML files. Using `path.parent / (path.stem + ".tmp")` would also work but `with_suffix` is simpler and readable.

**Edge case**: If `.tmp` already exists (process killed previously), `replace()` overwrites it — correct behavior.

**Alternatives considered**:
- `tempfile.NamedTemporaryFile` + move — works but more complex; same directory is important for atomicity (same filesystem)
- Direct `write_text()` — rejected (truncates file on kill)

---

## R-04: `parse_version()` Pre-Release Stripping

**Decision**: Strip everything after the first `-` before splitting on `.`:
```python
base = version_str.strip().split("-")[0]
parts = [int(p) if p.isdigit() else 0 for p in base.split(".")]
```

**Clarification outcome** (from speckit.clarify): `parse_version("1.0.0-beta")` returns `(1, 0, 0)` — equal to `parse_version("1.0.0")`. Pre-release CLIs satisfy version requirements for the same numeric version.

**Edge cases verified**:
- `""` → `(0,)` (empty string after strip)
- `"1.0"` → `(1, 0)`
- `"1.0.0-rc.1"` → `(1, 0, 0)` (splits on first `-`, ignores `.1` in suffix)
- `"1.a.0"` → `(1, 0, 0)` (non-numeric parts → 0)

---

## R-05: `get_agent_config()` Unsupported Tool Warning

**Decision**: Add a module-level `logger = logging.getLogger(__name__)` to `agents.py` (currently none exists). Log a warning when the tool is in `AGENT_CONFIG` but not in `SUPPORTED_AI_TOOLS`. Do NOT raise — callers that pass `"cursor"` must continue to receive the config (cursor rules deployment partially works).

**Alternatives considered**:
- Raise `ValueError` — rejected (breaks existing configs that include cursor)
- No change — rejected (FR-015 requires warning)

---

## R-06: `after_remove` Hook Consistency

**Decision**: When an `after_remove` hook fails, raise `ExtensionError` with a message that clarifies the extension IS already removed from the registry. Do not roll back the registry deletion.

**Rationale**: By the time `after_remove` runs, the registry entry is already deleted. Rolling back would require re-inserting the entry and re-copying files — disproportionate complexity for a v1.0 fix. The error message must make clear: "Extension 'X' was removed from registry, but cleanup hook '{cmd}' failed: {exc}. Manual cleanup may be required."

**Alternatives considered**:
- Rollback registry on hook failure — rejected (complex, no incidents, deferred to COP-6 which is already deferred)
- Keep warning only — rejected (FR-016 requires raise, inconsistency with after_install)

---

## R-07: `configure --dry-run` Without Init

**Decision**: Modify the init guard to skip when `dry_run=True`. If dry_run and no `.dotnet-ai-kit/` dir, print `[yellow]Warning: Not initialized. Showing default config preview.[/yellow]` then continue with `DotnetAiConfig()` defaults.

**Rationale**: A dry-run preview with default values is useful even without init — it shows what configure would set. The current behavior (exit code 1) is unusable for users exploring the tool before setup.

---

## R-08: `changelog` Command Implementation

**Decision**:
1. Check for `CHANGELOG.md` in `_get_package_dir()` (bundled assets dir or repo root in dev mode)
2. If found, print its content via `console.print()`
3. If not found, run `git tag --sort=-version:refname` (list tags newest first), take first 5, print with `git log {tag} --format="%ai" -1` for dates
4. If git not available, print `"No CHANGELOG.md found and git is not available."` and exit 0

**Alternative**: Print hardcoded version notes — rejected (goes stale immediately, no single source of truth)

---

## R-09: Command Files Usage+Examples Budget

**Decision**: For the 14 commands needing Usage+Examples, use this compact pattern (8 lines):

```markdown
## Usage

```
/dotnet-ai.{name} $ARGUMENTS
```

**Examples:**
- (no args) — {most common use}
- `--dry-run` — Preview without changes
```

For files at or near 200-line limit (specify.md=200, tasks.md=200, analyze.md=197, implement.md=196), trim 8–10 lines from internal steps by:
- Merging redundant sub-steps (e.g., "1a. Do X. 1b. Do Y." → "1. Do X, then Y.")
- Removing bracketed repetitions that reference the same artifact multiple times
- Condensing "if X: do Y; else: do Z" branches to a single rule

---

## R-10: `rules/multi-repo.md` Content

**Decision**: Cover exactly 4 topics per FR-029:
1. Event contract ownership (MUST / MUST NOT)
2. Branch naming convention (`chore/brief-NNN-name`)
3. Deploy order (command → processor → query → gateway → controlpanel)
4. No circular cross-repo dependencies

Target: ~70 lines (well under 100-line limit). Use the same enforcement language as existing rules (MUST, MUST NOT, ALWAYS, NEVER).

---

## Summary

| # | Decision | Confidence |
|---|----------|-----------|
| R-01 | `CatalogInstallError` subclass for friendly catalog message | High |
| R-02 | `model_validator(mode="before")` for unknown config key warnings | High |
| R-03 | `Path.replace()` atomic write pattern | High |
| R-04 | `parse_version()` strips pre-release suffix, equals stable | High (clarified) |
| R-05 | `logger.warning()` in `get_agent_config()` for unsupported tools | High |
| R-06 | `after_remove` raises `ExtensionError`, no registry rollback | High |
| R-07 | `configure --dry-run` skips init guard, shows default preview | High |
| R-08 | `changelog` reads CHANGELOG.md or falls back to git tags | High |
| R-09 | 8-line Usage+Examples block; trim steps in budget-constrained files | High |
| R-10 | `multi-repo.md` ~70 lines, 4 topics, MUST/MUST NOT language | High |

All decisions confirmed. No further research needed. Proceed to Phase 1.
