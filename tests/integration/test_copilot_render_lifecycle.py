"""T066 — Copilot render lifecycle integration test.

Per CHK016, CHK017, CHK018, FR-004:

  init → render → edit metadata → upgrade --copilot → files reflect new metadata

Asserts the metadata embedded in the rendered Copilot files updates when
project.yml changes (after an explicit upgrade --copilot).
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _setup_project_with_metadata(tmp_path: Path, company: str) -> None:
    (tmp_path / "MyApp.sln").write_text("Microsoft\n", encoding="utf-8")
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>",
        encoding="utf-8",
    )
    cfg = tmp_path / ".dotnet-ai-kit"
    cfg.mkdir(exist_ok=True)
    (cfg / "project.yml").write_text(
        f"company: {company}\ndomain: Order\nside: Command\n"
        "project_type: api\ndotnet_version: '9.0'\n"
        "detected_paths: {}\n",
        encoding="utf-8",
    )


def test_init_render_edit_upgrade_lifecycle(tmp_path: Path, monkeypatch) -> None:
    """The end-to-end lifecycle: rendered file reflects current project.yml."""
    # Step 1: bare project (NO pre-existing .dotnet-ai-kit/) so init is clean
    (tmp_path / "MyApp.sln").write_text("Microsoft\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    # Run init with copilot — creates .dotnet-ai-kit/ but project.yml is empty
    rc = runner.invoke(app, ["init", str(tmp_path), "--ai", "copilot"]).exit_code
    assert rc == 0

    instructions = tmp_path / ".github" / "copilot-instructions.md"
    assert instructions.is_file()

    # Step 2: edit project.yml metadata (set company=Acme)
    _setup_project_with_metadata(tmp_path, "Acme")

    # Step 3: upgrade --copilot --force-render to pick up the new metadata
    rc = runner.invoke(
        app,
        ["upgrade", "--copilot", "--force-render", ".github/copilot-instructions.md"],
    ).exit_code
    assert rc == 0
    body_after_acme = instructions.read_text(encoding="utf-8")
    assert "Acme" in body_after_acme

    # Step 4: edit project.yml metadata (change to Globex)
    _setup_project_with_metadata(tmp_path, "Globex")

    rc = runner.invoke(
        app,
        ["upgrade", "--copilot", "--force-render", ".github/copilot-instructions.md"],
    ).exit_code
    assert rc == 0
    body_after_globex = instructions.read_text(encoding="utf-8")
    assert "Globex" in body_after_globex
    assert "Acme" not in body_after_globex, (
        "FR-024 violation: upgrade --copilot did not re-render with new metadata"
    )
