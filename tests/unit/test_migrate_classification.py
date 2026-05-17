"""T092 — migrate file classification by SHA-256 (commit 10 / FR-020 / CHK020).

Asserts that `classify_file()` correctly classifies each previously-managed
file as `clean`, `user-modified`, or `missing` based on content hash.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotnet_ai_kit.manifest import (
    DeployedFile,
    Manifest,
    classify_file,
    infer_host_owner,
    sha256_file,
    utc_now_iso,
    write_manifest,
)


def _make_file(project: Path, relpath: str, content: str = "x") -> Path:
    p = project / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_classify_file_clean(tmp_path: Path) -> None:
    """File on disk with matching sha256 → 'clean'."""
    project = tmp_path / "proj"
    project.mkdir()
    f = _make_file(project, ".claude/cmd.md", "hello")
    entry = DeployedFile(
        path=".claude/cmd.md",
        sha256=sha256_file(f),
        plugin_version="1.0.0",
        deployed_at=utc_now_iso(),
        host_owner="claude",
    )
    assert classify_file(project, entry) == "clean"


def test_classify_file_user_modified(tmp_path: Path) -> None:
    """File on disk with different sha256 → 'user-modified'."""
    project = tmp_path / "proj"
    project.mkdir()
    _make_file(project, ".claude/cmd.md", "modified content")
    entry = DeployedFile(
        path=".claude/cmd.md",
        sha256="a" * 64,  # not the actual hash
        plugin_version="1.0.0",
        deployed_at=utc_now_iso(),
        host_owner="claude",
    )
    assert classify_file(project, entry) == "user-modified"


def test_classify_file_missing(tmp_path: Path) -> None:
    """File not on disk → 'missing'."""
    project = tmp_path / "proj"
    project.mkdir()
    entry = DeployedFile(
        path=".claude/nonexistent.md",
        sha256="a" * 64,
        plugin_version="1.0.0",
        deployed_at=utc_now_iso(),
        host_owner="claude",
    )
    assert classify_file(project, entry) == "missing"


@pytest.mark.parametrize(
    "path,expected",
    [
        (".claude/commands/dai.md", "claude"),
        (".claude/skills/x/SKILL.md", "claude"),
        (".codex/foo", "codex"),
        (".cursor/rules/x.mdc", "cursor"),
        (".github/agents/my.agent.md", "copilot"),
        (".github/copilot-instructions.md", "copilot"),
        (".github/instructions/api.instructions.md", "copilot"),
        ("src/foo.cs", None),
        (".dotnet-ai-kit/config.yml", None),
        (".github/other-file.md", None),
    ],
)
def test_infer_host_owner_per_path_pattern(path: str, expected: str | None) -> None:
    """`infer_host_owner` MUST match the R16 mapping table."""
    assert infer_host_owner(path) == expected


def test_legacy_v1_manifest_read_with_inferred_host_owner(tmp_path: Path) -> None:
    """Legacy v1 manifest reads correctly, with host_owner inferred per R16."""
    project = tmp_path / "proj"
    config_dir = project / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)

    legacy_payload = {
        "plugin_version": "1.0.0",
        "schema_version": "1",
        "created_at": utc_now_iso(),
        "files": [
            {
                "path": ".claude/commands/x.md",
                "sha256": "a" * 64,
                "plugin_version": "1.0.0",
                "deployed_at": utc_now_iso(),
            },
            {
                "path": ".github/copilot-instructions.md",
                "sha256": "b" * 64,
                "plugin_version": "1.0.0",
                "deployed_at": utc_now_iso(),
            },
        ],
    }
    (config_dir / "manifest.json").write_text(
        json.dumps(legacy_payload), encoding="utf-8"
    )

    from dotnet_ai_kit.manifest import read_manifest

    manifest = read_manifest(project)
    assert manifest is not None
    assert manifest.schema_version == "1"
    # host_owner inferred for legacy entries
    by_path = {f.path: f.host_owner for f in manifest.files}
    assert by_path[".claude/commands/x.md"] == "claude"
    assert by_path[".github/copilot-instructions.md"] == "copilot"
