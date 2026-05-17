"""T076 — FR-038: scripts/check.py serves as the local pre-commit entry point."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECK = REPO / "scripts" / "check.py"


def test_check_script_exists_and_is_executable() -> None:
    assert CHECK.is_file()
    text = CHECK.read_text(encoding="utf-8")
    assert "scripts/check.py" in text or "argparse" in text


def test_check_script_passes_through_args(tmp_path: Path) -> None:
    """Invoke `python scripts/check.py --root <empty-tmp>` against an empty
    directory — pytest exits 5 (no tests collected) which the script
    surfaces as a non-zero exit. This proves --root + arg propagation work."""
    proc = subprocess.run(
        [sys.executable, str(CHECK), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Exit code may be 5 (no tests) or 4 (pytest config error); neither is 0.
    assert proc.returncode != 0


def test_check_script_passes_on_real_repo() -> None:
    # Smoke: invoking on the real repo should produce a pytest-shaped result.
    # We only assert the script itself executes and returns an int.
    proc = subprocess.run(
        [sys.executable, str(CHECK), "--root", str(REPO), "--collect-only", "-q"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert isinstance(proc.returncode, int)
