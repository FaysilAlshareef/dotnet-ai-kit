"""T065-smoke — SC-012: /dai.learn yields 7-file memory split AND
/dai.plan + /dai.review consume topic files selectively."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

EXPECTED = {
    "constitution.md",
    "architecture.md",
    "domain-model.md",
    "event-flow.md",
    "interfaces.md",
    "dependencies.md",
    "conventions.md",
}


def test_learn_emits_seven_files(tmp_path: Path) -> None:
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")
    # Fixture: a minimal .NET tree with a Domain.csproj so /dai.learn has work.
    (tmp_path / "src" / "App").mkdir(parents=True)
    (tmp_path / "src" / "App" / "App.csproj").write_text("<Project/>\n", encoding="utf-8")
    proc = subprocess.run(
        ["claude", "--print", "/dai.learn"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=300,
    )
    memory_dir = tmp_path / ".dotnet-ai-kit" / "memory"
    assert memory_dir.is_dir(), proc.stdout + proc.stderr
    produced = {p.name for p in memory_dir.iterdir() if p.is_file()}
    assert produced == EXPECTED, f"expected {EXPECTED}, got {produced}"

    const = memory_dir / "constitution.md"
    n = len(const.read_text(encoding="utf-8").splitlines())
    assert n <= 100, f"constitution.md is {n} lines (>100)"


def test_plan_and_review_consume_selective_topic_files(tmp_path: Path) -> None:
    """SC-012: /dai.plan reads architecture.md + domain-model.md but NOT
    event-flow.md / dependencies.md; /dai.review reads conventions.md +
    interfaces.md but NOT architecture.md.

    The transcript fixture captures which topic files the AI actually opened.
    """
    if shutil.which("claude") is None:
        pytest.skip("claude CLI not on PATH")

    # Run /dai.learn first to seed the memory split.
    test_learn_emits_seven_files(tmp_path)

    plan_proc = subprocess.run(
        ["claude", "--print", "/dai.plan", "--dry-run"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=300,
    )
    plan_out = plan_proc.stdout + plan_proc.stderr
    # Transcript should reference the topic files /dai.plan needs and NOT
    # those it doesn't.
    assert "architecture.md" in plan_out
    assert "domain-model.md" in plan_out
    assert "event-flow.md" not in plan_out, (
        "/dai.plan must not pull event-flow.md (FR-024 selective reads)"
    )
    assert "dependencies.md" not in plan_out

    review_proc = subprocess.run(
        ["claude", "--print", "/dai.review", "--dry-run"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=300,
    )
    review_out = review_proc.stdout + review_proc.stderr
    assert "conventions.md" in review_out
    assert "interfaces.md" in review_out
    assert "architecture.md" not in review_out, (
        "/dai.review must not pull architecture.md (FR-024 selective reads)"
    )
