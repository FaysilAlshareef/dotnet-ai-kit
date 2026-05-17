"""T053 — Cursor fixture-decision consistency (commit 6 / CHK052 area).

Per `contracts/cursor-fixture-decision.contract.md`: agents-field presence
in `.cursor-plugin/plugin.json` MUST be consistent with spec language
(A-005/SC-008/OOS-005) AND with release-notes language.

This test uses the embedded fixture sets under
`tests/fixtures/cursor_fixture_{pass,fail}/` so it does NOT depend on the
real release-notes file existing yet (the real release-notes file is
written in commit 15). The live-artifact version of this test is T125a
in commit 15.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "branch",
    ["pass", "fail"],
)
def test_cursor_fixture_consistency(branch: str) -> None:
    """Per branch fixture: manifest `agents` presence ↔ spec ↔ release notes."""
    base = FIXTURES / f"cursor_fixture_{branch}"
    assert base.is_dir(), f"missing fixture set: {base}"

    manifest = json.loads(_read_text(base / ".cursor-plugin" / "plugin.json"))
    spec_text = _read_text(base / "spec.md")
    release_text = _read_text(base / "release-notes.md")

    has_agents = "agents" in manifest

    if branch == "pass":
        # PASS branch: manifest declares `agents`, spec says "passed",
        # release notes say "shipped".
        assert has_agents, (
            f"PASS branch: manifest must declare `agents` field, got {list(manifest.keys())}"
        )
        # Spec language consistent with pass outcome
        assert "passed" in spec_text.lower() or "ships" in spec_text.lower(), (
            "PASS branch: spec A-005 must mention 'passed' or 'ships'"
        )
        # Release notes confirm shipping
        assert "shipped" in release_text.lower(), (
            "PASS branch: release notes must state 'Cursor sub-agent generation shipped'"
        )
        # Release notes MUST NOT say "deferred" in pass branch
        assert "deferred" not in release_text.lower(), (
            "PASS branch: release notes must NOT mention deferral"
        )

    elif branch == "fail":
        # FAIL branch: manifest MUST NOT declare `agents`; spec says "failed/deferred";
        # release notes say "deferred".
        assert not has_agents, (
            f"FAIL branch: manifest must NOT declare `agents` field. "
            f"cursor-fixture-decision.contract.md fail-path violated: {manifest}"
        )
        assert "failed" in spec_text.lower() or "deferred" in spec_text.lower(), (
            "FAIL branch: spec A-005 must mention 'failed' or 'deferred'"
        )
        assert "deferred" in release_text.lower(), (
            "FAIL branch: release notes must state 'deferred to v1.1'"
        )
        assert "shipped" not in release_text.lower(), (
            "FAIL branch: release notes must NOT mention shipping"
        )
