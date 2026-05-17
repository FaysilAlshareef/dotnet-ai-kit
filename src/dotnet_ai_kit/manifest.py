"""Generated-file manifest (T042 / FR-032).

Represents ``.dotnet-ai-kit/manifest.json`` — the per-project record of every
file the plugin has deployed. Used by the atomic upgrade orchestrator
(``upgrade.py``) to detect user modifications and roll back on failure.

The schema mirrors ``specs/018-fix-token-burn/contracts/manifest.schema.json``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(\.\d+)?$")


class DeployedFile(BaseModel):
    """One file deployed by the plugin in this project."""

    path: str
    sha256: str
    plugin_version: str
    deployed_at: str
    source_template: str | None = None

    @field_validator("path")
    @classmethod
    def _no_traversal(cls, v: str) -> str:
        if ".." in Path(v).parts:
            raise ValueError("manifest path must not contain '..' segments")
        return v.replace("\\", "/")

    @field_validator("sha256")
    @classmethod
    def _hex_sha(cls, v: str) -> str:
        if not SHA256_RE.match(v):
            raise ValueError("sha256 must be 64 lowercase hex chars")
        return v

    @field_validator("plugin_version")
    @classmethod
    def _version_shape(cls, v: str) -> str:
        if not VERSION_RE.match(v):
            raise ValueError(f"plugin_version {v!r} is not N.N.N[.N]")
        return v


class Manifest(BaseModel):
    """The full ``.dotnet-ai-kit/manifest.json`` payload."""

    plugin_version: str
    schema_version: str = Field(default="1")
    created_at: str
    last_upgrade_at: str | None = None
    files: list[DeployedFile] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _schema_one(cls, v: str) -> str:
        if v != "1":
            raise ValueError(f"manifest schema_version must be '1' (got {v!r})")
        return v

    @field_validator("plugin_version")
    @classmethod
    def _root_version(cls, v: str) -> str:
        if not VERSION_RE.match(v):
            raise ValueError(f"plugin_version {v!r} is not N.N.N[.N]")
        return v

    @field_validator("files")
    @classmethod
    def _unique_paths(cls, files: list[DeployedFile]) -> list[DeployedFile]:
        seen: set[str] = set()
        for f in files:
            if f.path in seen:
                raise ValueError(f"duplicate manifest path: {f.path!r}")
            seen.add(f.path)
        return files


def manifest_path(project_root: Path) -> Path:
    return project_root / ".dotnet-ai-kit" / "manifest.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(project_root: Path) -> Manifest | None:
    p = manifest_path(project_root)
    if not p.is_file():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return Manifest.model_validate(data)


def write_manifest(project_root: Path, manifest: Manifest) -> Path:
    """Atomically write the manifest to disk (temp + os.replace)."""
    target = manifest_path(project_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest.model_dump(mode="json", exclude_none=False)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    tmp = target.with_name(f"manifest.json.{uuid.uuid4().hex}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)
    return target


# ---------------------------------------------------------------------------
# Feature 019 / commit 9 / T107: integrity_check
# ---------------------------------------------------------------------------


@dataclass
class IntegrityIssue:
    """A single integrity-check finding."""

    path: str
    issue_class: str  # "missing", "hash_mismatch", "extra", "manifest_unreadable"
    expected_hash: str | None = None
    observed_state: str = ""
    remediation: str = ""


@dataclass
class IntegrityReport:
    """Result of `integrity_check(project_root)` per FR-032 / CHK042.

    `ok`: True iff there are no issues across all checks.
    `issues`: list of `IntegrityIssue` (empty if ok).
    """

    project_root: Path
    manifest_readable: bool = True
    issues: list[IntegrityIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.manifest_readable and not self.issues

    def fail_message(self) -> str:
        """Compose an actionable failure message per FR-032 / CHK042.

        Names each inconsistent file, the expected hash, the observed state,
        and the remediation command. Returns empty string when `ok`.
        """
        if self.ok:
            return ""

        lines: list[str] = []
        if not self.manifest_readable:
            lines.append(
                "manifest.json is missing or unreadable. "
                "Run `dotnet-ai init <path>` to (re)create it."
            )
        for issue in self.issues:
            parts = [f"  - {issue.path}: {issue.issue_class}"]
            if issue.expected_hash:
                parts.append(f"expected sha256={issue.expected_hash[:12]}...")
            if issue.observed_state:
                parts.append(f"observed: {issue.observed_state}")
            if issue.remediation:
                parts.append(f"fix: {issue.remediation}")
            lines.append(" — ".join(parts))
        return "\n".join(lines)


def integrity_check(project_root: Path) -> IntegrityReport:
    """Verify `.dotnet-ai-kit/manifest.json` integrity per FR-032 / CHK042.

    Checks:
    1. Manifest file readable + schema-valid (recorded in `manifest_readable`).
    2. Every path in `files[]` exists on disk.
    3. Every existing file's sha256 matches the manifest's recorded hash.

    Returns an `IntegrityReport`. Caller maps `report.ok` to exit code 0/14
    per the contract.
    """
    report = IntegrityReport(project_root=project_root)

    p = manifest_path(project_root)
    if not p.is_file():
        report.manifest_readable = False
        report.issues.append(
            IntegrityIssue(
                path=str(p),
                issue_class="manifest_unreadable",
                observed_state="file does not exist",
                remediation=f"run `dotnet-ai init {project_root}`",
            )
        )
        return report

    try:
        manifest = read_manifest(project_root)
    except Exception as exc:  # noqa: BLE001 — surface the message to the user
        report.manifest_readable = False
        report.issues.append(
            IntegrityIssue(
                path=str(p),
                issue_class="manifest_unreadable",
                observed_state=f"parse error: {exc}",
                remediation=f"validate manifest.json against schemas/manifest-json.schema.json or run `dotnet-ai init --force {project_root}`",
            )
        )
        return report

    assert manifest is not None  # narrowed by read_manifest result

    for entry in manifest.files:
        target = project_root / entry.path
        if not target.is_file():
            report.issues.append(
                IntegrityIssue(
                    path=entry.path,
                    issue_class="missing",
                    expected_hash=entry.sha256,
                    observed_state="file not found on disk",
                    remediation=f"run `dotnet-ai upgrade {project_root}` to restore",
                )
            )
            continue

        actual_hash = sha256_file(target)
        if actual_hash != entry.sha256:
            report.issues.append(
                IntegrityIssue(
                    path=entry.path,
                    issue_class="hash_mismatch",
                    expected_hash=entry.sha256,
                    observed_state=f"sha256={actual_hash[:12]}...",
                    remediation=(
                        "either accept the user modification by running "
                        f"`dotnet-ai migrate {project_root}` (user-modified files "
                        "are preserved in place) or re-render with "
                        f"`dotnet-ai upgrade {project_root}`"
                    ),
                )
            )

    return report
