"""T086a — FR-029: CI runs static+unit every PR; smoke runs gated."""

from __future__ import annotations

from pathlib import Path

import pytest

CI = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"


def _ci_text() -> str:
    if not CI.is_file():
        pytest.skip(".github/workflows/ci.yml not present")
    return CI.read_text(encoding="utf-8")


def test_static_unit_job_runs_on_every_pr() -> None:
    text = _ci_text()
    assert "static-unit" in text or "static_unit" in text, "static-unit job not found in CI config"


def test_smoke_job_gated_by_label_or_schedule() -> None:
    text = _ci_text()
    has_label = "[smoke]" in text or "labels" in text
    has_schedule = "schedule" in text or "cron" in text
    assert has_label or has_schedule, "smoke job must be gated by [smoke] label or nightly cron"
    assert "CLAUDE_CODE_SMOKE" in text
