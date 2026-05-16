"""T012 — FR-002 / FR-003 / SC-004 / SC-005: blocking hooks return exit 2."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PRE_BASH = REPO / "hooks" / "pre-bash-guard.sh"
PRE_COMMIT_LINT = REPO / "hooks" / "pre-commit-lint.sh"


def _resolve_bash() -> str | None:
    """Find a real bash. On Windows the bare `bash` on PATH is usually the
    WSL relay, which cannot exec `/bin/bash`; prefer the MSYS / git-bash
    binary instead."""
    if sys.platform == "win32":
        for candidate in (
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
            r"C:\msys64\usr\bin\bash.exe",
        ):
            if Path(candidate).is_file():
                return candidate
    return shutil.which("bash")


BASH = _resolve_bash()
needs_bash = pytest.mark.skipif(BASH is None, reason="bash (msys/git-bash) unavailable")


def _run_hook(script: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    """Run the hook via the stdin JSON protocol Claude Code actually uses.

    No $1 argv fallback: the hook is responsible for picking a real python
    interpreter (smoke-tested in the script) and parsing stdin itself.
    """
    return subprocess.run(
        [BASH, str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )


@needs_bash
def test_pre_bash_guard_blocks_rm_rf_with_exit_2() -> None:
    payload = {"tool_input": {"command": "rm -rf /"}}
    proc = _run_hook(PRE_BASH, payload)
    assert proc.returncode == 2, proc.stdout + proc.stderr


@needs_bash
def test_pre_bash_guard_allows_safe_command() -> None:
    payload = {"tool_input": {"command": "ls -la"}}
    proc = _run_hook(PRE_BASH, payload)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@needs_bash
def test_pre_commit_lint_blocks_on_format_failure(tmp_path: Path) -> None:
    """Simulate a `dotnet format --verify-no-changes` failure. The hook must
    exit 2, not exit 1.

    We stub `dotnet` on PATH so we don't depend on a real installation.
    """
    stub_dir = tmp_path / "stub_bin"
    stub_dir.mkdir()
    stub = stub_dir / "dotnet"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$1\" == 'format' ]] && [[ \"$2\" == '--verify-no-changes' ]]; then\n"
        "  echo 'formatting issues found'\n"
        "  exit 1\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)

    (tmp_path / "stub.csproj").write_text("<Project/>", encoding="utf-8")

    env_path = f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    proc = subprocess.run(
        [BASH, str(PRE_COMMIT_LINT)],
        input=json.dumps({"tool_input": {"command": "git commit -m test"}}),
        cwd=str(tmp_path),
        env={**os.environ, "PATH": env_path},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
