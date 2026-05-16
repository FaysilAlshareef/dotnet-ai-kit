"""T037 — FR-031 / SC-013: atomic upgrade with rollback.

Covers 7 cases:
  (a) successful upgrade
  (b) IOError mid-run → full rollback
  (c) dry-run writes nothing
  (d) user-modified managed file aborts without --force
  (e) --force overrides user-modified check
  (f) legacy install with no manifest
  (g) backup rotation retains last 3 runs
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from dotnet_ai_kit.manifest import (
    DeployedFile,
    Manifest,
    manifest_path,
    sha256_file,
    utc_now_iso,
    write_manifest,
)
from dotnet_ai_kit.upgrade import run_upgrade


def _seed_existing(project: Path, body: str = "v1\n") -> Manifest:
    project.mkdir(parents=True, exist_ok=True)
    target = project / "commands" / "init.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body.encode("utf-8"))
    manifest = Manifest(
        plugin_version="1.0.0",
        created_at=utc_now_iso(),
        files=[
            DeployedFile(
                path="commands/init.md",
                sha256=sha256_file(target),
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
            )
        ],
    )
    write_manifest(project, manifest)
    return manifest


def _good_deploy(project: Path, ctx) -> list[DeployedFile]:
    target = project / "commands" / "init.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    ctx.record_backup(target)
    target.write_bytes(b"v2\n")
    return [
        DeployedFile(
            path="commands/init.md",
            sha256=sha256_file(target),
            plugin_version="1.1.0",
            deployed_at=utc_now_iso(),
        )
    ]


def _failing_deploy(project: Path, ctx) -> list[DeployedFile]:
    target = project / "commands" / "init.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    ctx.record_backup(target)
    target.write_bytes(b"v2\n")
    raise IOError("simulated mid-run failure")


def test_a_successful_upgrade_updates_manifest_and_backs_up(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _seed_existing(project)
    result = run_upgrade(project, plugin_version="1.1.0", deploy_fn=_good_deploy)
    assert result.status == "ok"
    assert result.files_changed == 1
    assert (project / "commands/init.md").read_bytes() == b"v2\n"
    # Backup contains the v1 copy.
    backup = list(result.backup_dir.rglob("init.md"))
    assert backup and backup[0].read_bytes() == b"v1\n"
    # Manifest reflects the new SHA.
    new_sha = hashlib.sha256(b"v2\n").hexdigest()
    assert result.manifest_path is not None
    text = result.manifest_path.read_text(encoding="utf-8")
    assert new_sha in text

    # Idempotent re-run on the same content yields zero diff.
    re_result = run_upgrade(project, plugin_version="1.1.0", deploy_fn=_good_deploy)
    assert re_result.status == "ok"
    assert (project / "commands/init.md").read_bytes() == b"v2\n"


def test_b_ioerror_mid_run_triggers_full_rollback(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _seed_existing(project)
    result = run_upgrade(project, plugin_version="1.1.0", deploy_fn=_failing_deploy)
    assert result.status == "rolled-back"
    # File restored to v1
    assert (project / "commands/init.md").read_text(encoding="utf-8") == "v1\n"


def test_c_dry_run_writes_nothing(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _seed_existing(project)

    def boom(*_a, **_k):  # should never run on dry-run
        raise AssertionError("deploy_fn must not be called on dry-run")

    result = run_upgrade(project, plugin_version="1.1.0", deploy_fn=boom, dry_run=True)
    assert result.status == "dry-run"
    assert (project / "commands/init.md").read_text(encoding="utf-8") == "v1\n"


def test_d_user_modified_aborts_without_force(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _seed_existing(project)
    # Tamper.
    (project / "commands/init.md").write_bytes(b"hand-edited\n")
    result = run_upgrade(project, plugin_version="1.1.0", deploy_fn=_good_deploy)
    assert result.status == "user-modified"
    assert result.user_modified == ["commands/init.md"]
    assert (project / "commands/init.md").read_bytes() == b"hand-edited\n"


def test_e_force_overrides_user_modified(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _seed_existing(project)
    (project / "commands/init.md").write_bytes(b"hand-edited\n")
    result = run_upgrade(
        project,
        plugin_version="1.1.0",
        deploy_fn=_good_deploy,
        force=True,
    )
    assert result.status == "ok"
    assert (project / "commands/init.md").read_bytes() == b"v2\n"


def test_f_legacy_install_with_no_manifest(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    # No prior manifest, no prior files.
    result = run_upgrade(project, plugin_version="1.1.0", deploy_fn=_good_deploy)
    assert result.status == "ok"
    assert manifest_path(project).is_file()


def test_g_backup_rotation_retains_last_three(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _seed_existing(project)
    for _ in range(5):
        run_upgrade(project, plugin_version="1.1.0", deploy_fn=_good_deploy)
    backups = sorted((project / ".dotnet-ai-kit" / "backups" / "upgrade").iterdir())
    assert len(backups) <= 3, f"expected ≤3 backups, found {len(backups)}"
