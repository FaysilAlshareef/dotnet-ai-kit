"""T196 (commit 29, F6 / content-quality review O2): plugin-manifest path
references MUST resolve on disk.

Asserts every `agents[]`, `skills[]`, `commands[]`, `rules` path declared in
`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and
`.cursor-plugin/plugin.json` resolves to an existing file or directory in
the source tree. Catches the F6 class of issues automatically.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent

MANIFESTS = (
    REPO / ".claude-plugin" / "plugin.json",
    REPO / ".codex-plugin" / "plugin.json",
    REPO / ".cursor-plugin" / "plugin.json",
)


@pytest.mark.parametrize("manifest_path", MANIFESTS, ids=lambda p: p.parent.name)
def test_plugin_manifest_paths_resolve(manifest_path: Path) -> None:
    """Every scalar path AND every entry in array path fields MUST exist."""
    if not manifest_path.is_file():
        pytest.skip(f"manifest not present: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plugin_root = manifest_path.parent  # e.g. .claude-plugin/

    # Fields whose value is a scalar relative path like "./skills/"
    SCALAR_PATH_FIELDS = ("skills", "rules", "agents", "commands", "hooks", "mcpServers")
    # Fields whose value is an array of relative paths
    ARRAY_PATH_FIELDS = ("agents_array", "skills_array", "commands_array")

    missing: list[str] = []

    for field in SCALAR_PATH_FIELDS:
        if field not in manifest:
            continue
        rel = manifest[field]
        if not isinstance(rel, str) or not rel.startswith("./"):
            continue
        # Cursor's `./agents/` etc. resolve relative to the plugin manifest dir,
        # but the actual files live at the repo root (the plugin is mounted at
        # repo root in real installs). Resolve both options.
        candidates = [
            (plugin_root / rel).resolve(),
            (REPO / rel[2:]).resolve() if rel.startswith("./") else (REPO / rel).resolve(),
        ]
        if not any(c.exists() for c in candidates):
            missing.append(f"{field}={rel} (tried: {[str(c.relative_to(REPO) if c.is_relative_to(REPO) else c) for c in candidates]})")

    for field in ARRAY_PATH_FIELDS:
        canonical = field.replace("_array", "")
        if canonical not in manifest:
            continue
        value = manifest[canonical]
        if not isinstance(value, list):
            continue
        for rel in value:
            if not isinstance(rel, str):
                continue
            candidates = [
                (plugin_root / rel).resolve(),
                (REPO / rel[2:]).resolve() if rel.startswith("./") else (REPO / rel).resolve(),
            ]
            if not any(c.exists() for c in candidates):
                missing.append(f"{canonical}[]={rel}")

    assert not missing, (
        f"F6 violation: manifest {manifest_path.relative_to(REPO)} declares "
        f"paths that don't resolve on disk:\n  - " + "\n  - ".join(missing)
    )
