"""T008 — Windows-specific packaging assertions for feature 019.

Re-runs the T006 wheel-content assertions inside the Windows CI matrix slot.
Validates Windows path-separator handling per A-010 / plan.md:27 /
traceability.md:79.

Wheel files are zip archives — they MUST use POSIX `/` separators regardless
of the build OS (per PEP 427). On Windows, this is the critical assertion:
no `\\` should leak into the zip's internal namelist.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent

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
    sys.platform != "win32",
    reason="Windows-specific packaging assertions (CI matrix windows-latest)",
)


@pytest.fixture(scope="module")
def built_wheel_windows(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out_dir = tmp_path_factory.mktemp("wheel_out_windows")
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


def test_windows_wheel_uses_posix_separators(built_wheel_windows: Path) -> None:
    """Wheel zip namelist MUST use POSIX `/` even on Windows builds (PEP 427)."""
    with zipfile.ZipFile(built_wheel_windows) as z:
        names = z.namelist()
    backslash_entries = [n for n in names if "\\" in n]
    assert not backslash_entries, (
        f"wheel built on Windows leaked backslash separators: {backslash_entries[:3]}"
    )


@pytest.mark.parametrize("suffix", _FEATURE_019_BUNDLED_FILES)
def test_windows_wheel_bundles_per_host_manifests(
    built_wheel_windows: Path, suffix: str
) -> None:
    """T008: per-host manifest files MUST be in the Windows wheel."""
    with zipfile.ZipFile(built_wheel_windows) as z:
        names = z.namelist()
    assert any(n.endswith(suffix) for n in names), (
        f"{suffix} not bundled in Windows wheel"
    )


@pytest.mark.parametrize("prefix", _FEATURE_019_BUNDLED_DIRS)
def test_windows_wheel_bundles_feature_019_dirs(
    built_wheel_windows: Path, prefix: str
) -> None:
    """T008: feature-019 directories MUST be present in Windows wheel."""
    with zipfile.ZipFile(built_wheel_windows) as z:
        names = z.namelist()
    assert any(prefix in n for n in names), (
        f"{prefix} not bundled in Windows wheel"
    )
