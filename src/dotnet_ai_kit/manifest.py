"""Generated-file manifest (T042 / FR-032).

Represents ``.dotnet-ai-kit/manifest.json`` — the per-project record of every
file the plugin has deployed. Used by the atomic upgrade orchestrator
(``upgrade.py``) to detect user modifications and roll back on failure.

The schema mirrors ``specs/018-fix-token-burn/contracts/manifest.schema.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

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
