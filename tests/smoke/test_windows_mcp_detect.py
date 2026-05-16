"""T066b — SC-014: Windows MCP detect path persists to config.yml."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = [pytest.mark.smoke, pytest.mark.windows_only]


@pytest.mark.skipif(sys.platform != "win32", reason="windows-only")
def test_codebase_memory_mcp_detected_on_windows(tmp_path: Path) -> None:
    if shutil.which("codebase-memory-mcp") is None:
        pytest.skip("codebase-memory-mcp not on PATH")

    from dotnet_ai_kit.cli import _record_mcp_state

    outcome = _record_mcp_state(tmp_path)
    state_path = tmp_path / ".dotnet-ai-kit" / "mcp-state.yml"
    assert state_path.is_file()
    persisted = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert persisted["mcp"]["codebase-memory-mcp"]["status"] in {
        "accepted",
        "below-minimum",
    }

    # Rerun should be idempotent.
    second = _record_mcp_state(tmp_path)
    assert second["status"] == outcome["status"]
