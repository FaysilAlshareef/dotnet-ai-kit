# Research: Fix Command Style Lifecycle

## Decision 1: Cleanup Strategy — Delete-then-Write vs. Diff-based

**Decision**: Delete-then-write (clean all managed files, then write fresh)

**Rationale**: Simpler, idempotent, and handles all edge cases (renamed files, count changes). The `copy_skills()` and `copy_agents()` functions in the same codebase already use `shutil.rmtree()` for clean overwrites — this follows the established pattern but is more targeted (pattern-match delete instead of directory wipe).

**Alternatives considered**:
- Diff-based cleanup (track what was written last time, delete only differences) — rejected because it requires persisting state and handling stale state files
- Directory wipe (like `copy_skills()` does) — rejected because the commands directory may contain user-created files that must be preserved

## Decision 2: Plugin Detection Method

**Decision**: Check `_get_package_dir() / ".claude-plugin" / "plugin.json"` at runtime

**Rationale**: The `.claude-plugin/plugin.json` is the canonical marker for a Claude Code plugin. In dev mode, `_get_package_dir()` returns the repo root where this file lives. In wheel installs, the `.claude-plugin/` directory is included in the package. This is a simple, reliable check with zero external dependencies.

**Alternatives considered**:
- Environment variable (e.g., `CLAUDE_PLUGIN_MODE=1`) — rejected because it requires user configuration and is error-prone
- Check if `commands/` directory is present in project root (heuristic) — rejected because it's unreliable and doesn't indicate plugin mode specifically
- Config flag in `config.yml` (e.g., `install_mode: plugin`) — rejected because it adds user burden and can get out of sync

## Decision 3: Short Alias Content Strategy

**Decision**: Always write full command content to `dai.*.md` files, regardless of style mode

**Rationale**: The redirect stub approach was a premature optimization. The stubs add complexity (different code paths for `short` vs `both`) while providing no benefit — Claude Code loads command files on-demand, so having full content in both prefixes doesn't waste resources. Removing the stub logic simplifies `copy_commands()` from 3 branches to 2.

**Alternatives considered**:
- Keep stubs but make them include the full content via Jinja2 include — rejected because it adds template complexity for no user benefit
- Use symlinks for `dai.*.md` → `dotnet-ai.*.md` — rejected because symlinks have cross-platform issues (Windows requires elevated permissions)

## Decision 4: Where to Compute is_plugin

**Decision**: Compute in `cli.py` (`_detect_plugin_mode()`) and pass as parameter to `copy_commands()`

**Rationale**: Keeps `copier.py` focused on file operations without knowledge of package layout. The CLI layer already knows the package directory (`_get_package_dir()`) and is the right place for environment detection. This follows the existing pattern where `cli.py` resolves context and passes it to copier functions.

**Alternatives considered**:
- Detect inside `copy_commands()` — rejected because copier.py shouldn't know about plugin.json or package directories
- Global flag/singleton — rejected because it makes testing harder and violates explicit parameter passing

## Decision 5: Managed File Patterns

**Decision**: Use two glob patterns: `dotnet-ai.*.md` and `dai.*.md`

**Rationale**: These are the only two prefixes the tool uses. The patterns are specific enough to avoid matching user files (e.g., `my-custom-command.md` won't match). The `*` in `dotnet-ai.*.md` matches the command name portion (e.g., `specify`, `plan`), so the full pattern is `dotnet-ai.{anything}.md`.

**Alternatives considered**:
- Track created files in a manifest — rejected as over-engineering for a simple pattern-based cleanup
- Use a subdirectory for managed commands — rejected because it would break existing installations and require migration
