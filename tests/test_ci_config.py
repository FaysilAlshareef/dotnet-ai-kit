"""T086a — FR-029: CI runs static+unit every PR; smoke runs gated.

ci/019-plugin-native-arch commit 40: smoke job moved to its own workflow
file `.github/workflows/smoke.yml` (per commit 39 — "reduce CI time" by
running smoke in parallel with the fast lint+unit workflow). The smoke
gating assertion now reads `smoke.yml` instead of `ci.yml`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
CI = WORKFLOWS / "ci.yml"
SMOKE = WORKFLOWS / "smoke.yml"


def _read_or_skip(path: Path) -> str:
    if not path.is_file():
        pytest.skip(f"{path.relative_to(WORKFLOWS.parent.parent)} not present")
    return path.read_text(encoding="utf-8")


def test_static_unit_job_runs_on_every_pr() -> None:
    """The fast lint + static + unit matrix MUST run on every push/PR.

    Lives in `ci.yml`; smoke was extracted to `smoke.yml` per commit 39.
    """
    text = _read_or_skip(CI)
    assert "static-unit" in text or "static_unit" in text, "static-unit job not found in CI config"


def test_smoke_job_gated_by_label_or_schedule() -> None:
    """The smoke job MUST be gated by `[smoke]` label or nightly cron.

    Per commit 39 the smoke job lives in its own workflow `smoke.yml`. This
    test asserts the gating shape and the env-var contract there (so the
    job correctly opts into the smoke pytest fixtures). The previous shape
    (smoke inside `ci.yml`) is now legacy.
    """
    text = _read_or_skip(SMOKE)
    has_label = "[smoke]" in text or "labels" in text or "'smoke'" in text
    has_schedule = "schedule" in text or "cron" in text
    assert has_label or has_schedule, "smoke job must be gated by [smoke] label or nightly cron"
    assert "CLAUDE_CODE_SMOKE" in text


def test_smoke_workflow_runs_on_push_to_ci_branches() -> None:
    """Per ci/019-plugin-native-arch commit 39, smoke also fires on push to
    `ci/**` integration branches (in INFORMATIONAL mode — fixture failures
    don't block the build; STRICT mode is reserved for workflow_dispatch /
    schedule / `smoke`-labelled PR).
    """
    text = _read_or_skip(SMOKE)
    assert "branches:" in text and "ci/**" in text, (
        "smoke.yml must trigger on push to ci/** integration branches"
    )
