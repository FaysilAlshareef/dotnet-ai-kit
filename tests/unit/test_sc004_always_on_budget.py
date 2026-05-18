"""T091 — SC-004 always-on context token budget (post-rule-reclassification).

Per FR-011 + SC-004: after the v1.0.8 rule reclassification (5 universal +
11 path-scoped), the always-on context (SessionStart stdout + universal
rule bodies) MUST:
- Total in the 2500-3000 token target band.
- Achieve ≥65% reduction from the pre-feature-019 baseline (~9000 tokens).

This test calls `scripts/measure_always_on.py` to compute the live values.
The CI workflow at `.github/workflows/measure.yml` captures the same
numbers on every push to measurements.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
MEASURE_SCRIPT = REPO / "scripts" / "measure_always_on.py"


def _measure() -> dict:
    """Run the measurement script and return the JSON payload."""
    result = subprocess.run(
        [sys.executable, str(MEASURE_SCRIPT)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"measure_always_on.py failed (rc={result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return json.loads(result.stdout)


def test_always_on_total_in_target_band() -> None:
    """SC-004: total always-on context tokens MUST be in 2500-3000 band."""
    payload = _measure()
    total = payload["total_tokens"]
    assert 2500 <= total <= 3000, (
        f"SC-004 band violation: total={total} tokens, target 2500-3000. "
        f"Breakdown: session_start={payload['session_start_tokens']}, "
        f"rules={payload['universal_rules_tokens']}"
    )


def test_always_on_at_least_65pct_reduction_from_baseline() -> None:
    """SC-004: ≥65% reduction from baseline ~9000 tokens."""
    payload = _measure()
    reduction = payload["reduction_pct_vs_baseline"]
    assert reduction >= 65.0, (
        f"SC-004 reduction violation: {reduction:.1f}% < 65% target. "
        f"total={payload['total_tokens']}, baseline={payload['baseline_estimate']}"
    )


def test_session_start_stdout_under_500_tokens() -> None:
    """SC-013 corollary: SessionStart stdout MUST be ≤500 tokens (covered
    by test_session_start_budget; this is a cross-check)."""
    payload = _measure()
    assert payload["session_start_tokens"] <= 500, (
        f"SessionStart stdout {payload['session_start_tokens']} tokens > 500 limit"
    )
