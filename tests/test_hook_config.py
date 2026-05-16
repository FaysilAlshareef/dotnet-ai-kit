"""T013 — FR-004 / FR-005 / FR-034: hooks.json shape & settings.json dedup."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOKS_JSON = REPO / "hooks" / "hooks.json"
CLAUDE_SETTINGS = REPO / ".claude" / "settings.json"
TOOL_NAME_RE = re.compile(r"^([A-Za-z]+)(\|[A-Za-z]+)*$")


def _hooks() -> dict:
    return json.loads(HOOKS_JSON.read_text(encoding="utf-8"))


def _iter_groups(events: list[dict]):
    for group in events:
        yield group


def test_hooks_json_matchers_are_tool_names_only() -> None:
    data = _hooks()
    for event_name, groups in data["hooks"].items():
        for group in _iter_groups(groups):
            matcher = group.get("matcher")
            if matcher is None:
                continue
            assert TOOL_NAME_RE.match(matcher), (
                f"hooks.{event_name}: matcher '{matcher}' must contain only "
                f"tool names (e.g. 'Bash', 'Edit|Write'). Permission-rule "
                f"patterns belong in handler `if:`."
            )


def test_pre_commit_lint_uses_if_filter() -> None:
    data = _hooks()
    pre = data["hooks"]["PreToolUse"]
    handlers = [
        h for grp in pre for h in grp.get("hooks", []) if "pre-commit-lint" in h.get("command", "")
    ]
    assert handlers, "pre-commit-lint hook missing"
    for h in handlers:
        assert h.get("if") == "Bash(git commit*)", h


def test_post_edit_format_uses_if_filter_for_cs() -> None:
    data = _hooks()
    post = data["hooks"]["PostToolUse"]
    handlers = [
        h
        for grp in post
        for h in grp.get("hooks", [])
        if "post-edit-format" in h.get("command", "")
    ]
    assert handlers, "post-edit-format hook missing"
    ifs = {h.get("if") for h in handlers}
    assert "Edit(*.cs)" in ifs
    assert "Write(*.cs)" in ifs


def test_post_scaffold_restore_uses_if_filter_for_dotnet_new() -> None:
    data = _hooks()
    post = data["hooks"]["PostToolUse"]
    handlers = [
        h
        for grp in post
        for h in grp.get("hooks", [])
        if "post-scaffold-restore" in h.get("command", "")
    ]
    assert handlers, "post-scaffold-restore hook missing"
    for h in handlers:
        assert h.get("if") == "Bash(dotnet new*)", h


def test_static_claude_settings_does_not_duplicate_plugin_hooks() -> None:
    """FR-034: .claude/settings.json must not statically re-register plugin
    hooks. The dynamic `_source: dotnet-ai-kit-arch` hook is allowed."""
    if not CLAUDE_SETTINGS.is_file():
        return
    settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    hooks = settings.get("hooks", {})

    forbidden = (
        "pre-bash-guard",
        "pre-commit-lint",
        "post-edit-format",
        "post-scaffold-restore",
        "session-start-bootstrap",
    )
    for event, groups in hooks.items():
        for group in groups:
            for handler in group.get("hooks", []):
                if handler.get("_source") == "dotnet-ai-kit-arch":
                    continue
                cmd = handler.get("command", "")
                for plugin_hook in forbidden:
                    assert plugin_hook not in cmd, (
                        f"{event}: static settings.json duplicates plugin hook "
                        f"'{plugin_hook}': {handler!r}"
                    )


def test_dynamic_arch_hook_source_marker_preserved() -> None:
    """FR-004 exception: the dynamic arch hook injected by copier.py uses the
    `_source: dotnet-ai-kit-arch` marker. Verify the source still emits it."""
    src = (REPO / "src" / "dotnet_ai_kit" / "copier.py").read_text(encoding="utf-8")
    assert '"_source": "dotnet-ai-kit-arch"' in src
