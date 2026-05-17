"""T065 — FR-023 / FR-024: learn.md splits memory into 6 named topic files."""

from __future__ import annotations

from pathlib import Path

LEARN = Path(__file__).resolve().parent.parent / "commands" / "learn.md"

TOPIC_FILES = (
    "architecture.md",
    "domain-model.md",
    "event-flow.md",
    "interfaces.md",
    "dependencies.md",
    "conventions.md",
)


def test_learn_references_all_six_topic_files() -> None:
    text = LEARN.read_text(encoding="utf-8")
    missing = [f for f in TOPIC_FILES if f not in text]
    assert not missing, f"learn.md missing topic file references: {missing}"


def test_learn_does_not_use_always_loaded_rule_phrase() -> None:
    text = LEARN.read_text(encoding="utf-8").lower()
    assert "always-loaded rule" not in text
    assert "always loaded rule" not in text


def test_learn_states_constitution_under_100_lines() -> None:
    text = LEARN.read_text(encoding="utf-8")
    assert "≤100 lines" in text or "<=100 lines" in text or "100 lines" in text
