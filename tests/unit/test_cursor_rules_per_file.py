"""T052 — Cursor rules emitted per-file (commit 6 / research R12).

Asserts that under feature 019:
1. Cursor plugin manifest declares `rules: "./rules/cursor/"` (per-rule dir,
   NOT one-blob).
2. The Cursor host adapter exists and is registered.
3. The legacy one-blob `.cursor/rules/dotnet-ai-kit.mdc` emitter is treated
   as legacy-managed (cleaned by migrate command per R12); the new
   architecture emits per-rule `.mdc` files under `rules/cursor/<name>.mdc`.

The per-rule .mdc files are SERVED by the plugin install path, not written
per-solution under feature 019 — the test asserts the manifest plus the
host adapter shape.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CURSOR_MANIFEST = REPO / ".cursor-plugin" / "plugin.json"


def test_cursor_plugin_rules_points_to_per_rule_dir() -> None:
    """`.cursor-plugin/plugin.json rules` field MUST point to `./rules/cursor/`."""
    manifest = json.loads(CURSOR_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["rules"] == "./rules/cursor/", (
        f"Cursor manifest must declare `rules: ./rules/cursor/` for per-rule "
        f".mdc files (research R12). Got: {manifest['rules']!r}"
    )


def test_cursor_host_adapter_registered() -> None:
    """Cursor host adapter MUST be importable and registered (T055)."""
    from dotnet_ai_kit.hosts import get_host
    from dotnet_ai_kit.hosts.cursor import CursorHost

    host = get_host("cursor")
    assert isinstance(host, CursorHost)
    assert host.name == "cursor"


def test_cursor_host_install_paths_under_home() -> None:
    """Cursor install paths MUST be under ~/.cursor/ per research R7."""
    from dotnet_ai_kit.hosts.cursor import CursorHost

    paths = CursorHost().install_paths()
    home = Path.home()
    for p in paths:
        assert str(p).startswith(str(home)), (
            f"Cursor install path '{p}' is not under home dir '{home}'"
        )
        assert ".cursor" in p.parts, (
            f"Cursor install path '{p}' does not contain `.cursor`"
        )


def test_cursor_per_solution_writes_is_noop(tmp_path: Path) -> None:
    """Under feature 019, Cursor has NO per-solution writes."""
    from dotnet_ai_kit.hosts.cursor import CursorHost

    result = CursorHost().write_per_solution_files(tmp_path)
    assert result == [], f"Cursor write_per_solution_files() returned {result}"


def test_cursor_rules_dir_exists_in_source() -> None:
    """`rules/cursor/` directory MUST exist in source (per .gitkeep)."""
    cursor_rules = REPO / "rules" / "cursor"
    assert cursor_rules.is_dir(), (
        "rules/cursor/ directory missing — required by Cursor manifest "
        "`./rules/cursor/` field"
    )
