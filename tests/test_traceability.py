"""T075 — SC-010: every FR + finding has a traceability row."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TRACE = REPO / "specs" / "018-fix-token-burn" / "traceability.md"
SPEC = REPO / "specs" / "018-fix-token-burn" / "spec.md"

FR_RE = re.compile(r"\bFR-(\d{3})\b")
TESTABLE_FINDINGS = {
    "F01",
    "F02",
    "F03",
    "F04",
    "F05",
    "F06",
    "F07",
    "F08",
    "F09",
    "F10",
    "F11",
    "F12",
    "F13",
    "F14",
    "F16",
    "F17",
    "F18",
}


def _trace_text() -> str:
    return TRACE.read_text(encoding="utf-8")


def test_every_fr_has_traceability_row() -> None:
    spec_text = SPEC.read_text(encoding="utf-8")
    declared = {int(m) for m in FR_RE.findall(spec_text)}
    assert declared, "no FRs found in spec.md"
    text = _trace_text()
    missing = [fr for fr in sorted(declared) if f"FR-{fr:03d}" not in text]
    assert not missing, f"FRs without traceability rows: {missing}"


def test_every_testable_finding_has_row() -> None:
    text = _trace_text()
    missing = sorted(f for f in TESTABLE_FINDINGS if f"| {f} " not in text and f" {f} " not in text)
    assert not missing, f"findings without traceability rows: {missing}"
