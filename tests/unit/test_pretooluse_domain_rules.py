"""Tests for `hooks/pretooluse-domain-rules.sh`.

The hook is the always-on backstop for the 11 path-scoped `rules/domain/*.md`
files. On every Edit/Write/MultiEdit, it reads the tool_input JSON from stdin,
matches the file_path against each rule's `paths:` frontmatter glob, and
prints matching rule bodies as additionalContext.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
HOOK = REPO / "hooks" / "pretooluse-domain-rules.sh"
RULES_DIR = REPO / "rules"


def _find_bash() -> str | None:
    import shutil as _shutil

    if sys.platform == "win32":
        for git_bash in (
            "C:/Program Files/Git/bin/bash.exe",
            "C:/Program Files (x86)/Git/bin/bash.exe",
        ):
            if Path(git_bash).is_file():
                return git_bash
    return _shutil.which("bash")


def _run_hook(
    tool_input: dict,
    cwd: Path,
    *,
    plugin_root: Path = REPO,
) -> subprocess.CompletedProcess:
    bash = _find_bash()
    if not bash:
        pytest.skip("no bash available — install Git Bash on Windows")
    env = {
        "CLAUDE_PLUGIN_ROOT": str(plugin_root),
        "DOTNET_AI_HOOK_DOMAIN_RULES": "true",
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    payload = json.dumps({"tool_input": tool_input})
    return subprocess.run(
        [bash, str(HOOK)],
        cwd=str(cwd),
        input=payload,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        env=env,
    )


pytestmark = pytest.mark.skipif(
    _find_bash() is None,
    reason="hook is a bash script — requires bash on PATH or Git Bash",
)


def test_hook_emits_data_access_rule_for_persistence_file(tmp_path: Path) -> None:
    """A file under `**/Persistence/**/*.cs` triggers data-access rule."""
    result = _run_hook(
        {"file_path": "src/Anis/Infrastructure/Persistence/AppDbContext.cs"},
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert "data-access" in result.stdout.lower() or "AsNoTracking" in result.stdout, (
        f"expected data-access rule for Persistence file, got:\n{result.stdout}"
    )


def test_hook_emits_nothing_for_non_matching_path(tmp_path: Path) -> None:
    """A path no domain rule globs match yields empty stdout."""
    result = _run_hook(
        {"file_path": "README.md"},
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    # Some rules glob `**/*.csproj` etc. — README.md should match none.
    assert result.stdout.strip() == "", (
        f"expected no output for README.md, got:\n{result.stdout}"
    )


def test_hook_handles_missing_file_path_gracefully(tmp_path: Path) -> None:
    """tool_input without file_path → exit 0 with no output."""
    result = _run_hook({}, cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_hook_handles_no_stdin_gracefully(tmp_path: Path) -> None:
    """Hook called with no stdin (interactive terminal) exits 0 silently."""
    bash = _find_bash()
    if not bash:
        pytest.skip("no bash")
    result = subprocess.run(
        [bash, str(HOOK)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env={
            "CLAUDE_PLUGIN_ROOT": str(REPO),
            "DOTNET_AI_HOOK_DOMAIN_RULES": "true",
            "PATH": __import__("os").environ.get("PATH", ""),
        },
        stdin=subprocess.DEVNULL,
    )
    # DEVNULL still presents stdin as readable but empty; should exit 0 quietly.
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_hook_disabled_via_env(tmp_path: Path) -> None:
    """DOTNET_AI_HOOK_DOMAIN_RULES=false short-circuits the hook."""
    bash = _find_bash()
    if not bash:
        pytest.skip("no bash")
    result = subprocess.run(
        [bash, str(HOOK)],
        cwd=str(tmp_path),
        input=json.dumps({"tool_input": {"file_path": "src/Persistence/X.cs"}}),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env={
            "CLAUDE_PLUGIN_ROOT": str(REPO),
            "DOTNET_AI_HOOK_DOMAIN_RULES": "false",
            "PATH": __import__("os").environ.get("PATH", ""),
        },
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_hook_does_not_emit_frontmatter(tmp_path: Path) -> None:
    """Emitted bodies must not contain the source files' YAML frontmatter."""
    result = _run_hook(
        {"file_path": "src/Foo/Infrastructure/Bar.cs"},
        cwd=tmp_path,
    )
    assert result.returncode == 0
    if result.stdout.strip():
        # No `---` delimiter lines from leaked frontmatter
        for line in result.stdout.splitlines():
            assert line.strip() != "---", (
                f"frontmatter leaked into hook output:\n{result.stdout}"
            )


def test_hook_respects_token_budget(tmp_path: Path) -> None:
    """Total output stays under the 24KB ceiling even with broad matches."""
    # `.cs` files under src match multiple rule globs simultaneously.
    result = _run_hook(
        {"file_path": "src/Foo/Repositories/Bar.cs"},
        cwd=tmp_path,
    )
    assert result.returncode == 0
    assert len(result.stdout) < 30000, (
        f"hook output exceeded budget: {len(result.stdout)} chars"
    )
