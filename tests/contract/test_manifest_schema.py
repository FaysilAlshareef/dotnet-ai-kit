"""T097 — manifest schema v1/v2 dual-read (commit 10 / R16).

Asserts that `schemas/manifest-json.schema.json` accepts both v1 and v2
manifest shapes via the contract's `oneOf` declaration.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SCHEMA = json.loads((REPO / "schemas" / "manifest-json.schema.json").read_text(encoding="utf-8"))


def _v1_manifest() -> dict:
    return {
        "schema_version": "1",
        "plugin_version": "1.0.0",
        "created_at": "2026-05-17T00:00:00Z",
        "files": [
            {
                "path": ".claude/x.md",
                "sha256": "a" * 64,
                "plugin_version": "1.0.0",
                "deployed_at": "2026-05-17T00:00:00Z",
            }
        ],
    }


def _v2_manifest() -> dict:
    return {
        "schema_version": "2",
        "plugin_version": "1.0.0",
        "created_at": "2026-05-17T00:00:00Z",
        "last_migrate_at": "2026-05-17T00:00:00Z",
        "files": [
            {
                "path": ".claude/x.md",
                "sha256": "a" * 64,
                "plugin_version": "1.0.0",
                "deployed_at": "2026-05-17T00:00:00Z",
                "host_owner": "claude",
            }
        ],
    }


def test_manifest_schema_accepts_v1() -> None:
    """The schema MUST accept legacy v1 manifests (no host_owner per file)."""
    jsonschema.validate(_v1_manifest(), SCHEMA)


def test_manifest_schema_accepts_v2() -> None:
    """The schema MUST accept v2 manifests (host_owner per file)."""
    jsonschema.validate(_v2_manifest(), SCHEMA)


def test_manifest_schema_rejects_unknown_schema_version() -> None:
    """schema_version other than '1' or '2' MUST be rejected."""
    bad = _v2_manifest()
    bad["schema_version"] = "99"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, SCHEMA)


def test_manifest_schema_v2_host_owner_enum() -> None:
    """v2 host_owner MUST be one of {claude, codex, cursor, copilot} or null."""
    for value in ("claude", "codex", "cursor", "copilot", None):
        m = _v2_manifest()
        m["files"][0]["host_owner"] = value
        jsonschema.validate(m, SCHEMA)

    # Invalid value rejected
    m = _v2_manifest()
    m["files"][0]["host_owner"] = "not-a-host"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(m, SCHEMA)
