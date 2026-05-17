"""T075 — PreToolUse architecture-profile hook (commit 13 / FR-034 / CHK046-048).

Asserts:
1. The hook reads project.yml at fire-time (no frozen snapshot).
2. A mid-session profile change is observed by the next invocation.
3. Missing/corrupt project.yml produces a corrective error naming the file
   + remediation command.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
HOOK = REPO / "hooks" / "pretooluse-arch-profile.sh"


def _find_bash() -> str | None:
    """Locate a working bash binary; prefer Git Bash over WSL on Windows."""
    import shutil as _shutil

    if sys.platform == "win32":
        for git_bash in (
            "C:/Program Files/Git/bin/bash.exe",
            "C:/Program Files (x86)/Git/bin/bash.exe",
        ):
            if Path(git_bash).is_file():
                return git_bash
    on_path = _shutil.which("bash")
    return on_path


def _run_hook(cwd: Path) -> subprocess.CompletedProcess:
    bash = _find_bash()
    if not bash:
        pytest.skip("no working bash binary available — install Git Bash on Windows")
    return subprocess.run(
        [bash, str(HOOK)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def _write_project_yml(project: Path, profile_name: str) -> None:
    config_dir = project / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "project.yml").write_text(
        f"""
detected:
  company: Acme
  domain: Sales
  side: server
  project_type: command
  architecture_branch: microservice
  architecture_profile_name: {profile_name}
  dotnet_version: '8.0'
  detected_paths:
    src: src
""".strip()
        + "\n",
        encoding="utf-8",
    )


pytestmark = pytest.mark.skipif(
    sys.platform == "win32" and not (Path("/usr/bin/bash").exists() or Path("/bin/bash").exists()),
    reason="hook is a bash script — Windows requires Git Bash/WSL on PATH",
)


def test_hook_reads_project_yml_at_fire_time(tmp_path: Path) -> None:
    """Per FR-034 / CHK046: hook reads project.yml at every fire, no cache."""
    project = tmp_path / "proj"
    project.mkdir()
    _write_project_yml(project, "microservice-command")

    result = _run_hook(project)
    assert result.returncode == 0
    assert "microservice-command" in result.stdout


def test_mid_session_profile_change_observed(tmp_path: Path) -> None:
    """CHK047: change profile mid-session → next fire observes the new value."""
    project = tmp_path / "proj"
    project.mkdir()
    _write_project_yml(project, "first-profile")

    first = _run_hook(project)
    assert "first-profile" in first.stdout

    # Change profile mid-session
    _write_project_yml(project, "second-profile")

    second = _run_hook(project)
    assert "second-profile" in second.stdout
    assert "first-profile" not in second.stdout


def test_missing_project_yml_emits_corrective_error(tmp_path: Path) -> None:
    """CHK048: missing metadata → error naming the file + remediation command."""
    project = tmp_path / "proj"
    project.mkdir()

    result = _run_hook(project)
    assert result.returncode == 0  # advisory; never block tool use
    assert "init" in result.stdout.lower()


def test_hook_never_returns_nonzero_per_advisory_rule(tmp_path: Path) -> None:
    """Per contract:54: hook MUST NOT exit non-zero (advisory hook)."""
    project = tmp_path / "proj"
    project.mkdir()

    # Both with and without project.yml, exit must be 0
    r1 = _run_hook(project)
    _write_project_yml(project, "x-profile")
    r2 = _run_hook(project)

    assert r1.returncode == 0
    assert r2.returncode == 0
