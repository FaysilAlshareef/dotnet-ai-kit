"""T044 — Codex CLI smoke fixture (commit 5 / FR-029 / CHK002).

Gated by `CODEX_SMOKE=1` env var + `codex` CLI on PATH. Verifies a Codex-
format skill is visible to Codex CLI's skill enumeration after the plugin
is installed.

Skipped locally — runs on nightly CI or PRs labelled `[smoke]`.
"""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        os.environ.get("CODEX_SMOKE") != "1",
        reason="requires CODEX_SMOKE=1",
    ),
    pytest.mark.skipif(
        shutil.which("codex") is None,
        reason="`codex` CLI not on PATH",
    ),
]


def test_codex_plugin_skill_listed() -> None:
    """A Codex-format skill from this plugin MUST appear in Codex's skill enumeration.

    Probes the Codex CLI for a known fixture skill name. Skills live under
    `skills/**/SKILL.md` in the plugin source; the Codex manifest at
    `.codex-plugin/plugin.json` declares `"skills": "./skills/"`.
    """
    # Use a stable fixture skill (e.g., workflow/verification-gate)
    fixture_name = "verification-gate"

    result = subprocess.run(
        ["codex", "plugin", "skills", "list", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, (
        f"`codex plugin skills list` exited {result.returncode}: {result.stderr}"
    )
    assert fixture_name in result.stdout, (
        f"Codex skill listing does not include the plugin's `{fixture_name}` skill. "
        f"Output: {result.stdout!r}"
    )
