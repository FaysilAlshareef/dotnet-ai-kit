"""T102 — manifest integrity check (commit 9 / FR-032 / CHK042).

Asserts that `manifest.integrity_check(project_root)`:
1. Returns ok=True when manifest is valid and all files match hashes.
2. Reports `manifest_unreadable` if manifest is missing.
3. Reports `missing` for files in manifest that don't exist on disk.
4. Reports `hash_mismatch` for files whose sha256 differs.
5. Produces an actionable fail_message naming file + expected hash +
   observed state + remediation command per CHK042.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotnet_ai_kit.manifest import (
    DeployedFile,
    IntegrityReport,
    Manifest,
    integrity_check,
    sha256_file,
    utc_now_iso,
    write_manifest,
)


def _create_managed_file(project_root: Path, relpath: str, content: str = "x") -> Path:
    p = project_root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_integrity_check_ok_when_manifest_matches_disk(tmp_path: Path) -> None:
    """All files present + hashes match → report.ok is True."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    f = _create_managed_file(project_root, ".claude/settings.json", "{}")
    manifest = Manifest(
        plugin_version="1.0.0",
        created_at=utc_now_iso(),
        files=[
            DeployedFile(
                path=".claude/settings.json",
                sha256=sha256_file(f),
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
            )
        ],
    )
    write_manifest(project_root, manifest)

    report = integrity_check(project_root)
    assert report.ok
    assert report.manifest_readable
    assert report.issues == []


def test_integrity_check_reports_missing_manifest(tmp_path: Path) -> None:
    """No manifest → report.ok=False, manifest_readable=False."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    report = integrity_check(project_root)
    assert not report.ok
    assert not report.manifest_readable
    assert len(report.issues) == 1
    assert report.issues[0].issue_class == "manifest_unreadable"
    assert "init" in report.issues[0].remediation


def test_integrity_check_reports_missing_file(tmp_path: Path) -> None:
    """File in manifest but not on disk → 'missing' issue."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    # Manifest references a file that won't exist
    manifest = Manifest(
        plugin_version="1.0.0",
        created_at=utc_now_iso(),
        files=[
            DeployedFile(
                path=".claude/nonexistent.json",
                sha256="a" * 64,
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
            )
        ],
    )
    write_manifest(project_root, manifest)

    report = integrity_check(project_root)
    assert not report.ok
    assert len(report.issues) == 1
    assert report.issues[0].issue_class == "missing"
    assert report.issues[0].path == ".claude/nonexistent.json"


def test_integrity_check_reports_hash_mismatch(tmp_path: Path) -> None:
    """File on disk with different hash than manifest → 'hash_mismatch' issue."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    f = _create_managed_file(project_root, ".claude/settings.json", "{}")
    manifest = Manifest(
        plugin_version="1.0.0",
        created_at=utc_now_iso(),
        files=[
            DeployedFile(
                path=".claude/settings.json",
                sha256="a" * 64,  # NOT the actual hash
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
            )
        ],
    )
    write_manifest(project_root, manifest)

    report = integrity_check(project_root)
    assert not report.ok
    assert len(report.issues) == 1
    assert report.issues[0].issue_class == "hash_mismatch"
    assert report.issues[0].expected_hash == "a" * 64
    assert "sha256=" in report.issues[0].observed_state


def test_integrity_check_fail_message_is_actionable(tmp_path: Path) -> None:
    """Per CHK042: fail message includes path + expected hash + remediation."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    _create_managed_file(project_root, ".claude/settings.json", "{}")
    manifest = Manifest(
        plugin_version="1.0.0",
        created_at=utc_now_iso(),
        files=[
            DeployedFile(
                path=".claude/settings.json",
                sha256="b" * 64,
                plugin_version="1.0.0",
                deployed_at=utc_now_iso(),
            )
        ],
    )
    write_manifest(project_root, manifest)

    report = integrity_check(project_root)
    msg = report.fail_message()

    assert ".claude/settings.json" in msg
    assert "hash_mismatch" in msg
    assert "expected sha256=" in msg
    assert "fix:" in msg
