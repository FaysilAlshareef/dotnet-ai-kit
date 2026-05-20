"""Extended tests for mcp_check.py — covers the missing-file fallback (line 31),
OSError path (lines 38-39), and the absent-binary path.
"""

from __future__ import annotations

from unittest.mock import patch

from dotnet_ai_kit.mcp_check import (
    _read_min_version_from_mcp_json,
    check_codebase_memory_mcp,
)


class TestReadMinVersionFromMcpJson:
    def test_returns_fallback_when_file_missing(self) -> None:
        """Covers line 31 — mcp_path not found → returns a valid semver string."""
        from dotnet_ai_kit.mcp_check import _FALLBACK_MIN_VERSION

        # The module-level constant is read at import time; verify it's valid semver.
        assert _FALLBACK_MIN_VERSION == "0.6.1"
        # Direct call with a patched path that doesn't exist returns the fallback.
        from pathlib import Path as _Path

        with patch.object(_Path, "is_file", return_value=False):
            result = _read_min_version_from_mcp_json()
        assert result == "0.6.1"

    def test_returns_fallback_on_oserror(self, tmp_path) -> None:
        """Covers lines 38-39 — OSError during file read → fallback."""
        from pathlib import Path as _Path

        bad_path = tmp_path / ".mcp.json"
        bad_path.write_text("{invalid json}", encoding="utf-8")

        with (
            patch.object(_Path, "is_file", return_value=True),
            patch.object(_Path, "read_text", side_effect=OSError("permission denied")),
        ):
            result = _read_min_version_from_mcp_json()
        assert result == "0.6.1"

    def test_returns_fallback_on_invalid_json(self, tmp_path) -> None:
        """Covers the json.JSONDecodeError branch (lines 38-39)."""
        from pathlib import Path as _Path

        with (
            patch.object(_Path, "is_file", return_value=True),
            patch.object(_Path, "read_text", return_value="{not valid json}"),
        ):
            result = _read_min_version_from_mcp_json()
        assert result == "0.6.1"


class TestCheckCodebaseMemoryMcp:
    def test_binary_not_on_path(self) -> None:
        with patch("dotnet_ai_kit.mcp_check.shutil.which", return_value=None):
            health = check_codebase_memory_mcp()
        assert not health.present
        assert not health.meets_minimum
        assert health.error == "binary not on PATH"

    def test_binary_present_meets_minimum(self) -> None:
        from unittest.mock import MagicMock

        mock_proc = MagicMock()
        mock_proc.stdout = "codebase-memory-mcp 0.7.0\n"
        mock_proc.stderr = ""
        with (
            patch(
                "dotnet_ai_kit.mcp_check.shutil.which",
                return_value="/usr/bin/codebase-memory-mcp",
            ),
            patch("dotnet_ai_kit.mcp_check.subprocess.run", return_value=mock_proc),
        ):
            health = check_codebase_memory_mcp()
        assert health.present
        assert health.meets_minimum
        assert health.version == "0.7.0"

    def test_binary_present_below_minimum(self) -> None:
        from unittest.mock import MagicMock

        mock_proc = MagicMock()
        mock_proc.stdout = "codebase-memory-mcp 0.5.0\n"
        mock_proc.stderr = ""
        with (
            patch(
                "dotnet_ai_kit.mcp_check.shutil.which",
                return_value="/usr/bin/codebase-memory-mcp",
            ),
            patch("dotnet_ai_kit.mcp_check.subprocess.run", return_value=mock_proc),
        ):
            health = check_codebase_memory_mcp()
        assert health.present
        assert not health.meets_minimum

    def test_unparseable_version_output(self) -> None:
        from unittest.mock import MagicMock

        mock_proc = MagicMock()
        mock_proc.stdout = "no version here\n"
        mock_proc.stderr = ""
        with (
            patch(
                "dotnet_ai_kit.mcp_check.shutil.which",
                return_value="/usr/bin/codebase-memory-mcp",
            ),
            patch("dotnet_ai_kit.mcp_check.subprocess.run", return_value=mock_proc),
        ):
            health = check_codebase_memory_mcp()
        assert health.present
        assert not health.meets_minimum
        assert health.error is not None
