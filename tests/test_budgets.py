"""T048 — FR-025 / FR-026 / FR-027 / FR-037: token line-budget enforcement."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

BUDGETS = {
    "commands/*.md": 200,
    "rules/*.md": 100,
    "skills/**/SKILL.md": 400,
    "agents/*.md": 120,
    "profiles/**/*.md": 100,
}


def _files(glob: str) -> list[Path]:
    return list(REPO.glob(glob))


def test_command_budget() -> None:
    over: list[tuple[str, int]] = []
    for f in _files("commands/*.md"):
        n = len(f.read_text(encoding="utf-8").splitlines())
        if n > BUDGETS["commands/*.md"]:
            over.append((str(f.relative_to(REPO)), n))
    assert not over, f"commands over budget (>200): {over}"


def test_rule_budget() -> None:
    over: list[tuple[str, int]] = []
    for f in _files("rules/*.md"):
        n = len(f.read_text(encoding="utf-8").splitlines())
        if n > BUDGETS["rules/*.md"]:
            over.append((str(f.relative_to(REPO)), n))
    assert not over, f"rules over budget (>100): {over}"


def test_skill_budget() -> None:
    over: list[tuple[str, int]] = []
    for f in _files("skills/**/SKILL.md"):
        n = len(f.read_text(encoding="utf-8").splitlines())
        if n > BUDGETS["skills/**/SKILL.md"]:
            over.append((str(f.relative_to(REPO)), n))
    assert not over, f"skills over budget (>400): {over}"


def test_agent_budget() -> None:
    over: list[tuple[str, int]] = []
    for f in _files("agents/*.md"):
        n = len(f.read_text(encoding="utf-8").splitlines())
        if n > BUDGETS["agents/*.md"]:
            over.append((str(f.relative_to(REPO)), n))
    assert not over, f"agents over budget (>120): {over}"


def test_profile_budget() -> None:
    over: list[tuple[str, int]] = []
    for f in _files("profiles/**/*.md"):
        n = len(f.read_text(encoding="utf-8").splitlines())
        if n > BUDGETS["profiles/**/*.md"]:
            over.append((str(f.relative_to(REPO)), n))
    assert not over, f"profiles over budget (>100): {over}"
