"""T030 — Claude Code smoke fixture (commit 4 / FR-029 / CHK001).

Gated by `CLAUDE_CODE_SMOKE=1` env var + `claude` CLI on PATH. Verifies a
Claude-native custom agent fixture is listed in `/agents` under the plugin
namespace after the plugin is installed.

This test is intentionally gated — it runs only on nightly CI or PRs
labelled `[smoke]` (per `.github/workflows/ci.yml`). Skipped locally.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        os.environ.get("CLAUDE_CODE_SMOKE") != "1",
        reason="requires CLAUDE_CODE_SMOKE=1",
    ),
    pytest.mark.skipif(
        shutil.which("claude") is None,
        reason="`claude` CLI not on PATH",
    ),
]


def test_plugin_namespace_agent_listed_in_agents_listing() -> None:
    """A Claude-native custom agent from this plugin MUST appear in `/agents`.

    Probes the Claude Code CLI for a known fixture agent name. The fixture is
    committed under `agents-source/` and rendered to `agents-claude/<name>.md`
    by `scripts/gen_agents_claude.py` (commit 4); the manifest declares the
    rendered path.
    """
    # Use the dotnet-architect fixture (always present per agents/).
    fixture_name = "dotnet-architect"

    result = subprocess.run(
        ["claude", "/agents", "list", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Allow CLI to print to stderr; main assertion is fixture present in output.
    assert result.returncode == 0, (
        f"`claude /agents list` exited {result.returncode}: {result.stderr}"
    )
    assert fixture_name in result.stdout, (
        f"Claude `/agents` listing does not include the plugin's `{fixture_name}` "
        f"agent. Output: {result.stdout!r}"
    )
