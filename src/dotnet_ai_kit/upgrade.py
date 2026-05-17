"""Atomic upgrade orchestrator (T043 / FR-031 / SC-013).

``run_upgrade()`` performs an idempotent, transactional upgrade of a
.dotnet-ai-kit installation:

1. Read existing manifest (or scan known plugin paths if absent).
2. For each managed file, compare current SHA-256 with the manifest entry.
3. If a managed file was modified locally, abort unless ``force=True``.
4. Create a timestamped backup of every file we are about to overwrite.
5. Run the deploy.
6. On ANY exception, walk the backup directory and restore each file.
7. Write the new manifest.
8. Rotate backup directories to keep only the last 3.

The orchestrator depends on a caller-supplied ``deploy_fn`` so we don't
hard-couple to ``copier.py`` here — tests can pass a stub.
"""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .manifest import (
    DeployedFile,
    Manifest,
    read_manifest,
    sha256_file,
    utc_now_iso,
    write_manifest,
)

DeployFn = Callable[[Path, "UpgradeContext"], list[DeployedFile]]


@dataclass
class UpgradeContext:
    """Passed to a caller-supplied deploy function so it can record outputs."""

    project_root: Path
    plugin_version: str
    backup_root: Path
    dry_run: bool = False
    force: bool = False
    backed_up: dict[Path, Path] = field(default_factory=dict)

    def record_backup(self, target: Path) -> None:
        """Backup an existing managed file before overwriting it."""
        if not target.is_file():
            return
        rel = target.relative_to(self.project_root)
        backup_path = self.backup_root / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup_path)
        self.backed_up[target] = backup_path


@dataclass
class UpgradeResult:
    """Outcome of ``run_upgrade()``."""

    status: str  # "ok" | "rolled-back" | "user-modified" | "dry-run"
    files_changed: int
    backup_dir: Path | None
    manifest_path: Path | None
    user_modified: list[str] = field(default_factory=list)
    error: str | None = None


def _detect_user_modified(project_root: Path, manifest: Manifest) -> list[str]:
    """Return relative paths whose on-disk SHA differs from the manifest."""
    modified: list[str] = []
    for entry in manifest.files:
        on_disk = project_root / entry.path
        if not on_disk.is_file():
            continue
        if sha256_file(on_disk) != entry.sha256:
            modified.append(entry.path)
    return sorted(modified)


def _restore(backup_root: Path, project_root: Path) -> None:
    """Walk backups and restore each file to its original location."""
    if not backup_root.is_dir():
        return
    for src in backup_root.rglob("*"):
        if src.is_file():
            rel = src.relative_to(backup_root)
            dst = project_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def _rotate_backups(parent: Path, keep: int = 3) -> None:
    if not parent.is_dir():
        return
    dirs = sorted([p for p in parent.iterdir() if p.is_dir()], key=lambda p: p.name)
    for old in dirs[:-keep]:
        shutil.rmtree(old, ignore_errors=True)


def run_upgrade(
    project_root: Path,
    *,
    plugin_version: str,
    deploy_fn: DeployFn,
    dry_run: bool = False,
    force: bool = False,
) -> UpgradeResult:
    """Atomic upgrade. See module docstring for the flow."""
    backup_parent = project_root / ".dotnet-ai-kit" / "backups" / "upgrade"
    backup_parent.mkdir(parents=True, exist_ok=True)

    iso = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = backup_parent / f"{iso}-{uuid.uuid4().hex[:8]}"

    existing_manifest = read_manifest(project_root)
    user_modified: list[str] = []
    if existing_manifest is not None:
        user_modified = _detect_user_modified(project_root, existing_manifest)
        if user_modified and not force:
            return UpgradeResult(
                status="user-modified",
                files_changed=0,
                backup_dir=None,
                manifest_path=None,
                user_modified=user_modified,
                error=(
                    f"refusing to overwrite {len(user_modified)} user-modified file(s); "
                    "re-run with --force to proceed."
                ),
            )

    if dry_run:
        return UpgradeResult(
            status="dry-run",
            files_changed=0,
            backup_dir=None,
            manifest_path=None,
            user_modified=user_modified,
        )

    backup_dir.mkdir(parents=True, exist_ok=True)
    context = UpgradeContext(
        project_root=project_root,
        plugin_version=plugin_version,
        backup_root=backup_dir,
        dry_run=False,
        force=force,
    )

    try:
        deployed = deploy_fn(project_root, context)
    except Exception as exc:
        _restore(backup_dir, project_root)
        return UpgradeResult(
            status="rolled-back",
            files_changed=0,
            backup_dir=backup_dir,
            manifest_path=None,
            user_modified=user_modified,
            error=f"{type(exc).__name__}: {exc}",
        )

    # Successful deploy — write/refresh manifest.
    created_at = existing_manifest.created_at if existing_manifest else utc_now_iso()
    manifest = Manifest(
        plugin_version=plugin_version,
        schema_version="1",
        created_at=created_at,
        last_upgrade_at=utc_now_iso(),
        files=deployed,
    )
    manifest_p = write_manifest(project_root, manifest)
    _rotate_backups(backup_parent)
    return UpgradeResult(
        status="ok",
        files_changed=len(deployed),
        backup_dir=backup_dir,
        manifest_path=manifest_p,
        user_modified=user_modified,
    )
