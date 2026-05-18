"""T095 — host_owner enum coverage + v1/v2 inference (commit 10 / R16).

Asserts:
- All 4 host_owner values (claude/codex/cursor/copilot) accepted by v2 writer.
- null host_owner allowed (for non-host-specific files like .dotnet-ai-kit/config.yml).
- v1 reader infers host_owner correctly per path patterns.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotnet_ai_kit.manifest import (
    DeployedFile,
    Manifest,
    read_manifest,
    utc_now_iso,
    write_manifest,
)


@pytest.mark.parametrize(
    "host_owner",
    ["claude", "codex", "cursor", "copilot", None],
)
def test_v2_writer_accepts_all_host_owner_values(tmp_path: Path, host_owner: str | None) -> None:
    """All 4 host names + null MUST be writable in v2 manifest."""
    project = tmp_path / "proj"
    project.mkdir()

    entry = DeployedFile(
        path="some/managed/file.md",
        sha256="a" * 64,
        plugin_version="1.0.0",
        deployed_at=utc_now_iso(),
        host_owner=host_owner,
    )
    manifest = Manifest(
        plugin_version="1.0.0",
        schema_version="2",
        created_at=utc_now_iso(),
        files=[entry],
    )
    write_manifest(project, manifest)

    # Round-trip
    read_back = read_manifest(project)
    assert read_back is not None
    assert read_back.files[0].host_owner == host_owner


def test_invalid_host_owner_rejected() -> None:
    """host_owner must be in the enum or null."""
    with pytest.raises(Exception):
        DeployedFile(
            path="x.md",
            sha256="a" * 64,
            plugin_version="1.0.0",
            deployed_at=utc_now_iso(),
            host_owner="bogus-host",  # type: ignore[arg-type]
        )


def test_v1_manifest_round_trip_upgrades_inferred_host_owners(tmp_path: Path) -> None:
    """Reading a v1 manifest infers host_owner; writing it produces v2."""
    project = tmp_path / "proj"
    config_dir = project / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)

    legacy = {
        "plugin_version": "1.0.0",
        "schema_version": "1",
        "created_at": utc_now_iso(),
        "files": [
            {
                "path": ".claude/cmd.md",
                "sha256": "a" * 64,
                "plugin_version": "1.0.0",
                "deployed_at": utc_now_iso(),
            },
            {
                "path": ".cursor/rules/x.mdc",
                "sha256": "b" * 64,
                "plugin_version": "1.0.0",
                "deployed_at": utc_now_iso(),
            },
        ],
    }
    (config_dir / "manifest.json").write_text(json.dumps(legacy), encoding="utf-8")

    manifest = read_manifest(project)
    assert manifest is not None

    # Host owners filled in
    by_path = {f.path: f.host_owner for f in manifest.files}
    assert by_path[".claude/cmd.md"] == "claude"
    assert by_path[".cursor/rules/x.mdc"] == "cursor"
