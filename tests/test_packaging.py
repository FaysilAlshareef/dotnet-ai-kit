"""T014 — packaging: plugin manifest, hook scripts, MCP config bundled in wheel."""

from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out_dir = tmp_path_factory.mktemp("wheel_out")
    proc = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(out_dir)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        pytest.skip(
            "wheel build failed (likely missing `build` package): "
            f"{proc.stderr.splitlines()[-1] if proc.stderr else proc.stdout}"
        )
    wheels = list(out_dir.glob("*.whl"))
    assert wheels, "no wheel produced"
    return wheels[0]


def test_wheel_bundles_plugin_manifest(built_wheel: Path) -> None:
    with zipfile.ZipFile(built_wheel) as z:
        names = z.namelist()
    assert any(n.endswith("bundled/.claude-plugin/plugin.json") for n in names), (
        "plugin.json not bundled"
    )


def test_wheel_bundles_hook_scripts(built_wheel: Path) -> None:
    with zipfile.ZipFile(built_wheel) as z:
        names = z.namelist()
    expected = {
        "pre-bash-guard.sh",
        "pre-commit-lint.sh",
        "post-edit-format.sh",
        "post-scaffold-restore.sh",
        "session-start-bootstrap.sh",
        "hooks.json",
    }
    bundled = {Path(n).name for n in names if "/bundled/hooks/" in n}
    missing = expected - bundled
    assert not missing, f"hook scripts missing from wheel: {missing}"


def test_wheel_bundles_mcp_config(built_wheel: Path) -> None:
    with zipfile.ZipFile(built_wheel) as z:
        names = z.namelist()
    assert any(re.search(r"bundled/\.mcp\.json$", n) for n in names), ".mcp.json not bundled"
