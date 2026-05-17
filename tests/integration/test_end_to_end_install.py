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
    assert data["schema_version"] == "1"
    assert "files" in data and data["files"], "manifest must list deployed files"

    # Pydantic + JSON Schema validation.
    from dotnet_ai_kit.manifest import Manifest

    Manifest.model_validate(data)
    try:
        import jsonschema

        schema = json.loads(
            (
                REPO / "specs" / "018-fix-token-burn" / "contracts" / "manifest.schema.json"
            ).read_text(encoding="utf-8")
        )
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
    data2 = json.loads(manifest.read_text(encoding="utf-8"))
    Manifest.model_validate(data2)
    assert data2["schema_version"] == "1"

    # Backup directory must have been created and rotated.
    backups = project / ".dotnet-ai-kit" / "backups" / "upgrade"
    assert backups.is_dir(), "atomic upgrade should leave a backup directory"
    snapshots = [p for p in backups.iterdir() if p.is_dir()]
    assert snapshots, "at least one snapshot expected after one upgrade"
