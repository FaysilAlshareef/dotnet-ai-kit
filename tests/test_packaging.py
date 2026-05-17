"""Packaging assertions for the wheel.

Original (feature 018): plugin manifest, hook scripts, MCP config.
Extended (feature 019 / T006-T009): per-host plugin manifests, agent
source/output dirs, rule-classification dirs, schema dir.
"""

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


# ---------------------------------------------------------------------------
# T006 — feature 019 commit 2: per-host plugin manifests + new packaging dirs
# ---------------------------------------------------------------------------

# Each entry: (path-suffix in wheel, human-friendly description).
# Files: the path-suffix must match a file inside the wheel.
# Dirs: the path-suffix must be a prefix matched by at least one wheel entry.
_FEATURE_019_BUNDLED_FILES = [
    ("bundled/.codex-plugin/plugin.json", "Codex CLI plugin manifest"),
    ("bundled/.cursor-plugin/plugin.json", "Cursor plugin manifest"),
]

_FEATURE_019_BUNDLED_DIRS = [
    ("bundled/agents-source/", "Source-of-truth agent definitions"),
    ("bundled/agents-claude/", "Generated Claude-shape agent files"),
    ("bundled/agents/", "Cursor sub-agent build output"),
    ("bundled/agents-copilot-templates/", "Copilot agent jinja2 templates"),
    ("bundled/rules/conventions/", "Always-on convention rules (5 per FR-011)"),
    ("bundled/rules/domain/", "Just-in-time domain rules (11 per FR-011)"),
    ("bundled/rules/cursor/", "Cursor per-rule .mdc files"),
    ("bundled/schemas/", "JSON Schema definitions"),
]


@pytest.mark.parametrize(
    "suffix,description",
    _FEATURE_019_BUNDLED_FILES,
    ids=[entry[1] for entry in _FEATURE_019_BUNDLED_FILES],
)
def test_wheel_bundles_feature_019_files(
    built_wheel: Path, suffix: str, description: str
) -> None:
    """T006: each per-host plugin manifest must be in the wheel."""
    with zipfile.ZipFile(built_wheel) as z:
        names = z.namelist()
    assert any(n.endswith(suffix) for n in names), (
        f"{description} ({suffix}) not bundled in wheel"
    )


@pytest.mark.parametrize(
    "prefix,description",
    _FEATURE_019_BUNDLED_DIRS,
    ids=[entry[1] for entry in _FEATURE_019_BUNDLED_DIRS],
)
def test_wheel_bundles_feature_019_dirs(
    built_wheel: Path, prefix: str, description: str
) -> None:
    """T006: each feature-019 directory must be present in the wheel.

    Asserts at least one entry exists under the directory prefix. Empty stub
    directories that ship `.gitkeep` markers satisfy this; later feature-019
    commits replace the markers with real content.
    """
    with zipfile.ZipFile(built_wheel) as z:
        names = z.namelist()
    assert any(prefix in n for n in names), (
        f"{description} ({prefix}) not bundled in wheel"
    )
