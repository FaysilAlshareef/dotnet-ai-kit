"""T091 — gating PR5 integration test: install + init + upgrade.

Asserts end-to-end behaviour through the actual ``python -m dotnet_ai_kit``
entry point. /cost (SC-001 token measurement) is captured by the maintainer
in measurements.md — this test verifies the *installation* and *upgrade*
plumbing that makes that capture possible.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "dotnet_ai_kit", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_init_then_upgrade_produces_valid_manifest(tmp_path: Path) -> None:
    # `__main__.py` is part of the package contract (FR-038: `python -m
    # dotnet_ai_kit` is the supported entry point). Failing-hard instead of
    # skipping protects against accidental removal of the entry point.
    assert (REPO / "src" / "dotnet_ai_kit" / "__main__.py").is_file(), (
        "package must ship `python -m dotnet_ai_kit` entry point"
    )

    project = tmp_path / "proj"
    project.mkdir()
    # Make this look like a .NET project so init's detection doesn't bail.
    (project / "Solution.sln").write_text("// stub", encoding="utf-8")

    init = _run(["init", str(project), "--ai", "claude", "--json"], cwd=REPO)
    assert init.returncode == 0, init.stdout + init.stderr

    manifest = project / ".dotnet-ai-kit" / "manifest.json"
    assert manifest.is_file(), f"init must produce a manifest; stdout={init.stdout!r}"

    data = json.loads(manifest.read_text(encoding="utf-8"))
    # Feature 019 / commit 10: writer always emits v2. The reader still
    # accepts v1 for backward compatibility, but newly-written manifests
    # ship with schema_version="2".
    assert data["schema_version"] in ("1", "2"), (
        f"schema_version must be '1' (legacy) or '2' (feature 019), got {data['schema_version']!r}"
    )
    assert "files" in data and data["files"], "manifest must list deployed files"

    # Pydantic + JSON Schema validation.
    from dotnet_ai_kit.manifest import Manifest

    Manifest.model_validate(data)
    try:
        import jsonschema

        # Feature 019: validate against the new feature-019 manifest schema
        # which has v1/v2 dual-read via oneOf. Falls back to legacy schema if
        # the new one isn't present.
        new_schema = REPO / "schemas" / "manifest-json.schema.json"
        legacy_schema = REPO / "specs" / "018-fix-token-burn" / "contracts" / "manifest.schema.json"
        schema_path = new_schema if new_schema.is_file() else legacy_schema
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)
    except ImportError:
        pass

    # Stale the version so upgrade actually runs.
    (project / ".dotnet-ai-kit" / "version.txt").write_text("0.0.1", encoding="utf-8")

    upgrade = _run(["upgrade"], cwd=project)
    assert upgrade.returncode == 0, (
        f"upgrade must succeed cleanly on a freshly initialized project; "
        f"got {upgrade.returncode}\nstdout={upgrade.stdout}\nstderr={upgrade.stderr}"
    )

    # Manifest must remain valid after upgrade.
    # Feature 019 / commit 10: writer always emits v2. Reader accepts both.
    data2 = json.loads(manifest.read_text(encoding="utf-8"))
    Manifest.model_validate(data2)
    assert data2["schema_version"] in ("1", "2")

    # Backup directory must have been created and rotated.
    backups = project / ".dotnet-ai-kit" / "backups" / "upgrade"
    assert backups.is_dir(), "atomic upgrade should leave a backup directory"
    snapshots = [p for p in backups.iterdir() if p.is_dir()]
    assert snapshots, "at least one snapshot expected after one upgrade"
