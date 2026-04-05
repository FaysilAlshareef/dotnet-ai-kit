# Quickstart: Pre-Release v1.0.0 Hardening

**Phase**: 1 — Implementation Reference
**Date**: 2026-04-04

Quick-reference guide for implementing all 29 FRs. Organized by file.

---

## Implementation Order (dependency-safe)

1. `utils.py` — create first (depended on by copier.py + extensions.py)
2. `copier.py` — alias fix, constants, deploy loop, token logging, import utils
3. `extensions.py` — CatalogInstallError, after_remove, conflicts, import utils
4. `models.py` — DotnetAiConfig validator
5. `config.py` — atomic writes
6. `agents.py` — logger + warning
7. `cli.py` — all CLI changes (verbose, init flag, changelog, configure guard, etc.)
8. `commands/*.md` — 14 Usage+Examples blocks (independent, no code deps)
9. `rules/multi-repo.md` — new file
10. `skills/workflow/*/SKILL.md` — category field (2 files)
11. `tests/` — all new tests

---

## File-by-File Quick Reference

### `src/dotnet_ai_kit/utils.py` (NEW)

```python
from __future__ import annotations

def parse_version(version_str: str) -> tuple[int, ...]:
    base = version_str.strip().split("-")[0]  # strip pre-release suffix
    parts = []
    for part in base.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0,)
```

### `src/dotnet_ai_kit/copier.py`

1. Add at module top: `from dotnet_ai_kit.utils import parse_version`
2. Remove `_parse_version()` function
3. Replace all `_parse_version(` calls → `parse_version(`
4. Add to `COMMAND_SHORT_ALIASES`: `"configure": "config"`, `"add-crud": "crud"`, `"add-page": "page"`
5. Add `from dotnet_ai_kit.utils import HOOK_MODEL, HOOK_TIMEOUT_MS` to imports (constants live in utils.py — see T001)
6. In `copy_hook()`: replace inline `"claude-haiku-4-5-20251001"` → `HOOK_MODEL`, `15000` → `HOOK_TIMEOUT_MS`
7. In `_resolve_detected_path_tokens()`: before removing paths: line, call `logger.debug("Removing paths: line — token %s resolved to empty", key)`
8. In `deploy_to_linked_repos()` inner loop: `for tool_name in sec_ai_tools:` (was `config.ai_tools`)

### `src/dotnet_ai_kit/extensions.py`

1. Add `from dotnet_ai_kit.utils import parse_version` at top
2. Remove `_parse_version_tuple()` function
3. Replace all `_parse_version_tuple(` calls → `parse_version(`
4. Add `class CatalogInstallError(ExtensionError): ...` near top
5. Change `raise ExtensionError("Catalog-based...")` → `raise CatalogInstallError("Catalog-based installs are not yet supported. Use --dev to install from a local path: dotnet-ai extension-add --dev ./my-ext")`
6. In `after_remove` hook block: change `logger.warning(...)` → `raise ExtensionError(f"Extension '{name}' was removed from registry but cleanup hook '{hook_cmd}' failed: {exc}. Manual cleanup may be required.")`
7. In `_check_conflicts()`: add rule name collision check (see data-model.md R-08)

### `src/dotnet_ai_kit/models.py`

1. Add `import logging` at top (if not present)
2. Add `_KNOWN_CONFIG_KEYS` frozenset above `DotnetAiConfig`
3. Add `from pydantic import model_validator` to pydantic imports
4. Add `warn_unknown_keys` model_validator to `DotnetAiConfig` (see data-model.md)

### `src/dotnet_ai_kit/config.py`

1. In `save_config()`: replace `path.write_text(...)` with atomic pattern
2. In `save_project()`: same atomic pattern

### `src/dotnet_ai_kit/agents.py`

1. Add `import logging` at top
2. Add `logger = logging.getLogger(__name__)` at module level
3. In `get_agent_config()`: after confirming key in `AGENT_CONFIG`, check `if key not in SUPPORTED_AI_TOOLS: logger.warning(...)`

### `src/dotnet_ai_kit/cli.py`

**Verbose except blocks** (5 locations):
- Line ~463 (init, detected_paths): `_verbose_log(verbose, f"Skipping detected paths load: {exc}")`
- Line ~567 (init, hook): `_verbose_log(verbose, f"Skipping hook deployment: {exc}")`
- Line ~1642 (configure, detected_paths): `_verbose_log(verbose, f"Skipping detected paths load: {exc}")`
- Line ~1683 (configure, project.yml): `_verbose_log(verbose, f"Skipping profile type load: {exc}")`
- Line ~1709 (configure, hook): `_verbose_log(verbose, f"Skipping hook deployment: {exc}")`

**configure --dry-run guard**: Move `if not (target / ".dotnet-ai-kit").is_dir():` block to after the `if dry_run:` early-return. Or: wrap guard in `if not dry_run:`.

**upgrade --force profile/hook**: Add `if force:` condition to ensure profile+hook deployment runs when `force=True` even if version matches.

**extension-list empty state**: After `extensions = list_extensions(target)`, if empty:
```python
if not extensions:
    console.print("No extensions installed. Use 'dotnet-ai extension-add --dev <path>' to install one.")
    return
```

**configure --json warnings**: After saving config, if `json_output` and `config.permissions_level == "full"`:
```python
data["warnings"] = ["bypassPermissions enabled — all operations run without confirmation"]
```

**check --verbose profile/hook detail**: After `console.print(table)`, if verbose:
```python
for tool_name in config.ai_tools:
    ts = _get_tool_status(tool_name, get_agent_config(tool_name), target)
    if ts["profile"]:
        rules_dir = get_agent_config(tool_name).get("rules_dir", "")
        console.print(f"  Profile: {rules_dir}/architecture-profile.md")
    if ts["hook"] and tool_name == "claude":
        console.print(f"  Hook: model={HOOK_MODEL}, timeout={HOOK_TIMEOUT_MS // 1000}s")
```
Note: `from dotnet_ai_kit.utils import HOOK_MODEL, HOOK_TIMEOUT_MS` at top of cli.py — public constants from utils.py, not private symbols from copier.

**init --permissions flag**:
```python
permissions: Optional[str] = typer.Option(
    None, "--permissions",
    help="Permission level (minimal/standard/full).",
)
```
Validate value if provided. Apply before saving config and before `copy_permissions()` call.

**changelog command**:
```python
@app.command("changelog")
def changelog() -> None:
    """Show project changelog or recent version tags."""
    package_dir = _get_package_dir()
    changelog_path = package_dir / "CHANGELOG.md"
    if changelog_path.is_file():
        console.print(changelog_path.read_text(encoding="utf-8"))
        return
    # Fallback: git tags
    result = subprocess.run(
        ["git", "tag", "--sort=-version:refname"],
        capture_output=True, text=True,
    )
    tags = [t for t in result.stdout.strip().splitlines() if t][:5]
    if not tags:
        console.print("No changelog available.")
        return
    for tag in tags:
        date_result = subprocess.run(
            ["git", "log", tag, "--format=%ai", "-1"],
            capture_output=True, text=True,
        )
        date_str = date_result.stdout.strip()[:10]
        console.print(f"  {tag}  {date_str}")
```

**extension-add catalog handler** — add before existing `except ExtensionError`:
```python
except CatalogInstallError as exc:
    console.print(f"[yellow]Note:[/yellow] {exc}")
    raise typer.Exit(code=1)
```
Also import `CatalogInstallError` from `dotnet_ai_kit.extensions`.

---

## `rules/multi-repo.md` Template

```markdown
---
description: Multi-repo coordination rules for CQRS microservice features.
alwaysApply: true
---

# Multi-Repo Coordination

## Event Contract Ownership

- The **command service** MUST be the sole owner of event schemas.
- Query and processor services MUST NOT define or modify event data types.
- Event schema changes MUST be backward-compatible until all consumers are updated.

## Cross-Repo Branch Naming

- Feature branches that span multiple repositories MUST follow the pattern:
  `chore/brief-{NNN}-{short-name}` where NNN matches the feature ID.
- NEVER commit multi-repo feature work directly to main/master/develop.

## Deploy Order

When deploying a feature across services, MUST follow this order:
1. command (event producers and aggregate changes)
2. processor (event consumers that update read models)
3. query (read model consumers)
4. gateway (API changes last)
5. controlpanel (UI changes last)

MUST NOT deploy query or gateway before command in production.

## No Circular Dependencies

- Service A MUST NOT consume events produced by Service B if Service B
  already consumes events from Service A.
- NEVER create two-way event coupling between services — use a mediator or
  redesign event ownership.
```

---

## Test Checklist

| Test | File | Pattern |
|------|------|---------|
| `test_parse_version_basic` | `test_utils.py` | `assert parse_version("1.2.3") == (1, 2, 3)` |
| `test_parse_version_pre_release` | `test_utils.py` | `assert parse_version("1.0.0-beta") == (1, 0, 0)` |
| `test_parse_version_non_numeric` | `test_utils.py` | `assert parse_version("1.a.0") == (1, 0, 0)` |
| `test_command_aliases_config_crud_page` | `test_copier.py` | Verify `dai.config.md`, `dai.crud.md`, `dai.page.md` generated |
| `test_catalog_install_friendly_message` | `test_extensions.py` | `CatalogInstallError` raised; message has "--dev" |
| `test_extension_add_catalog_exits_nonzero` | `test_cli.py` | CLI exit != 0, "not yet supported" in output |
| `test_after_remove_hook_failure_raises` | `test_extensions.py` | Mock subprocess → CalledProcessError; assert ExtensionError |
| `test_extension_rule_conflict_detected` | `test_extensions.py` | Two exts with same rule name → ExtensionError |
| `test_dotnet_ai_config_warns_unknown_key` | `test_models.py` | caplog: WARNING contains "foo" |
| `test_save_config_no_tmp_after_success` | `test_config.py` | No `.tmp` file after save |
| `test_extension_list_empty_message` | `test_cli.py` | "No extensions installed" in output |
| `test_changelog_exits_0` | `test_cli.py` | exit 0 |
| `test_init_permissions_flag` | `test_cli.py` | `--permissions standard` applies level |
| `test_configure_dry_run_without_init` | `test_cli.py` | No exit code 1 |
| `test_check_verbose_profile_detail` | `test_cli.py` | "architecture-profile.md" in verbose output |
