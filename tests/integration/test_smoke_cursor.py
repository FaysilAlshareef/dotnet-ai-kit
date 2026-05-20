"""T051 — Cursor sub-agent fixture smoke test (commit 6 / FR-029 / A-005 / CHK003).

Gated by `CURSOR_SMOKE=1` env var + `cursor` CLI on PATH. Verifies the
single Cursor sub-agent fixture at `agents/dotnet-ai-architect.md` is
listed by Cursor per the A-005 spike.

If this test PASSES in CI: full Cursor sub-agent generation ships
(release notes line: "Cursor sub-agent generation shipped").
If this test FAILS in CI: T061 fail-path executes per
`contracts/cursor-fixture-decision.contract.md`.

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
        os.environ.get("CURSOR_SMOKE") != "1",
        reason="requires CURSOR_SMOKE=1",
    ),
    pytest.mark.skipif(
        shutil.which("cursor") is None,
        reason="`cursor` CLI not on PATH",
    ),
]

FIXTURE_NAME = "dotnet-ai-architect"


def test_cursor_subagent_listed() -> None:
    """The fixture sub-agent MUST appear in Cursor's sub-agent listing.

    Probes the Cursor CLI for the known fixture. The fixture is committed
    to `agents/<fixture>.md` with Cursor's verified frontmatter shape
    (name, description, model, readonly).
    """
    result = subprocess.run(
        ["cursor", "agents", "list", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, (
        f"`cursor agents list` exited {result.returncode}: {result.stderr}"
    )
    assert FIXTURE_NAME in result.stdout, (
        f"Cursor sub-agent listing does not include the plugin's `{FIXTURE_NAME}` "
        f"fixture. Output: {result.stdout!r}. "
        f"Per cursor-fixture-decision.contract.md fail-path: T061 executes."
    )
