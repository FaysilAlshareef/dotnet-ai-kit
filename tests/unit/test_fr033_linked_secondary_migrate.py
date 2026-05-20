"""T096 — FR-033 / SC-014 (migrate half): linked-secondary migrate.

Per FR-033 / SC-014 / CHK051: when `dotnet-ai migrate --include-linked` is
applied to the primary repo, the migrate flow iterates `config.repos.*`
linked secondaries and applies the same classification rules (clean →
move-to-backup, user-modified → preserve in place per FR-022).
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app
from dotnet_ai_kit.manifest import DeployedFile, Manifest, write_manifest

runner = CliRunner()


def _setup_with_manifest(repo: Path, name: str, file_body: str = "BODY\n") -> Path:
    """Set up a repo with one manifest entry pointing at a real file."""
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "App.sln").write_text("Microsoft\n", encoding="utf-8")
    config_dir = repo / ".dotnet-ai-kit"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "version.txt").write_text("1.0.0", encoding="utf-8")
    (config_dir / "config.yml").write_text("ai_tools: [claude]\nrepos: {}\n", encoding="utf-8")
    # Create a managed file with known hash
    managed_dir = repo / ".claude" / "commands"
    managed_dir.mkdir(parents=True, exist_ok=True)
    managed_file = managed_dir / f"{name}.md"
    # Write bytes directly so the hash matches what sha256_file reads back.
    body_bytes = file_body.encode("utf-8")
    managed_file.write_bytes(body_bytes)

    # Build a manifest with one entry for this file
    import hashlib

    entry = DeployedFile(
        path=str(managed_file.relative_to(repo)).replace("\\", "/"),
        sha256=hashlib.sha256(body_bytes).hexdigest(),
        host_owner="claude",
        plugin_version="1.0.0",
        deployed_at="2026-05-18T00:00:00Z",
    )
    manifest = Manifest(
        plugin_version="1.0.0",
        schema_version="2",
        created_at="2026-05-18T00:00:00Z",
        last_upgrade_at="2026-05-18T00:00:00Z",
        last_migrate_at=None,
        files=[entry],
    )
    write_manifest(repo, manifest)
    return managed_file


def test_migrate_include_linked_processes_secondaries(tmp_path: Path) -> None:
    """T096: `migrate --include-linked` MUST iterate linked secondaries."""
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"
    primary_file = _setup_with_manifest(primary, "primary-cmd")
    secondary_file = _setup_with_manifest(secondary, "secondary-cmd")

    # Wire the secondary into primary's config.repos.command
    (primary / ".dotnet-ai-kit" / "config.yml").write_text(
        f"ai_tools: [claude]\nrepos:\n  command: {secondary.as_posix()}\n",
        encoding="utf-8",
    )

    # Run migrate --include-linked
    result = runner.invoke(
        app,
        ["migrate", str(primary), "--include-linked"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, f"migrate failed: {result.output}"

    # Both files should be MOVED (they were 'clean' per their manifest hashes)
    assert not primary_file.is_file(), "primary clean file MUST be moved"
    assert not secondary_file.is_file(), (
        "T096: secondary clean file MUST also be moved with --include-linked"
    )

    # Backups should exist on both
    primary_backup_root = primary / ".dotnet-ai-kit" / "backups" / "migrate"
    secondary_backup_root = secondary / ".dotnet-ai-kit" / "backups" / "migrate"
    assert primary_backup_root.is_dir()
    assert secondary_backup_root.is_dir()


def test_migrate_preserves_user_modified_in_secondaries(tmp_path: Path) -> None:
    """FR-022 + FR-033: user-modified files in linked secondaries MUST be
    preserved in place (NOT moved to backup) when migrate runs without
    --include-modified."""
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"
    _setup_with_manifest(primary, "primary-cmd", file_body="X\n")
    sec_file = _setup_with_manifest(secondary, "sec-cmd", file_body="ORIGINAL\n")

    # Now MUTATE the secondary file so its hash no longer matches manifest
    sec_file.write_bytes(b"USER-MODIFIED\n")

    (primary / ".dotnet-ai-kit" / "config.yml").write_text(
        f"ai_tools: [claude]\nrepos:\n  command: {secondary.as_posix()}\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["migrate", str(primary), "--include-linked"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # The user-modified secondary file MUST still be present (preserved)
    assert sec_file.is_file(), (
        "FR-022 violation: user-modified secondary file was moved despite "
        "missing --include-modified flag"
    )
    assert sec_file.read_bytes() == b"USER-MODIFIED\n"


def test_migrate_without_include_linked_does_not_touch_secondaries(tmp_path: Path) -> None:
    """Default behavior: migrate WITHOUT --include-linked leaves secondaries
    untouched. The user must explicitly opt in to multi-repo migration."""
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"
    _setup_with_manifest(primary, "primary-cmd")
    sec_file = _setup_with_manifest(secondary, "sec-cmd")

    (primary / ".dotnet-ai-kit" / "config.yml").write_text(
        f"ai_tools: [claude]\nrepos:\n  command: {secondary.as_posix()}\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["migrate", str(primary)],  # NO --include-linked
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Secondary file MUST still be present — not touched without opt-in
    assert sec_file.is_file(), "migrate without --include-linked MUST NOT touch linked secondaries"
