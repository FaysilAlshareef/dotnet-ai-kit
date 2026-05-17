"""T078 — SC-008: when codebase-memory-mcp is absent, exact fallback line emitted."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

EXACT = (
    "MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; "
    "falling back to csharp-ls + grep/read."
)


def test_fallback_line_emitted_when_mcp_absent(tmp_path: Path) -> None:
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")

    # Shadow `codebase-memory-mcp` with a no-op stub at the head of PATH so
    # the live MCP discovery in the session reads our shim instead of the
    # real binary. Wiping PATH entirely would also kill `csharp-ls`, git,
    # and other process dependencies the claude CLI relies on.
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    if sys.platform == "win32":
        shim = shim_dir / "codebase-memory-mcp.cmd"
        shim.write_text("@exit /b 127\n", encoding="utf-8")
    else:
        shim = shim_dir / "codebase-memory-mcp"
        shim.write_text("#!/usr/bin/env bash\nexit 127\n", encoding="utf-8")
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    env = {**os.environ, "PATH": f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"}

    proc = subprocess.run(
        ["claude", "--print", "/dai.analyze"],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    assert out.count(EXACT) == 1, f"expected exact fallback line once; got:\n{out}"
