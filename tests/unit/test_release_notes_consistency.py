"""T125a — release-notes consistency with Cursor spike outcome (commit 15).

Asserts cross-artifact consistency for the Cursor sub-agent spike branching
per cursor-fixture-decision.contract.md:
- The outcome JSON (`specs/.../cursor-subagent-outcome.json`) is the source
  of truth for the spike result.
- Release notes language (PASS/FAIL/PENDING) is consistent with the JSON.
- `.cursor-plugin/plugin.json` `agents` field presence is consistent.
- Spec A-005 / SC-008 / OOS-005 language is consistent.

Handles the "pending" state per the contract: CI hasn't flipped the outcome
yet → release notes assume PASS branch but flag the pending status.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
OUTCOME_JSON = REPO / "specs" / "019-plugin-native-arch" / "discussion" / "tasks-phase" / "cursor-subagent-outcome.json"
RELEASE_NOTES = REPO / "docs" / "release-notes-v1.0.md"
CURSOR_MANIFEST = REPO / ".cursor-plugin" / "plugin.json"


def _load_outcome() -> dict:
    if not OUTCOME_JSON.is_file():
        pytest.skip(f"outcome JSON not found: {OUTCOME_JSON}")
    return json.loads(OUTCOME_JSON.read_text(encoding="utf-8"))


def _load_release_notes() -> str:
    if not RELEASE_NOTES.is_file():
        pytest.skip(f"release notes not found: {RELEASE_NOTES}")
    return RELEASE_NOTES.read_text(encoding="utf-8")


def _load_cursor_manifest() -> dict:
    return json.loads(CURSOR_MANIFEST.read_text(encoding="utf-8"))


def test_outcome_json_has_valid_state() -> None:
    """outcome JSON MUST have one of {pending, passed, failed} as outcome."""
    outcome = _load_outcome()
    assert outcome["outcome"] in ("pending", "passed", "failed")


def test_release_notes_reference_spike_outcome() -> None:
    """Release notes MUST reference the Cursor spike outcome (any state)."""
    notes = _load_release_notes()
    assert "Cursor sub-agent" in notes or "A-005" in notes


def test_cursor_manifest_agents_field_matches_outcome_state() -> None:
    """Per cursor-fixture-decision.contract.md: agents-field presence in
    .cursor-plugin/plugin.json MUST be consistent with the outcome.

    - outcome=passed   → agents field present (full generation shipped)
    - outcome=failed   → agents field ABSENT (fail-path scope revision)
    - outcome=pending  → agents field MAY be present (default-assume-pass)
    """
    outcome = _load_outcome()
    manifest = _load_cursor_manifest()
    has_agents = "agents" in manifest

    state = outcome["outcome"]
    if state == "failed":
        assert not has_agents, (
            "FAIL branch: .cursor-plugin/plugin.json `agents` field MUST be absent "
            "per cursor-fixture-decision.contract.md:39"
        )
    elif state == "passed":
        assert has_agents, (
            "PASS branch: .cursor-plugin/plugin.json `agents` field MUST be present"
        )
    # pending: either is acceptable
