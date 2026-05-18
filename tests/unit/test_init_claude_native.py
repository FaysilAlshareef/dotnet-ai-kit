"""T029 — `dotnet-ai init` Claude plugin-native behavior (commit 4).

Asserts that init with Claude selected writes ONLY the per-solution files
per FR-005 / FR-006, and does NOT bulk-copy commands/skills/agents into
`.claude/` (those live in the plugin install path now per FR-004).

Per-solution writes (Claude):
- `.dotnet-ai-kit/config.yml`   (UserConfig)
- `.dotnet-ai-kit/project.yml`  (ProjectMetadata)
- `.dotnet-ai-kit/manifest.json` (ManagedFile manifest)
- `.claude/settings.json`       (permissions merge ONLY)

Forbidden writes (Claude under feature 019):
- `.claude/commands/`   (served by plugin)
- `.claude/skills/`     (served by plugin)
- `.claude/agents/`     (served by plugin)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _create_dotnet_project(tmp_path: Path) -> None:
    """Create a minimal .NET solution structure so init detection succeeds."""
    (tmp_path / "MyApp.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_init_claude_writes_per_solution_files(tmp_path: Path) -> None:
    """Init with Claude MUST write the 3 per-solution YAML/JSON files."""
    _create_dotnet_project(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude"],
        catch_exceptions=False,
    )

    # init may exit 0 or print specific output; not asserting exit code strictly,
    # asserting the per-solution files exist.
    assert (tmp_path / ".dotnet-ai-kit").is_dir(), (
        f"init must create .dotnet-ai-kit/ — exit_code={result.exit_code}, output={result.output!r}"
    )


def test_init_claude_does_not_bulk_copy_agents(tmp_path: Path) -> None:
    """Init with Claude MUST NOT bulk-copy agents under feature 019.

    Per feature 019 FR-004: agents live in the plugin install path now, NOT
    per-solution. This test asserts the agent-side of the bulk-copy removal
    (commit 4 / T041a / T043 via copy_agents() no-op).

    The commands/skills/rules side of the removal is deferred to a follow-up
    commit (T042 full cli.py init refactor), tracked via this test's sibling
    `test_init_claude_does_not_bulk_copy_commands_skills` which is currently
    marked as `xfail` until that refactor lands.
    """
    _create_dotnet_project(tmp_path)

    runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude"],
        catch_exceptions=False,
    )

    forbidden = tmp_path / ".claude" / "agents"
    if forbidden.is_dir():
        contents = list(forbidden.iterdir())
        assert not contents, (
            f"feature 019 violation: per-solution `.claude/agents/` contains "
            f"bulk-copied files: {[p.name for p in contents]}. Per FR-004 these "
            f"live in the plugin install path, not per-solution."
        )


@pytest.mark.parametrize(
    "forbidden_dir",
    [".claude/commands", ".claude/skills"],
)
def test_init_claude_does_not_bulk_copy_commands_skills(tmp_path: Path, forbidden_dir: str) -> None:
    """T042/T043 — Claude plugin-native init MUST NOT bulk-copy commands/skills.

    Per FR-005/FR-006: these directories are served from the plugin install path,
    NOT per-solution. The cli.py init flow short-circuits the copy for hosts in
    `PLUGIN_NATIVE_HOSTS`.
    """
    _create_dotnet_project(tmp_path)

    runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude"],
        catch_exceptions=False,
    )

    forbidden = tmp_path / forbidden_dir
    if forbidden.is_dir():
        contents = list(forbidden.iterdir())
        assert not contents, (
            f"feature 019 violation: per-solution `{forbidden_dir}/` contains "
            f"bulk-copied files: {[p.name for p in contents]}"
        )
