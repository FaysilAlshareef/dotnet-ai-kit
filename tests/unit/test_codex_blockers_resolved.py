"""Codex implement-phase round-1 blockers — verification suite.

Maps each of the 6 BLOCK-WITH-CONCERNS items from
`specs/019-plugin-native-arch/discussion/implement-phase/round1-codex-reply.md`
to a passing test that demonstrates the fix.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app
from dotnet_ai_kit.manifest import read_manifest

runner = CliRunner()


def _create_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("Microsoft\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>",
        encoding="utf-8",
    )


# ----------------------------------------------------------------------
# Blocker 1: init --ai codex MUST NOT write .claude/settings.json
# ----------------------------------------------------------------------


def test_blocker1_init_codex_does_not_write_claude_settings(tmp_path: Path) -> None:
    """Per spec.md:171: init writes files only for selected hosts."""
    _create_project(tmp_path)
    result = runner.invoke(app, ["init", str(tmp_path), "--ai", "codex"], catch_exceptions=False)
    assert result.exit_code == 0
    assert not (tmp_path / ".claude" / "settings.json").exists(), (
        "Blocker-1 regression: `init --ai codex` MUST NOT create .claude/settings.json"
    )


# ----------------------------------------------------------------------
# Blocker 2: Copilot init MUST NOT bulk-copy legacy command-agent files
# ----------------------------------------------------------------------


def test_blocker2_copilot_init_does_not_bulk_copy_command_agents(tmp_path: Path) -> None:
    """Per FR-007 (spec.md:155): Copilot init renders 3 file classes only."""
    _create_project(tmp_path)
    result = runner.invoke(app, ["init", str(tmp_path), "--ai", "copilot"], catch_exceptions=False)
    assert result.exit_code == 0
    # The legacy AGENT_CONFIG['copilot']['commands_dir'] is .github/agents/commands
    # which MUST NOT be created under feature 019.
    assert not (tmp_path / ".github" / "agents" / "commands").exists(), (
        "Blocker-2 regression: Copilot init wrote legacy .github/agents/commands/ files"
    )


# ----------------------------------------------------------------------
# Blocker 3: Copilot repo-wide render inlines convention rule bodies
# ----------------------------------------------------------------------


def test_blocker3_copilot_instructions_inlines_convention_rules(tmp_path: Path) -> None:
    """Per copilot-instructions.contract.md:13-17: convention rule BODIES inlined."""
    _create_project(tmp_path)
    runner.invoke(app, ["init", str(tmp_path), "--ai", "copilot"])
    body = (tmp_path / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")

    # All 5 universal rule names MUST be referenced
    for rule in (
        "async-concurrency",
        "coding-style",
        "existing-projects",
        "security",
        "tool-calls",
    ):
        assert rule in body, f"Blocker-3 regression: copilot-instructions.md missing rule '{rule}'"
    # Placeholder phrase MUST NOT appear
    assert "Convention rule bodies will be inlined here in the full render" not in body, (
        "Blocker-3 regression: copilot-instructions.md still has placeholder text"
    )


# ----------------------------------------------------------------------
# Blocker 4: upgrade --copilot refreshes managed renders without --force-render
# ----------------------------------------------------------------------


def test_blocker4_upgrade_copilot_refreshes_managed_renders(tmp_path: Path, monkeypatch) -> None:
    """Per FR-015 (spec.md:172): `upgrade --copilot` re-renders using current
    plugin source + project metadata. MUST NOT require --force-render for
    its own managed files."""
    _create_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    # Initial init
    rc = runner.invoke(app, ["init", str(tmp_path), "--ai", "copilot"]).exit_code
    assert rc == 0

    # Edit project.yml metadata so re-render produces different content
    (tmp_path / ".dotnet-ai-kit" / "project.yml").write_text(
        "company: NewCompany\ndomain: NewDomain\nside: server\n"
        "project_type: api\ndotnet_version: '9.0'\ndetected_paths: {}\n",
        encoding="utf-8",
    )

    # upgrade --copilot without --force-render MUST succeed (exit 0)
    result = runner.invoke(app, ["upgrade", "--copilot", "--json"], catch_exceptions=False)
    assert result.exit_code == 0, (
        f"Blocker-4 regression: upgrade --copilot exit_code={result.exit_code} "
        f"(expected 0). Output: {result.output[:500]}"
    )

    # The rendered file MUST reflect the new metadata
    body = (tmp_path / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert "NewCompany" in body, (
        "Blocker-4 regression: upgrade --copilot did not pick up new project.yml metadata"
    )


# ----------------------------------------------------------------------
# Blocker 5: manifest tracks .github/instructions/ and .github/agents/
# ----------------------------------------------------------------------


def test_blocker5_manifest_includes_copilot_path_scoped_and_agents(tmp_path: Path) -> None:
    """Per SC-006 + copilot-instructions.contract.md:21-27: all Copilot
    renders MUST be recorded in manifest.json with host_owner='copilot'."""
    _create_project(tmp_path)
    # Set up detected_paths so path-scoped renders happen
    cfg = tmp_path / ".dotnet-ai-kit"
    cfg.mkdir(exist_ok=True)
    (cfg / "project.yml").write_text(
        "company: A\ndomain: B\nside: C\nproject_type: api\n"
        "dotnet_version: '9.0'\ndetected_paths:\n  testing: 'tests/**'\n",
        encoding="utf-8",
    )

    rc = runner.invoke(app, ["init", str(tmp_path), "--ai", "copilot", "--force"]).exit_code
    # init may exit 1 if .dotnet-ai-kit exists without --force; we created it
    assert rc == 0, f"init failed: rc={rc}"

    manifest = read_manifest(tmp_path)
    assert manifest is not None
    copilot_paths = {
        f.path.replace("\\", "/")
        for f in manifest.files
        if (f.host_owner or "").lower() == "copilot"
    }

    # Repo-wide instructions MUST be tracked
    assert ".github/copilot-instructions.md" in copilot_paths, (
        f"Blocker-5 regression: copilot-instructions.md missing from manifest. Got: {copilot_paths}"
    )

    # Path-scoped instructions for `testing` MUST be tracked
    assert ".github/instructions/testing.instructions.md" in copilot_paths, (
        f"Blocker-5 regression: path-scoped instructions missing from manifest. "
        f"Got: {copilot_paths}"
    )

    # Per-agent files MUST be tracked (at least dotnet-ai-architect)
    agent_paths = [p for p in copilot_paths if "/agents/" in p and p.endswith(".agent.md")]
    assert agent_paths, (
        f"Blocker-5 regression: no .github/agents/*.agent.md tracked in manifest. "
        f"Got: {copilot_paths}"
    )


def test_blocker5_check_detects_stale_copilot_renders(tmp_path: Path) -> None:
    """Per SC-006: `dotnet-ai check --host copilot` MUST detect stale renders.

    Exit code is either 14 (manifest_integrity — covers hash mismatch) OR 15
    (copilot_freshness — direct stale-render signal). Either is correct
    detection; the test just asserts NON-ZERO and that copilot_freshness
    reports the stale file when reached.
    """
    _create_project(tmp_path)
    runner.invoke(app, ["init", str(tmp_path), "--ai", "copilot"])

    # Now mutate one rendered file to make it stale
    inst = tmp_path / ".github" / "copilot-instructions.md"
    inst.write_text("USER EDIT\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["check", str(tmp_path), "--host", "copilot", "--json"],
        catch_exceptions=False,
    )
    # Per check-cli.contract.md:31-36, multiple failures use the LOWEST exit
    # code — manifest_integrity (14) precedes copilot_freshness (15), so a
    # stale render that's also recorded in manifest must surface as 14.
    assert result.exit_code == 14, (
        f"Blocker-5 regression: check did NOT detect stale render with the "
        f"contract-mandated lowest exit code (14). "
        f"exit_code={result.exit_code}, output={result.output[:500]}"
    )
    # And the response payload MUST include either:
    # - manifest_integrity fail (stale file shows up in hash mismatch listing), OR
    # - copilot_freshness fail (direct staleness reporting)
    body = result.output
    assert "copilot-instructions.md" in body and (
        "fail" in body.lower() or '"exit_code": 14' in body or '"exit_code": 15' in body
    ), (
        f"Blocker-5 regression: stale file not surfaced in check output. "
        f"output={result.output[:500]}"
    )


# ----------------------------------------------------------------------
# Sibling Blocker 1' (Codex round 2): plain `upgrade` for Copilot
# ----------------------------------------------------------------------


def test_sibling_blocker_upgrade_copilot_only_does_not_bulk_copy(
    tmp_path: Path, monkeypatch
) -> None:
    """Per FR-015 (spec.md:172): plain `upgrade` is no-op for plugin-native
    AND render-only hosts. `dotnet-ai upgrade` on a `ai_tools: [copilot]`
    solution MUST NOT bulk-copy legacy `.github/agents/commands/` or write
    `.claude/settings.json`."""
    _create_project(tmp_path)
    cfg = tmp_path / ".dotnet-ai-kit"
    cfg.mkdir(exist_ok=True)
    (cfg / "config.yml").write_text(
        "ai_tools: [copilot]\npermissions_level: minimal\n",
        encoding="utf-8",
    )
    (cfg / "version.txt").write_text("0.0.1", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["upgrade", "--json"], catch_exceptions=False)
    assert result.exit_code == 0, result.output

    assert not (tmp_path / ".github" / "agents" / "commands").exists(), (
        "Sibling Blocker 1' regression: plain upgrade wrote legacy "
        ".github/agents/commands/ for Copilot-only solution"
    )
    assert not (tmp_path / ".claude" / "settings.json").exists(), (
        "Sibling Blocker 1' regression: plain upgrade wrote .claude/settings.json "
        "on a Copilot-only solution (Claude not in ai_tools)"
    )


# ----------------------------------------------------------------------
# Sibling Blocker 2' (Codex round 2): `configure --tools copilot`
# ----------------------------------------------------------------------


def test_sibling_blocker_configure_copilot_only_does_not_bulk_copy(
    tmp_path: Path, monkeypatch
) -> None:
    """Per FR-016 (spec.md:171): configure writes files only for selected hosts."""
    _create_project(tmp_path)
    cfg = tmp_path / ".dotnet-ai-kit"
    cfg.mkdir(exist_ok=True)
    # Pre-init the .dotnet-ai-kit/ so configure has something to read
    (cfg / "config.yml").write_text("ai_tools: [copilot]\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "configure",
            "--no-input",
            "--company",
            "Acme",
            "--tools",
            "copilot",
            "--permissions",
            "minimal",
            "--json",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    assert not (tmp_path / ".github" / "agents" / "commands").exists(), (
        "Sibling Blocker 2' regression: configure --tools copilot wrote legacy "
        ".github/agents/commands/"
    )
    assert not (tmp_path / ".claude" / "settings.json").exists(), (
        "Sibling Blocker 2' regression: configure --tools copilot wrote .claude/settings.json"
    )


# ----------------------------------------------------------------------
# Blocker 6: linked-secondary Copilot deploy calls CopilotHost.render()
# ----------------------------------------------------------------------


def test_blocker6_linked_secondary_copilot_uses_render(tmp_path: Path) -> None:
    """Per FR-033 (spec.md:205): linked-secondary deploy follows the same
    plugin-native footprint, including Copilot render."""
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"
    for r in (primary, secondary):
        r.mkdir()
        (r / "App.sln").write_text("Microsoft\n", encoding="utf-8")
        cfg = r / ".dotnet-ai-kit"
        cfg.mkdir()
        (cfg / "config.yml").write_text(
            "ai_tools: [copilot]\ncommand_style: both\n", encoding="utf-8"
        )
        (cfg / "project.yml").write_text(
            "project_type: generic\nconfidence: low\ndetected_paths: {}\n",
            encoding="utf-8",
        )
        (cfg / "version.txt").write_text("0.0.0", encoding="utf-8")

    from unittest.mock import MagicMock, patch  # noqa: PLC0415

    from dotnet_ai_kit.copier import deploy_to_linked_repos  # noqa: PLC0415
    from dotnet_ai_kit.models import DotnetAiConfig  # noqa: PLC0415

    config = DotnetAiConfig(ai_tools=["copilot"])
    config.repos.command = str(secondary)

    fake_proc = MagicMock(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=fake_proc):
        deploy_to_linked_repos(
            primary_root=primary,
            config=config,
            tool_version="1.0.0",
            package_dir=Path(__file__).resolve().parent.parent.parent,
        )

    # The render path MUST have fired in the secondary
    assert (secondary / ".github" / "copilot-instructions.md").is_file(), (
        "Blocker-6 regression: linked-secondary Copilot deploy did NOT render "
        "copilot-instructions.md"
    )
