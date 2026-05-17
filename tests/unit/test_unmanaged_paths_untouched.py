"""T045 — root AGENTS.md is NEVER written/modified/deleted (FR-008 / A-008).

Per spec A-008 (extended in spec-phase round 1): paths outside the formally
managed manifest MUST NOT be touched by any tool command. The repository-
root `AGENTS.md` is the canonical concrete example.

Feature 019 / commit 5 / T045: with `copy_commands_codex` deleted (T049)
and the `AGENT_CONFIG["codex"]["agents_file"] = "AGENTS.md"` mapping
removed (T048), no code path should produce root AGENTS.md.

This test exercises every write command and asserts root AGENTS.md is
untouched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text(
        "Microsoft Visual Studio Solution File\n", encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        "<Project Sdk=\"Microsoft.NET.Sdk\"><PropertyGroup>"
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_init_does_not_create_root_agents_md(tmp_path: Path) -> None:
    """`dotnet-ai init` MUST NOT write `AGENTS.md` at the project root."""
    _create_dotnet_project(tmp_path)

    runner.invoke(
        app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False
    )

    agents_md = tmp_path / "AGENTS.md"
    assert not agents_md.exists(), (
        f"FR-008 / A-008 violation: init created root AGENTS.md "
        f"({agents_md.read_text(encoding='utf-8')!r})"
    )


def test_init_codex_does_not_create_root_agents_md(tmp_path: Path) -> None:
    """`dotnet-ai init --ai codex` MUST NOT write root AGENTS.md (T049 binding)."""
    _create_dotnet_project(tmp_path)

    # Codex pre-existing AGENTS.md (the user's own, not tool-managed)
    pre_existing = tmp_path / "AGENTS.md"
    pre_existing.write_text("# User-authored AGENTS.md\n", encoding="utf-8")
    original_content = pre_existing.read_text(encoding="utf-8")

    runner.invoke(
        app, ["init", str(tmp_path), "--ai", "codex"], catch_exceptions=False
    )

    # The pre-existing file MUST be preserved verbatim
    assert pre_existing.read_text(encoding="utf-8") == original_content, (
        "FR-008 / A-008 violation: init modified user's root AGENTS.md "
        "(this path is OUTSIDE the formally managed manifest per A-008)"
    )


def test_upgrade_does_not_create_root_agents_md(tmp_path: Path) -> None:
    """`dotnet-ai upgrade` MUST NOT write root AGENTS.md."""
    _create_dotnet_project(tmp_path)
    runner.invoke(
        app, ["init", str(tmp_path), "--ai", "claude"], catch_exceptions=False
    )

    # Ensure no AGENTS.md after init
    agents_md = tmp_path / "AGENTS.md"
    assert not agents_md.exists()

    runner.invoke(app, ["upgrade", str(tmp_path)], catch_exceptions=False)
    assert not agents_md.exists(), "upgrade created root AGENTS.md"


def test_copy_commands_codex_function_removed() -> None:
    """T049: `copy_commands_codex` MUST be removed from copier.py."""
    from dotnet_ai_kit import copier
    assert not hasattr(copier, "copy_commands_codex"), (
        "copy_commands_codex still present in copier — T049 incomplete"
    )


def test_agent_config_codex_has_no_agents_file_mapping() -> None:
    """T048: `AGENT_CONFIG['codex']['agents_file'] = 'AGENTS.md'` MUST be removed."""
    from dotnet_ai_kit.agents import AGENT_CONFIG
    codex_cfg = AGENT_CONFIG.get("codex", {})
    assert "agents_file" not in codex_cfg, (
        f"AGENT_CONFIG['codex'] still has `agents_file`: {codex_cfg.get('agents_file')!r} "
        f"— T048 incomplete (root AGENTS.md emitter still wired up)"
    )
