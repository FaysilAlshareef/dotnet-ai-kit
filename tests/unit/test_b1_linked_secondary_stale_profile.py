"""T138 (commit 18, B-1): linked-secondary stale-profile regression.

Closes the Codex round-3 trap: a pre-019 linked-secondary repo may have a
stale `.claude/rules/architecture-profile.md` left over from a prior bulk-copy
deploy. Plugin-native Claude MUST NOT re-embed that stale profile into the
secondary's `.claude/settings.json` via `copy_hook()` during the next
`deploy_to_linked_repos` invocation.

Per FR-004 and B-1 fix: the architecture profile lives in the plugin install
path (rules/conventions/ + rules/domain/), not per-solution. The stale-profile
gate in `copier.py:_deploy_to_repo_path()` checks `tool_name in
PLUGIN_NATIVE_HOSTS` regardless of file existence.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from dotnet_ai_kit.copier import deploy_to_linked_repos
from dotnet_ai_kit.models import DotnetAiConfig, ReposConfig


def _init_secondary_repo(secondary: Path, version: str = "1.0") -> None:
    kit = secondary / ".dotnet-ai-kit"
    kit.mkdir(parents=True, exist_ok=True)
    (kit / "config.yml").write_text(
        f"version: '{version}'\nai_tools:\n  - claude\ncompany:\n  name: 'Acme'\n",
        encoding="utf-8",
    )
    (kit / "project.yml").write_text(
        "project_type: query-sql\nconfidence: high\n",
        encoding="utf-8",
    )
    (kit / "version.txt").write_text(version, encoding="utf-8")


def _create_package_profiles(pkg_dir: Path) -> None:
    profiles = pkg_dir / "profiles" / "microservice"
    profiles.mkdir(parents=True, exist_ok=True)
    (profiles / "query-sql.md").write_text(
        "---\nalwaysApply: true\n---\n\n- constraint\n", encoding="utf-8"
    )
    (profiles / "generic.md").write_text(
        "---\nalwaysApply: true\n---\n\n- generic constraint\n", encoding="utf-8"
    )
    tpl = pkg_dir / "templates"
    tpl.mkdir(parents=True, exist_ok=True)
    (tpl / "hook-prompt-template.md").write_text("Check.\n\n{{ constraints }}\n", encoding="utf-8")


@patch("subprocess.run")
def test_linked_secondary_with_stale_profile_does_not_embed_hook(mock_run, tmp_path: Path) -> None:
    """Pre-create stale `.claude/rules/architecture-profile.md` in a linked
    secondary; run linked-secondary deploy with plugin-native Claude; assert
    `copy_hook` is NOT called and `.claude/settings.json` has no PreToolUse
    `dotnet-ai-kit-arch` entry referencing the stale profile.
    """
    primary = tmp_path / "primary"
    primary.mkdir()
    secondary = tmp_path / "secondary"
    secondary.mkdir()
    pkg = tmp_path / "pkg"

    _init_secondary_repo(secondary, version="0.9")  # older to force upgrade path
    _create_package_profiles(pkg)

    # Pre-create stale profile (simulating pre-019 layout)
    stale_profile = secondary / ".claude" / "rules" / "architecture-profile.md"
    stale_profile.parent.mkdir(parents=True, exist_ok=True)
    stale_profile.write_text(
        "---\nalwaysApply: true\n---\n\n- STALE constraint\n", encoding="utf-8"
    )

    # Pre-create empty settings.json
    settings_path = secondary / ".claude" / "settings.json"
    settings_path.write_text("{}", encoding="utf-8")

    mock_run.return_value.stdout = ""
    mock_run.return_value.returncode = 0

    config = DotnetAiConfig(
        repos=ReposConfig(query=str(secondary)),
        ai_tools=["claude"],
    )

    with patch("dotnet_ai_kit.copier.copy_hook") as mock_hook:
        deploy_to_linked_repos(primary, config, "1.0", pkg)

    # B-1 stale-profile gate: copy_hook MUST NOT be called even though the
    # stale profile exists on disk, because Claude is in PLUGIN_NATIVE_HOSTS.
    assert not mock_hook.called, (
        f"B-1 stale-profile trap: copy_hook was called {mock_hook.call_count} "
        "time(s) for a linked-secondary plugin-native Claude deploy, despite "
        "the architecture profile being served from the plugin install path. "
        f"Calls: {mock_hook.call_args_list}"
    )

    # Belt-and-braces: settings.json MUST NOT have a `dotnet-ai-kit-arch` hook.
    final_settings = json.loads(settings_path.read_text(encoding="utf-8"))
    pretool = (final_settings.get("hooks") or {}).get("PreToolUse") or []
    arch_hooks = [
        h
        for matcher in pretool
        for h in (matcher.get("hooks") or [])
        if h.get("_source") == "dotnet-ai-kit-arch"
    ]
    assert not arch_hooks, (
        f"B-1 violation: plugin-native Claude linked-secondary deploy embedded "
        f"stale `dotnet-ai-kit-arch` PreToolUse hook in {settings_path}: {arch_hooks!r}"
    )
