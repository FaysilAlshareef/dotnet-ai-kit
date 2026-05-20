"""T093 — migrate backup folder + 3-keep rotation (commit 10 / FR-021 / CHK021 / CHK023).

Asserts:
1. Clean files MOVE to `.dotnet-ai-kit/backups/migrate/<YYYYMMDD-HHMMSS>/`
2. 3-keep retention rotates oldest backup folders when a 4th is created
3. Backup folder structure preserves the file's original repo-root-relative path
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app
from dotnet_ai_kit.manifest import (
    DeployedFile,
    Manifest,
    sha256_file,
    utc_now_iso,
    write_manifest,
)

runner = CliRunner()


def _build_managed_project(tmp_path: Path) -> Path:
    """Create a project with .dotnet-ai-kit/ + manifest + 2 managed files."""
    project = tmp_path / "proj"
    project.mkdir()

    # Two managed files
    cmd_file = project / ".claude" / "commands" / "x.md"
    cmd_file.parent.mkdir(parents=True)
    cmd_file.write_text("clean content\n", encoding="utf-8")

    skill_file = project / ".claude" / "skills" / "y" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("clean skill\n", encoding="utf-8")

    manifest = Manifest(
        plugin_version="1.0.0",
        schema_version="2",
        created_at=utc_now_iso(),
        files=[
            DeployedFile(
                path=".claude/commands/x.md",
                sha256=sha256_file(cmd_file),
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
                host_owner="claude",
            ),
            DeployedFile(
                path=".claude/skills/y/SKILL.md",
                sha256=sha256_file(skill_file),
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
                host_owner="claude",
            ),
        ],
    )
    write_manifest(project, manifest)
    return project


def test_migrate_moves_clean_files_to_backup_folder(tmp_path: Path) -> None:
    """Clean files MOVE to backups/migrate/<timestamp>/<original-path>/."""
    project = _build_managed_project(tmp_path)

    result = runner.invoke(app, ["migrate", str(project)])
    assert result.exit_code == 0, result.output

    # Both files should no longer exist at original locations
    assert not (project / ".claude" / "commands" / "x.md").exists()
    assert not (project / ".claude" / "skills" / "y" / "SKILL.md").exists()

    # Backup folder created under .dotnet-ai-kit/backups/migrate/<timestamp>/
    backup_root = project / ".dotnet-ai-kit" / "backups" / "migrate"
    assert backup_root.is_dir()
    backups = list(backup_root.iterdir())
    assert len(backups) == 1, f"expected 1 backup folder, got {len(backups)}"

    # Backup preserves original repo-root-relative path
    timestamp_dir = backups[0]
    assert (timestamp_dir / ".claude" / "commands" / "x.md").is_file()
    assert (timestamp_dir / ".claude" / "skills" / "y" / "SKILL.md").is_file()


def test_migrate_dry_run_does_not_mutate(tmp_path: Path) -> None:
    """--dry-run MUST NOT move or delete any files."""
    project = _build_managed_project(tmp_path)

    pre_files = {p.relative_to(project) for p in project.rglob("*") if p.is_file()}
    result = runner.invoke(app, ["migrate", str(project), "--dry-run"])
    assert result.exit_code == 0, result.output

    post_files = {p.relative_to(project) for p in project.rglob("*") if p.is_file()}
    assert pre_files == post_files, (
        f"--dry-run mutated files: added {post_files - pre_files}, removed {pre_files - post_files}"
    )


def test_migrate_preserves_user_modified_by_default(tmp_path: Path) -> None:
    """User-modified files (hash mismatch) MUST be preserved by default."""
    project = _build_managed_project(tmp_path)
    # Mutate one managed file to make it user-modified
    cmd_file = project / ".claude" / "commands" / "x.md"
    user_content = "USER EDITED THIS FILE\n"
    cmd_file.write_text(user_content, encoding="utf-8")

    result = runner.invoke(app, ["migrate", str(project)])
    assert result.exit_code == 0

    # User file still exists at original location
    assert cmd_file.is_file()
    assert cmd_file.read_text(encoding="utf-8") == user_content


def test_migrate_include_modified_removes_modified_files(tmp_path: Path) -> None:
    """--include-modified opt-in moves user-modified files to backup too."""
    project = _build_managed_project(tmp_path)
    cmd_file = project / ".claude" / "commands" / "x.md"
    cmd_file.write_text("USER EDITED\n", encoding="utf-8")

    result = runner.invoke(app, ["migrate", str(project), "--include-modified"])
    assert result.exit_code == 0

    # User file no longer at original location
    assert not cmd_file.exists()


def test_migrate_3_keep_rotation(tmp_path: Path) -> None:
    """When a 4th migrate runs, the oldest backup folder is rotated out."""
    project = _build_managed_project(tmp_path)

    # Run migrate 4 times, each time recreate the managed files to migrate again
    for i in range(4):
        # Recreate managed files
        (project / ".claude" / "commands" / "x.md").parent.mkdir(parents=True, exist_ok=True)
        (project / ".claude" / "commands" / "x.md").write_text(f"content {i}\n", encoding="utf-8")
        (project / ".claude" / "skills" / "y").mkdir(parents=True, exist_ok=True)
        (project / ".claude" / "skills" / "y" / "SKILL.md").write_text(
            f"skill {i}\n", encoding="utf-8"
        )
        # Update manifest hashes
        cmd_file = project / ".claude" / "commands" / "x.md"
        skill_file = project / ".claude" / "skills" / "y" / "SKILL.md"
        manifest = Manifest(
            plugin_version="1.0.0",
            schema_version="2",
            created_at=utc_now_iso(),
            files=[
                DeployedFile(
                    path=".claude/commands/x.md",
                    sha256=sha256_file(cmd_file),
                    plugin_version="1.0.0",
                    deployed_at=utc_now_iso(),
                    host_owner="claude",
                ),
                DeployedFile(
                    path=".claude/skills/y/SKILL.md",
                    sha256=sha256_file(skill_file),
                    plugin_version="1.0.0",
                    deployed_at=utc_now_iso(),
                    host_owner="claude",
                ),
            ],
        )
        write_manifest(project, manifest)

        # Run migrate — use unique timestamp suffix by sleeping (clock-second resolution)
        import time

        time.sleep(1.05)
        result = runner.invoke(app, ["migrate", str(project)])
        assert result.exit_code == 0, result.output

    backup_root = project / ".dotnet-ai-kit" / "backups" / "migrate"
    backups = sorted(p for p in backup_root.iterdir() if p.is_dir())
    assert len(backups) == 3, (
        f"3-keep rotation: expected 3 backup folders, got {len(backups)}: "
        f"{[b.name for b in backups]}"
    )
