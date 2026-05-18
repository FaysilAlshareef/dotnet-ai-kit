"""T182 (commit 27, OOS-003): source-tree wrappers in `bin/` must work.

Per `bin/README.md` and OOS-003, the `bin/dotnet-ai` (POSIX) and
`bin/dotnet-ai.cmd` (Windows) wrappers MUST exit 0 on `--version` and
emit the same version string as the installed `dotnet-ai --version`.

The test is 3-OS aware: it skips the wrapper that doesn't apply to the
current platform.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
BIN_POSIX = REPO / "bin" / "dotnet-ai"
BIN_WIN = REPO / "bin" / "dotnet-ai.cmd"


def _module_version_string() -> str:
    """Get the version string by invoking the module directly."""
    result = subprocess.run(
        [sys.executable, "-m", "dotnet_ai_kit.cli", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.mark.skipif(os.name == "nt", reason="POSIX wrapper not applicable on Windows")
def test_bin_dotnet_ai_posix_version_matches(monkeypatch) -> None:
    """`bin/dotnet-ai --version` must exit 0 and match the canonical version."""
    if not BIN_POSIX.is_file():
        pytest.skip(f"POSIX wrapper not present at {BIN_POSIX}")
    # Ensure executable
    if not os.access(BIN_POSIX, os.X_OK):
        pytest.skip(f"POSIX wrapper not executable: {BIN_POSIX}")

    expected = _module_version_string()
    result = subprocess.run(
        [str(BIN_POSIX), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"bin/dotnet-ai --version exited {result.returncode}.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert result.stdout.strip() == expected, (
        f"bin/dotnet-ai --version mismatch.\n"
        f"  bin: {result.stdout.strip()!r}\n"
        f"  module: {expected!r}"
    )


@pytest.mark.skipif(os.name != "nt", reason="Windows wrapper only applicable on Windows")
def test_bin_dotnet_ai_cmd_version_matches() -> None:
    """`bin\\dotnet-ai.cmd --version` must exit 0 and match canonical version."""
    if not BIN_WIN.is_file():
        pytest.skip(f"Windows wrapper not present at {BIN_WIN}")

    expected = _module_version_string()
    result = subprocess.run(
        [str(BIN_WIN), "--version"],
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    assert result.returncode == 0, (
        f"bin/dotnet-ai.cmd --version exited {result.returncode}.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert result.stdout.strip() == expected, (
        f"bin/dotnet-ai.cmd --version mismatch.\n"
        f"  bin: {result.stdout.strip()!r}\n"
        f"  module: {expected!r}"
    )
