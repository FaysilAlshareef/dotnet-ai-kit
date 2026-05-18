"""T036 — SC-005: Claude Code's listing surface shows exactly one entry
per logical command/skill (no duplicate from project copies).

Per SC-005: in plugin-native mode, the user should NEVER see a command
listed twice — once from the plugin install path and once from a
per-solution `.claude/commands/` copy. This is a regression-prevention
test ensuring init does NOT create the per-solution duplicates.

Verified structurally: after init, `.claude/commands/` MUST be empty (or
absent). Combined with the plugin install path serving every command,
this guarantees a one-entry-per-command listing.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text(
        "Microsoft Visual Studio Solution File\n", encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_no_per_solution_command_duplicates(tmp_path: Path) -> None:
    """SC-005: post-init `.claude/commands/` MUST be empty/absent (commands
    served by plugin install, not duplicated per-solution)."""
    _create_dotnet_project(tmp_path)
    result = runner.invoke(
        app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False
    )
    assert result.exit_code == 0
    commands_dir = tmp_path / ".claude" / "commands"
    if commands_dir.is_dir():
        files = [p.name for p in commands_dir.iterdir() if p.is_file()]
        assert not files, (
            f"SC-005 violation: per-solution `.claude/commands/` has "
            f"{len(files)} duplicate command file(s): {files[:5]}"
        )


def test_no_per_solution_skill_duplicates(tmp_path: Path) -> None:
    """SC-005 corollary: post-init `.claude/skills/` MUST be empty/absent."""
    _create_dotnet_project(tmp_path)
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"])
    skills_dir = tmp_path / ".claude" / "skills"
    if skills_dir.is_dir():
        skills = list(skills_dir.rglob("SKILL.md"))
        assert not skills, (
            f"SC-005 violation: per-solution `.claude/skills/` has "
            f"{len(skills)} duplicate skill(s)"
        )


def test_no_per_solution_agent_duplicates(tmp_path: Path) -> None:
    """SC-005 corollary: post-init `.claude/agents/` MUST be empty/absent."""
    _create_dotnet_project(tmp_path)
    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude"])
    agents_dir = tmp_path / ".claude" / "agents"
    if agents_dir.is_dir():
        agents = [p.name for p in agents_dir.iterdir() if p.is_file()]
        assert not agents, (
            f"SC-005 violation: per-solution `.claude/agents/` has "
            f"{len(agents)} duplicate agent(s): {agents[:5]}"
        )
