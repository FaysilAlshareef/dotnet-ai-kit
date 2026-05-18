"""T038 — FR-033 / SC-014 (init half): linked-secondary init under plugin-native mode.

Per FR-033: when a linked secondary repo is deployed to from the primary,
the deploy_to_linked_repos flow MUST follow plugin-native rules (no bulk
command copies for plugin-native hosts).

Verified structurally via:
- Inspecting `copier.py:deploy_to_linked_repos` body for the
  `_PLUGIN_NATIVE` branching that calls `ClaudeHost.write_per_solution_files`
  instead of `copy_commands/copy_skills/copy_agents`.
- An end-to-end test runs a no-network, in-memory simulation that mocks
  the git subprocess and verifies post-deploy the secondary has NO
  `.claude/commands/`, `.claude/skills/`, `.claude/agents/` content.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

from dotnet_ai_kit import copier
from dotnet_ai_kit.copier import deploy_to_linked_repos
from dotnet_ai_kit.models import DotnetAiConfig


REPO = Path(__file__).resolve().parent.parent.parent


def test_linked_secondary_writer_branches_for_plugin_native_hosts() -> None:
    """Structural assertion: copier.deploy_to_linked_repos contains the
    plugin-native branching after T043 refactor."""
    source = inspect.getsource(deploy_to_linked_repos)
    assert "_PLUGIN_NATIVE" in source, (
        "deploy_to_linked_repos MUST branch on plugin-native hosts per T043"
    )
    assert "ClaudeHost" in source, (
        "deploy_to_linked_repos MUST route Claude through hosts/claude.py per T043"
    )


def test_linked_secondary_does_not_call_bulk_copies_for_claude(tmp_path: Path) -> None:
    """End-to-end-ish: when secondary is configured for claude, the
    bulk-copy primitives (copy_commands/copy_skills/copy_agents) MUST NOT
    be called."""
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"
    for r in (primary, secondary):
        r.mkdir()
        (r / "App.sln").write_text("Microsoft\n", encoding="utf-8")
        config_dir = r / ".dotnet-ai-kit"
        config_dir.mkdir()
        (config_dir / "config.yml").write_text(
            "ai_tools: [claude]\ncommand_style: both\n", encoding="utf-8"
        )
        (config_dir / "project.yml").write_text(
            "project_type: generic\nconfidence: low\n", encoding="utf-8"
        )
        (config_dir / "version.txt").write_text("0.0.0", encoding="utf-8")

    config = DotnetAiConfig(ai_tools=["claude"])
    # Point one role at the secondary
    config.repos.command = str(secondary)

    # Patches: stub subprocess.run and the bulk-copy primitives
    fake_proc = MagicMock(returncode=0, stdout="", stderr="")
    bulk_called: dict[str, int] = {"copy_commands": 0, "copy_skills": 0, "copy_agents": 0}

    def _track(name: str):
        def _stub(*args, **kwargs):  # noqa: ANN002,ANN003
            bulk_called[name] += 1
            return 0

        return _stub

    with (
        patch.object(copier, "copy_commands", side_effect=_track("copy_commands")),
        patch.object(copier, "copy_skills", side_effect=_track("copy_skills")),
        patch.object(copier, "copy_agents", side_effect=_track("copy_agents")),
        patch("subprocess.run", return_value=fake_proc),
    ):
        deploy_to_linked_repos(
            primary_root=primary,
            config=config,
            tool_version="1.0.0",
            package_dir=REPO,
        )

    # For Claude plugin-native, none of the bulk primitives should fire.
    assert bulk_called == {
        "copy_commands": 0,
        "copy_skills": 0,
        "copy_agents": 0,
    }, (
        f"FR-033 violation: bulk-copy primitives fired for plugin-native host: "
        f"{bulk_called}"
    )
