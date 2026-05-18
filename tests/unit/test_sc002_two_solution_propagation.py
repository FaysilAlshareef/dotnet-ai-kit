"""T035 — SC-002: two solutions sharing one plugin install see updated
behavior after a single host-side update.

Per SC-002: in a plugin-native architecture, when the user updates the
plugin (e.g., `claude /plugin update dotnet-ai-kit`), ALL solutions that
share that plugin install observe the update WITHOUT needing per-solution
`dotnet-ai upgrade` runs.

This is structurally equivalent to: the plugin install path is the
single source of truth for commands/skills/agents. Per-solution writes
contain only metadata (`.dotnet-ai-kit/`) and permissions (`.claude/
settings.json`).
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _create_dotnet_project(tmp_path: Path, name: str = "MyApp") -> Path:
    sol = tmp_path / name
    sol.mkdir()
    (sol / f"{name}.sln").write_text(
        "Microsoft Visual Studio Solution File\n", encoding="utf-8"
    )
    (sol / "src").mkdir()
    (sol / "src" / f"{name}.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )
    return sol


def test_two_solutions_have_no_per_solution_command_copies(tmp_path: Path) -> None:
    """SC-002: in plugin-native mode, two solutions both init claude → neither
    has per-solution commands. The plugin install path serves both."""
    sol_a = _create_dotnet_project(tmp_path, "AppA")
    sol_b = _create_dotnet_project(tmp_path, "AppB")

    rc_a = runner.invoke(app, ["init", str(sol_a), "--ai", "claude"]).exit_code
    rc_b = runner.invoke(app, ["init", str(sol_b), "--ai", "claude"]).exit_code

    assert rc_a == 0 and rc_b == 0

    for sol in (sol_a, sol_b):
        commands_dir = sol / ".claude" / "commands"
        skills_dir = sol / ".claude" / "skills"
        agents_dir = sol / ".claude" / "agents"
        # Plugin-native: NONE of these contain bulk-copied content
        for d in (commands_dir, skills_dir, agents_dir):
            if d.is_dir():
                contents = list(d.iterdir())
                assert not contents, (
                    f"SC-002 violation: per-solution {d} contains "
                    f"{[p.name for p in contents]}; plugin install should serve these."
                )


def test_two_solutions_have_independent_metadata(tmp_path: Path) -> None:
    """Cross-check: per-solution METADATA (project.yml, config.yml) is per-solution,
    NOT shared. This is the inverse of SC-002 — solutions can have different
    project metadata while sharing the same plugin commands."""
    sol_a = _create_dotnet_project(tmp_path, "AppA")
    sol_b = _create_dotnet_project(tmp_path, "AppB")

    runner.invoke(app, ["init", str(sol_a), "--ai", "claude"])
    runner.invoke(app, ["init", str(sol_b), "--ai", "claude"])

    config_a = sol_a / ".dotnet-ai-kit" / "config.yml"
    config_b = sol_b / ".dotnet-ai-kit" / "config.yml"
    assert config_a.is_file()
    assert config_b.is_file()
    # The files are independent — editing one does NOT affect the other
    config_a.write_text("ai_tools: [claude]\nfoo: A\n", encoding="utf-8")
    config_b.write_text("ai_tools: [claude]\nfoo: B\n", encoding="utf-8")
    assert "foo: A" in config_a.read_text(encoding="utf-8")
    assert "foo: B" in config_b.read_text(encoding="utf-8")
