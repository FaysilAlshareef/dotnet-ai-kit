"""Tests for version_check.py — covers lines 19-22 (_parse) and 34-47
(check_claude_code_version subprocess paths).
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from dotnet_ai_kit.version_check import _parse, check_claude_code_version


class TestParse:
    def test_valid_version_string(self) -> None:
        result = _parse("claude 2.1.85")
        assert result == (2, 1, 85)

    def test_bare_version(self) -> None:
        result = _parse("3.0.0")
        assert result == (3, 0, 0)

    def test_no_match_returns_none(self) -> None:
        assert _parse("not a version") is None

    def test_empty_string_returns_none(self) -> None:
        assert _parse("") is None


class TestCheckClaudeCodeVersion:
    def test_claude_not_on_path_returns_false(self) -> None:
        with patch("dotnet_ai_kit.version_check.shutil.which", return_value=None):
            meets, version = check_claude_code_version()
        assert meets is False
        assert version is None

    def test_meets_minimum_version(self) -> None:
        mock_proc = MagicMock()
        mock_proc.stdout = "claude 2.2.0\n"
        mock_proc.stderr = ""
        with (
            patch("dotnet_ai_kit.version_check.shutil.which", return_value="/usr/bin/claude"),
            patch("dotnet_ai_kit.version_check.subprocess.run", return_value=mock_proc),
        ):
            meets, version = check_claude_code_version()
        assert meets is True
        assert version == "2.2.0"

    def test_below_minimum_version(self) -> None:
        mock_proc = MagicMock()
        mock_proc.stdout = "claude 2.0.0\n"
        mock_proc.stderr = ""
        with (
            patch("dotnet_ai_kit.version_check.shutil.which", return_value="/usr/bin/claude"),
            patch("dotnet_ai_kit.version_check.subprocess.run", return_value=mock_proc),
        ):
            meets, version = check_claude_code_version()
        assert meets is False
        assert version == "2.0.0"

    def test_timeout_returns_false(self) -> None:
        with (
            patch("dotnet_ai_kit.version_check.shutil.which", return_value="/usr/bin/claude"),
            patch(
                "dotnet_ai_kit.version_check.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5),
            ),
        ):
            meets, version = check_claude_code_version()
        assert meets is False
        assert version is None

    def test_oserror_returns_false(self) -> None:
        with (
            patch("dotnet_ai_kit.version_check.shutil.which", return_value="/usr/bin/claude"),
            patch(
                "dotnet_ai_kit.version_check.subprocess.run",
                side_effect=OSError("spawn failed"),
            ),
        ):
            meets, version = check_claude_code_version()
        assert meets is False
        assert version is None

    def test_unparseable_output_returns_false(self) -> None:
        mock_proc = MagicMock()
        mock_proc.stdout = "unexpected output\n"
        mock_proc.stderr = ""
        with (
            patch("dotnet_ai_kit.version_check.shutil.which", return_value="/usr/bin/claude"),
            patch("dotnet_ai_kit.version_check.subprocess.run", return_value=mock_proc),
        ):
            meets, version = check_claude_code_version()
        assert meets is False
        assert version is None
