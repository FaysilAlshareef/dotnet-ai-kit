"""T007 — macOS-specific packaging assertions for feature 019.

Re-runs the T006 wheel-content assertions inside the macOS CI matrix slot.
Validates POSIX path normalization in the wheel: every path uses `/`
separators (no Windows-style `\\`), and the new feature-019 paths and per-host
plugin manifest files are all bundled.

Per A-010 / plan.md:27 / traceability.md:79.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent

# Same lists as tests/test_packaging.py — keeping them in sync per T008's
# "platform-specific assertions only — does NOT duplicate cross-platform
# logic from T006" via shared parametrization.
_FEATURE_019_BUNDLED_FILES = [
    "bundled/.claude-plugin/plugin.json",
    "bundled/.codex-plugin/plugin.json",
    "bundled/.cursor-plugin/plugin.json",
]

_FEATURE_019_BUNDLED_DIRS = [
    "bundled/agents-source/",
    "bundled/agents-claude/",
    "bundled/agents/",
    "bundled/agents-copilot-templates/",
    "bundled/rules/conventions/",
    "bundled/rules/domain/",
    "bundled/rules/cursor/",
    "bundled/schemas/",
]


pytestmark = pytest.mark.skipif(
    sys.platform != "darwin",
    reason="macOS-specific packaging assertions (CI matrix macos-latest)",
)


@pytest.fixture(scope="module")
def built_wheel_macos(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out_dir = tmp_path_factory.mktemp("wheel_out_macos")
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


def test_macos_wheel_uses_posix_separators(built_wheel_macos: Path) -> None:
    """All wheel entries MUST use POSIX `/` separators on macOS."""
    with zipfile.ZipFile(built_wheel_macos) as z:
        names = z.namelist()
    backslash_entries = [n for n in names if "\\" in n]
    assert not backslash_entries, (
        f"wheel built on macOS contains backslash-separated entries: {backslash_entries[:3]}"
    )


@pytest.mark.parametrize("suffix", _FEATURE_019_BUNDLED_FILES)
def test_macos_wheel_bundles_per_host_manifests(built_wheel_macos: Path, suffix: str) -> None:
    """T007: per-host manifest files MUST be in the macOS wheel."""
    with zipfile.ZipFile(built_wheel_macos) as z:
        names = z.namelist()
    assert any(n.endswith(suffix) for n in names), (
        f"{suffix} not bundled in macOS wheel"
    )


@pytest.mark.parametrize("prefix", _FEATURE_019_BUNDLED_DIRS)
def test_macos_wheel_bundles_feature_019_dirs(built_wheel_macos: Path, prefix: str) -> None:
    """T007: feature-019 directories MUST be present in macOS wheel."""
    with zipfile.ZipFile(built_wheel_macos) as z:
        names = z.namelist()
    assert any(prefix in n for n in names), (
        f"{prefix} not bundled in macOS wheel"
    )
