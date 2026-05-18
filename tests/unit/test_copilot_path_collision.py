"""T072a — Copilot path collision protection per contract:33-41.

Asserts:
(a) Pre-existing `.github/copilot-instructions.md` (not in manifest) → init
    with copilot detects it, preserves it, emits a corrective error
    naming the file + the --force-render invocation, exits non-zero.
(b) Same default-preserve for `.github/instructions/<name>.instructions.md`
    and `.github/agents/<name>.agent.md`.
(c) FR-008 / A-008 binding: paths are unmanaged until explicit user opt-in.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app
from dotnet_ai_kit.hosts.copilot import CopilotHost

runner = CliRunner()


def _create_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("Microsoft\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_init_copilot_preserves_existing_copilot_instructions(tmp_path: Path) -> None:
    """(a) Pre-existing .github/copilot-instructions.md MUST be preserved."""
    _create_project(tmp_path)
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    existing = github_dir / "copilot-instructions.md"
    existing.write_text("USER WROTE THIS\n", encoding="utf-8")

    result = runner.invoke(app, ["init", str(tmp_path), "--ai", "copilot"], catch_exceptions=False)

    # init exits non-zero per FR-008 when unresolved conflicts exist
    assert result.exit_code != 0
    # File preserved
    assert existing.read_text(encoding="utf-8") == "USER WROTE THIS\n"
    # Error mentions --force-render
    assert "--force-render" in result.output


def test_render_preserves_instructions_path_files(tmp_path: Path) -> None:
    """(b) Pre-existing .github/instructions/<x>.instructions.md preserved."""
    _create_project(tmp_path)
    cfg_dir = tmp_path / ".dotnet-ai-kit"
    cfg_dir.mkdir()
    (cfg_dir / "project.yml").write_text(
        "company: A\ndomain: B\nside: C\nproject_type: api\n"
        "dotnet_version: '9.0'\n"
        "detected_paths:\n"
        "  testing: 'tests/**'\n",
        encoding="utf-8",
    )
    inst_dir = tmp_path / ".github" / "instructions"
    inst_dir.mkdir(parents=True)
    existing = inst_dir / "testing.instructions.md"
    existing.write_text("USER TESTING NOTES\n", encoding="utf-8")

    host = CopilotHost()
    result = host.render(tmp_path)

    assert any(p.name == "testing.instructions.md" for p in result.pending_user_consent)
    assert existing.read_text(encoding="utf-8") == "USER TESTING NOTES\n"


def test_render_preserves_agent_files(tmp_path: Path) -> None:
    """(b) Pre-existing .github/agents/<x>.agent.md preserved."""
    _create_project(tmp_path)
    agents_dir = tmp_path / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    existing = agents_dir / "dotnet-ai-architect.agent.md"
    existing.write_text("USER AGENT BODY\n", encoding="utf-8")

    host = CopilotHost()
    result = host.render(tmp_path)

    assert any(p.name == "dotnet-ai-architect.agent.md" for p in result.pending_user_consent)
    assert existing.read_text(encoding="utf-8") == "USER AGENT BODY\n"


def test_fr008_a008_unmanaged_until_consent(tmp_path: Path) -> None:
    """(c) FR-008 / A-008: paths are unmanaged until explicit user opt-in.

    Verified by inspecting CopilotRenderResult: pending_user_consent vs
    force_rendered partition the consent state.
    """
    _create_project(tmp_path)
    existing = tmp_path / ".github" / "copilot-instructions.md"
    existing.parent.mkdir()
    existing.write_text("USER\n", encoding="utf-8")

    host = CopilotHost()
    # WITHOUT consent → pending
    result_no_consent = host.render(tmp_path)
    assert existing in result_no_consent.pending_user_consent
    assert existing not in result_no_consent.force_rendered
    assert existing not in result_no_consent.written

    # WITH consent → force_rendered
    result_with_consent = host.render(tmp_path, force_render_paths=[existing])
    assert existing in result_with_consent.force_rendered
    assert existing not in result_with_consent.pending_user_consent
