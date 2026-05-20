"""T036 — FR-032: manifest pydantic models + JSON Schema compliance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotnet_ai_kit.manifest import (
    DeployedFile,
    Manifest,
    read_manifest,
    sha256_file,
    utc_now_iso,
    write_manifest,
)

REPO = Path(__file__).resolve().parent.parent
SCHEMA = REPO / "specs" / "018-fix-token-burn" / "contracts" / "manifest.schema.json"


def _file(**over) -> dict:
    base = dict(
        path="commands/init.md",
        sha256="a" * 64,
        plugin_version="1.0.0",
        deployed_at=utc_now_iso(),
        source_template="commands/init.md",
    )
    base.update(over)
    return base


def test_manifest_roundtrip(tmp_path: Path) -> None:
    m = Manifest(
        plugin_version="1.0.0",
        schema_version="1",
        created_at=utc_now_iso(),
        last_upgrade_at=None,
        files=[DeployedFile(**_file())],
    )
    project = tmp_path / "proj"
    write_manifest(project, m)
    out = read_manifest(project)
    assert out is not None
    assert out.plugin_version == "1.0.0"
    assert out.files[0].path == "commands/init.md"


def test_duplicate_paths_rejected() -> None:
    a = DeployedFile(**_file())
    b = DeployedFile(**_file())
    with pytest.raises(Exception) as exc:
        Manifest(
            plugin_version="1.0.0",
            schema_version="1",
            created_at=utc_now_iso(),
            files=[a, b],
        )
    assert "duplicate" in str(exc.value).lower()


def test_sha_must_be_64_hex_lower() -> None:
    with pytest.raises(Exception):
        DeployedFile(**_file(sha256="NOTHEX"))
    with pytest.raises(Exception):
        DeployedFile(**_file(sha256="A" * 64))  # uppercase rejected


def test_root_fields_enforced() -> None:
    # missing created_at
    with pytest.raises(Exception):
        Manifest(plugin_version="1.0.0", schema_version="1", files=[])  # type: ignore[arg-type]
    # Feature 019 / commit 10: schema_version defaults to "2" (writer always
    # emits v2). The reader still accepts "1" for backward compatibility.
    m = Manifest(plugin_version="1.0.0", created_at=utc_now_iso(), files=[])
    assert m.schema_version == "2"


def test_path_traversal_rejected() -> None:
    with pytest.raises(Exception):
        DeployedFile(**_file(path="../etc/passwd"))


def test_json_schema_validation() -> None:
    """Feature 019 / commit 10: validate against the new feature-019 schema.

    The legacy feature-018 schema doesn't know about host_owner or
    schema_version="2"; the model's default is now v2 with host_owner per
    file. We validate against the new schema (specs/019-plugin-native-arch/
    contracts/manifest-json.schema.json) which has v1/v2 dual-read via oneOf.
    """
    jsonschema = pytest.importorskip("jsonschema")
    new_schema_path = REPO / "schemas" / "manifest-json.schema.json"
    schema = json.loads(new_schema_path.read_text(encoding="utf-8"))
    m = Manifest(
        plugin_version="1.0.0",
        schema_version="2",
        created_at=utc_now_iso(),
        last_upgrade_at=None,
        last_migrate_at=None,
        files=[DeployedFile(**_file(), host_owner="claude")],
    )
    jsonschema.validate(m.model_dump(mode="json"), schema)


def test_sha256_file(tmp_path: Path) -> None:
    target = tmp_path / "hello.txt"
    target.write_bytes(b"hello\n")
    # Pre-computed SHA-256 of b"hello\n"
    assert sha256_file(target) == (
        "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
    )
