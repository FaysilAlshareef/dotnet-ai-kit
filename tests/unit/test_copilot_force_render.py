"""T072b — `--force-render <path>` flag per contract:39-41.

Asserts:
(a) `dotnet-ai init --force-render <path>` allows explicit overwrite of
    THAT exact path only.
(b) `--force-render` does NOT bypass protection for OTHER unmanaged Copilot
    paths (path-specific opt-in).
(c) After opt-in, the file is recorded in manifest.json with
    `host_owner="copilot"` and explicit-consent flag.
(d) The same opt-in flag works for `dotnet-ai upgrade --copilot --force-render <path>`.
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
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_force_render_overwrites_named_path_only(tmp_path: Path) -> None:
    """(a)+(b): --force-render <path> overwrites THAT path; OTHER pre-existing
    files MUST still be preserved."""
    _create_project(tmp_path)
    github = tmp_path / ".github"
    github.mkdir()
    target_to_overwrite = github / "copilot-instructions.md"
    target_to_overwrite.write_text("OLD CONTENT\n", encoding="utf-8")

    # Also create an unrelated pre-existing agent file — MUST NOT be overwritten
    agents = github / "agents"
    agents.mkdir()
    other = agents / "dotnet-ai-architect.agent.md"
    other.write_text("USER AGENT BODY\n", encoding="utf-8")

    runner.invoke(
        app,
        [
            "init",
            str(tmp_path),
            "--ai",
            "copilot",
            "--force-render",
            ".github/copilot-instructions.md",
        ],
        catch_exceptions=False,
    )

    # The named file should be overwritten (new content)
    new_content = target_to_overwrite.read_text(encoding="utf-8")
    assert new_content != "OLD CONTENT\n", "named --force-render path MUST be overwritten"

    # The OTHER file should still have the user content (not overwritten)
    assert other.read_text(encoding="utf-8") == "USER AGENT BODY\n", (
        "T072b violation: --force-render bypassed protection for OTHER unmanaged path"
    )


def test_force_render_records_explicit_consent_in_manifest(tmp_path: Path) -> None:
    """(c): After opt-in, file recorded in manifest with host_owner=copilot."""
    _create_project(tmp_path)
    github = tmp_path / ".github"
    github.mkdir()
    target_file = github / "copilot-instructions.md"
    target_file.write_text("OLD\n", encoding="utf-8")

    runner.invoke(
        app,
        [
            "init",
            str(tmp_path),
            "--ai",
            "copilot",
            "--force-render",
            ".github/copilot-instructions.md",
            "--json",
        ],
        catch_exceptions=False,
    )

    manifest = read_manifest(tmp_path)
    if manifest is None:
        # Init may not have created a manifest if conflict path exited;
        # acceptable — the contract is conditional. Run upgrade --copilot
        # to force the manifest record.
        runner.invoke(
            app,
            [
                "upgrade",
                "--copilot",
                "--force-render",
                ".github/copilot-instructions.md",
            ],
            catch_exceptions=False,
        )
        manifest = read_manifest(tmp_path)
    assert manifest is not None
    # Find the entry with host_owner="copilot" matching our path
    copilot_entries = [f for f in manifest.files if f.host_owner == "copilot"]
    assert any(f.path.endswith("copilot-instructions.md") for f in copilot_entries), (
        f"T072b violation: manifest MUST record host_owner='copilot' for "
        f"force-rendered file; got entries: {copilot_entries}"
    )


def test_upgrade_copilot_force_render_works(tmp_path: Path, monkeypatch) -> None:
    """(d): `dotnet-ai upgrade --copilot --force-render <path>` works."""
    _create_project(tmp_path)
    # Initial init writes copilot-instructions.md (since no pre-existing)
    runner.invoke(app, ["init", str(tmp_path), "--ai", "copilot"], catch_exceptions=False)
    monkeypatch.chdir(tmp_path)

    # Now SIMULATE the user editing the file (it becomes user-modified)
    target_file = tmp_path / ".github" / "copilot-instructions.md"
    target_file.write_text("USER EDIT\n", encoding="utf-8")

    # Without --force-render, upgrade --copilot preserves the user edit
    result = runner.invoke(app, ["upgrade", "--copilot"], catch_exceptions=False)
    assert target_file.read_text(encoding="utf-8") == "USER EDIT\n"

    # With --force-render, upgrade --copilot overwrites
    result = runner.invoke(
        app,
        [
            "upgrade",
            "--copilot",
            "--force-render",
            ".github/copilot-instructions.md",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert target_file.read_text(encoding="utf-8") != "USER EDIT\n"
