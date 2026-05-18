"""T067 — FR-015 + FR-024: `dotnet-ai upgrade` separation rules.

Per FR-015 (upgrade is no-op for plugin hosts) + FR-024 (upgrade --copilot
re-renders Copilot only; migrate does NOT touch Copilot):

1. `dotnet-ai upgrade` MUST NOT re-render Copilot files.
2. `dotnet-ai upgrade --copilot` MUST re-render Copilot files only (NOT
   bulk-copy Claude/Codex/Cursor).
3. `dotnet-ai migrate` MUST NOT re-render Copilot files (it only operates
   on the manifest's existing managed entries).
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _setup_project_with_copilot(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("Microsoft\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>",
        encoding="utf-8",
    )
    # Pre-init: write config so upgrade has something to read
    cfg = tmp_path / ".dotnet-ai-kit"
    cfg.mkdir()
    (cfg / "config.yml").write_text(
        "ai_tools: [claude, copilot]\npermissions_level: minimal\n",
        encoding="utf-8",
    )
    (cfg / "version.txt").write_text("0.0.1", encoding="utf-8")


def test_upgrade_without_copilot_flag_does_not_re_render_copilot(
    tmp_path: Path, monkeypatch
) -> None:
    """FR-024 / T067: plain `upgrade` MUST NOT touch Copilot files."""
    _setup_project_with_copilot(tmp_path)
    # Pre-create a copilot-instructions.md to test it's NOT modified
    github = tmp_path / ".github"
    github.mkdir()
    instructions = github / "copilot-instructions.md"
    instructions.write_text("PRE-UPGRADE CONTENT\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["upgrade"], catch_exceptions=False)

    # File MUST be unchanged
    assert instructions.read_text(encoding="utf-8") == "PRE-UPGRADE CONTENT\n", (
        "FR-024 violation: plain `upgrade` modified .github/copilot-instructions.md"
    )


def test_upgrade_copilot_does_not_touch_claude_files(tmp_path: Path, monkeypatch) -> None:
    """FR-015 / T067: `upgrade --copilot` MUST NOT bulk-copy to .claude/."""
    _setup_project_with_copilot(tmp_path)
    # Pre-create a marker in .claude/ that would be overwritten if bulk-copy fired
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    marker = claude_dir / "commands"
    marker.mkdir()
    sentinel = marker / "user-wrote-this.md"
    sentinel.write_text("USER FILE\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["upgrade", "--copilot"], catch_exceptions=False)

    # Sentinel survives — upgrade --copilot did NOT bulk-copy Claude commands
    assert sentinel.is_file()
    assert sentinel.read_text(encoding="utf-8") == "USER FILE\n", (
        "FR-015 violation: upgrade --copilot bulk-copied into .claude/"
    )


def test_upgrade_copilot_renders_copilot_files(tmp_path: Path, monkeypatch) -> None:
    """FR-024 / T067: `upgrade --copilot` re-renders Copilot files."""
    _setup_project_with_copilot(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["upgrade", "--copilot"], catch_exceptions=False)

    # The render command should succeed and create the instructions file
    # (no pre-existing file to preserve)
    assert result.exit_code == 0
    assert (tmp_path / ".github" / "copilot-instructions.md").is_file()
