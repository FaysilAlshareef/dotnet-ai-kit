"""T094 — `dotnet-ai init --force` prints migrate invocation on old-layout solutions.

Per FR-025 / CHK025: when `--force` lands on a solution that has legacy
pre-019 paths (e.g., `.claude/commands/` from feature 018), init MUST:
1. Detect the shadowed legacy artifacts
2. NOT auto-delete them
3. Print the exact `dotnet-ai migrate <path>` invocation
4. Exit non-zero so CI doesn't proceed silently
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import LEGACY_MANAGED_PATHS, _detect_shadowed_legacy_paths, app

runner = CliRunner()


def _create_dotnet_project_with_legacy(tmp_path: Path) -> None:
    """Create a project that already has pre-019 layout artifacts."""
    (tmp_path / "MyApp.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )
    # Existing legacy commands dir (simulating feature-018-era init output)
    legacy_cmds = tmp_path / ".claude" / "commands"
    legacy_cmds.mkdir(parents=True)
    (legacy_cmds / "dotnet-ai.foo.md").write_text("# Legacy command body\n", encoding="utf-8")
    # Also a pre-existing .dotnet-ai-kit/ so --force is required
    (tmp_path / ".dotnet-ai-kit").mkdir()
    (tmp_path / ".dotnet-ai-kit" / "config.yml").write_text(
        "ai_tools: [claude]\n", encoding="utf-8"
    )


def test_detect_shadowed_legacy_paths_finds_existing_dirs(tmp_path: Path) -> None:
    """Unit test of the helper: it returns the legacy paths that exist."""
    _create_dotnet_project_with_legacy(tmp_path)
    found = _detect_shadowed_legacy_paths(tmp_path)
    assert any(".claude/commands" in str(p).replace("\\", "/") for p in found), (
        f"helper missed `.claude/commands` in legacy layout: {found}"
    )


def test_detect_shadowed_legacy_paths_clean_solution(tmp_path: Path) -> None:
    """No legacy paths present → helper returns empty list."""
    (tmp_path / "MyApp.sln").write_text("Microsoft\n", encoding="utf-8")
    found = _detect_shadowed_legacy_paths(tmp_path)
    assert found == []


def test_init_force_refuses_and_prints_migrate(tmp_path: Path) -> None:
    """E2E: init --force MUST refuse and print migrate command on old-layout."""
    _create_dotnet_project_with_legacy(tmp_path)
    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude", "--force"],
        catch_exceptions=False,
    )
    assert result.exit_code != 0, "init --force on old-layout MUST exit non-zero per FR-025"
    # The exact migrate invocation MUST appear in output
    assert "dotnet-ai migrate" in result.output, (
        f"init --force MUST print the migrate invocation per FR-025; got output: {result.output!r}"
    )


def test_init_force_does_not_auto_delete_legacy(tmp_path: Path) -> None:
    """init --force MUST preserve the legacy files (no auto-deletion)."""
    _create_dotnet_project_with_legacy(tmp_path)
    legacy_file = tmp_path / ".claude" / "commands" / "dotnet-ai.foo.md"
    assert legacy_file.is_file()

    runner.invoke(app, ["init", str(tmp_path), "--ai", "claude", "--force"])

    # File MUST still exist — no auto-deletion per FR-025
    assert legacy_file.is_file(), (
        "FR-025 violation: init --force deleted legacy artifact instead of "
        "preserving and instructing user to run migrate"
    )


def test_legacy_managed_paths_list_includes_critical_dirs() -> None:
    """Constants check: the legacy-path list MUST include the pre-019
    feature-018 managed directories."""
    expected = {
        ".claude/commands",
        ".claude/rules",
        ".claude/skills",
        ".claude/agents",
    }
    actual = set(LEGACY_MANAGED_PATHS)
    missing = expected - actual
    assert not missing, f"LEGACY_MANAGED_PATHS missing critical dirs: {missing}"
