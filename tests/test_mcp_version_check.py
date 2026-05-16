"""T062 — FR-019 / FR-035: mcp_check.check_codebase_memory_mcp()."""

from __future__ import annotations

from unittest.mock import patch

from dotnet_ai_kit import mcp_check


class _Proc:
    def __init__(self, stdout: str = "", stderr: str = "") -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = 0


def test_parses_minimum_version_as_meets_minimum() -> None:
    with patch("dotnet_ai_kit.mcp_check.shutil.which", return_value="codebase-memory-mcp"):
        with patch(
            "dotnet_ai_kit.mcp_check.subprocess.run",
            return_value=_Proc(stdout="codebase-memory-mcp 0.6.1\n"),
        ):
            h = mcp_check.check_codebase_memory_mcp()
    assert h.present is True
    assert h.version == "0.6.1"
    assert h.meets_minimum is True


def test_below_minimum_does_not_meet() -> None:
    with patch("dotnet_ai_kit.mcp_check.shutil.which", return_value="codebase-memory-mcp"):
        with patch(
            "dotnet_ai_kit.mcp_check.subprocess.run",
            return_value=_Proc(stdout="codebase-memory-mcp 0.5.9\n"),
        ):
            h = mcp_check.check_codebase_memory_mcp()
    assert h.present is True
    assert h.version == "0.5.9"
    assert h.meets_minimum is False


def test_missing_binary_present_false() -> None:
    with patch("dotnet_ai_kit.mcp_check.shutil.which", return_value=None):
        h = mcp_check.check_codebase_memory_mcp()
    assert h.present is False
    assert h.version is None
    assert h.meets_minimum is False


def test_malformed_output_version_none() -> None:
    with patch("dotnet_ai_kit.mcp_check.shutil.which", return_value="codebase-memory-mcp"):
        with patch(
            "dotnet_ai_kit.mcp_check.subprocess.run",
            return_value=_Proc(stdout="hello world\n"),
        ):
            h = mcp_check.check_codebase_memory_mcp()
    assert h.present is True
    assert h.version is None
    assert h.meets_minimum is False
