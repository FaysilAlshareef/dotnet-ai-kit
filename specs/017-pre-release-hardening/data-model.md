# Data Model: Pre-Release v1.0.0 Hardening

**Phase**: 1 — Design
**Date**: 2026-04-04

This document specifies the interface shapes for all new/changed components. No database schema — this is a CLI tool with YAML files as its persistence layer.

---

## New Module: `src/dotnet_ai_kit/utils.py`

```python
"""Shared utility functions for dotnet-ai-kit."""

from __future__ import annotations

# Update when a new Haiku model is released
HOOK_MODEL: str = "claude-haiku-4-5-20251001"
HOOK_TIMEOUT_MS: int = 15_000

def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple of ints.

    Pre-release suffixes (e.g., -beta, -rc1) are stripped.
    Non-numeric parts are treated as 0.

    Examples:
        parse_version("1.0.0")       → (1, 0, 0)
        parse_version("1.2.3")       → (1, 2, 3)
        parse_version("1.0.0-beta")  → (1, 0, 0)   # equal to stable
        parse_version("1.0.0-rc.1")  → (1, 0, 0)   # suffix stripped at -
        parse_version("1.a.0")       → (1, 0, 0)    # non-numeric → 0
        parse_version("")            → (0,)
    """
```

**Callers after change**:
- `copier.py`: replaces `_parse_version()`, imports `HOOK_MODEL`/`HOOK_TIMEOUT_MS` for use in `copy_hook()`
- `extensions.py`: replaces `_parse_version_tuple()`
- `cli.py`: imports `HOOK_MODEL`/`HOOK_TIMEOUT_MS` for use in `check --verbose` output

**Rationale for placing hook constants in utils.py**: Both `copier.py` (deployment) and `cli.py` (status reporting) need these values. Placing them in utils.py avoids `cli.py` importing private symbols (`_HOOK_MODEL`) from `copier.py`, which would couple the modules through private internals.

---

## Changed: `copier.py` — `COMMAND_SHORT_ALIASES`

Before (10 entries):
```python
COMMAND_SHORT_ALIASES: dict[str, str] = {
    "specify": "spec",
    "analyze": "check",
    "implement": "go",
    "add-aggregate": "agg",
    "add-entity": "entity",
    "add-event": "event",
    "add-endpoint": "ep",
    "add-tests": "tests",
    "checkpoint": "save",
    "wrap-up": "done",
}
```

After (13 entries — 3 added):
```python
COMMAND_SHORT_ALIASES: dict[str, str] = {
    "specify": "spec",
    "analyze": "check",
    "implement": "go",
    "add-aggregate": "agg",
    "add-entity": "entity",
    "add-event": "event",
    "add-endpoint": "ep",
    "add-crud": "crud",        # NEW
    "add-page": "page",        # NEW
    "add-tests": "tests",
    "configure": "config",     # NEW
    "checkpoint": "save",
    "wrap-up": "done",
}
```

**Generated short filenames** (complete mapping after change):

| Command file | Short file |
|---|---|
| `specify.md` | `dai.spec.md` |
| `analyze.md` | `dai.check.md` |
| `implement.md` | `dai.go.md` |
| `add-aggregate.md` | `dai.agg.md` |
| `add-entity.md` | `dai.entity.md` |
| `add-event.md` | `dai.event.md` |
| `add-endpoint.md` | `dai.ep.md` |
| `add-crud.md` | `dai.crud.md` ← fixed |
| `add-page.md` | `dai.page.md` ← fixed |
| `add-tests.md` | `dai.tests.md` |
| `configure.md` | `dai.config.md` ← fixed |
| `checkpoint.md` | `dai.save.md` |
| `wrap-up.md` | `dai.done.md` |
| All others | `dai.{stem}.md` (unchanged) |

---

## Hook Constants — moved to `utils.py`

```python
# In src/dotnet_ai_kit/utils.py (canonical location)
HOOK_MODEL: str = "claude-haiku-4-5-20251001"   # public, no underscore
HOOK_TIMEOUT_MS: int = 15_000
```

`copier.py` imports them: `from dotnet_ai_kit.utils import HOOK_MODEL, HOOK_TIMEOUT_MS`
`cli.py` imports them for check --verbose output.

Previously these were private inline literals in `copy_hook()`. Moving to utils.py as public constants avoids cross-module private symbol imports and makes the update point discoverable.

---

## New: `extensions.py` — `CatalogInstallError`

```python
class CatalogInstallError(ExtensionError):
    """Raised when catalog-based installation is attempted but not yet supported.

    Caught separately in cli.extension_add() to display a user-friendly hint
    rather than a red error message.
    """
```

Raised in `install_extension()` when `dev=False`:
```python
raise CatalogInstallError(
    f"Catalog-based installs are not yet supported. "
    f"Use --dev to install from a local path: "
    f"dotnet-ai extension-add --dev ./my-ext"
)
```

CLI handler in `extension_add()`:
```python
except CatalogInstallError as exc:
    console.print(f"[yellow]Note:[/yellow] {exc}")
    raise typer.Exit(code=1)
except ExtensionError as exc:
    err_console.print(f"[red]Error: {exc}[/red]")
    raise typer.Exit(code=1) from exc
```

---

## Changed: `models.py` — `DotnetAiConfig` Unknown Key Validator

```python
_KNOWN_CONFIG_KEYS: frozenset[str] = frozenset({
    "version",
    "company",
    "naming",
    "repos",
    "permissions_level",
    "ai_tools",
    "command_style",
    "linked_from",
})

class DotnetAiConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")   # retained

    @model_validator(mode="before")
    @classmethod
    def warn_unknown_keys(cls, values: object) -> object:
        if isinstance(values, dict):
            for key in values:
                if key not in _KNOWN_CONFIG_KEYS:
                    logging.getLogger(__name__).warning(
                        "Unknown config key: '%s'. Known keys: %s",
                        key,
                        ", ".join(sorted(_KNOWN_CONFIG_KEYS)),
                    )
        return values
```

---

## Changed: `config.py` — Atomic Write Pattern

`save_config()` and `save_project()` both change from:
```python
path.write_text(yaml.dump(data), encoding="utf-8")
```
to:
```python
tmp = path.with_suffix(".tmp")
tmp.write_text(yaml.dump(data), encoding="utf-8")
tmp.replace(path)
```

---

## Changed: `extensions.py` — `_check_conflicts()` Rule Name Detection

New check appended to existing `_check_conflicts()`:
```python
# Rule file name collision check
existing_rule_names = {
    Path(r).name
    for ext in installed
    for r in ext.get("rules", [])
}
new_rule_names = {Path(r).name for r in manifest_rules}
rule_conflicts = existing_rule_names & new_rule_names
if rule_conflicts:
    raise ExtensionError(
        f"Rule file name conflict with installed extension: "
        f"{', '.join(sorted(rule_conflicts))}"
    )
```

---

## Changed: `agents.py` — Unsupported Tool Warning

```python
import logging
logger = logging.getLogger(__name__)   # new at module level

def get_agent_config(tool: str) -> dict[str, Any]:
    key = tool.lower()
    if key not in AGENT_CONFIG:
        ...raise ValueError...
    if key not in SUPPORTED_AI_TOOLS:
        logger.warning(
            "Tool '%s' is recognised but not fully supported in v1.0. "
            "Full support planned for v1.1.",
            tool,
        )
    return AGENT_CONFIG[key]
```

---

## New CLI Command: `dotnet-ai changelog`

```
dotnet-ai changelog
```

No flags. Reads `CHANGELOG.md` from `_get_package_dir()` if it exists; otherwise runs `git tag --sort=-version:refname` and shows the 5 most recent with dates. Exits 0 always (CHANGELOG absence is not an error).

---

## Changed CLI: `init --permissions`

```
dotnet-ai init [PATH] [--ai TOOL] [--type TYPE] [--permissions LEVEL] [--force] [--dry-run] [--json]
```

New flag: `--permissions` | values: `minimal`, `standard`, `full` | Optional. When provided, sets `config.permissions_level` before saving and applies permissions during init (no separate `configure` call needed). Invalid values produce a clear typer error.

---

## New File: `rules/multi-repo.md`

Single rule file covering 4 topics. Applied to all multi-repo projects. Max 100 lines.

Topics:
1. **Event contract ownership**: Command service defines and owns event schemas; query/processor services consume only.
2. **Branch naming**: Cross-repo feature branches MUST follow `chore/brief-{NNN}-{name}` pattern.
3. **Deploy order**: Changes MUST be deployed in order: command → processor → query → gateway → controlpanel.
4. **No circular dependencies**: Service A MUST NOT consume events produced by Service B if Service B consumes events from Service A.
