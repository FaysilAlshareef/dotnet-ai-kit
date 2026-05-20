"""T085 — no architecture-branching rules in the always-on set (FR-012 / CHK033-034).

Asserts:
- `error-handling` (which has architecture-specific branches per FR-012) is
  in rules/domain/, NOT rules/conventions/.
- `naming` (which requires runtime substitution per FR-012) is in
  rules/domain/, NOT rules/conventions/.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent


def test_error_handling_is_domain_not_convention() -> None:
    """CHK033: error-handling has arch-branches → MUST be path-scoped."""
    assert (REPO / "rules" / "domain" / "error-handling.md").is_file()
    assert not (REPO / "rules" / "conventions" / "error-handling.md").is_file()


def test_naming_is_domain_not_convention() -> None:
    """CHK034: naming requires runtime metadata substitution → MUST be path-scoped."""
    assert (REPO / "rules" / "domain" / "naming.md").is_file()
    assert not (REPO / "rules" / "conventions" / "naming.md").is_file()
