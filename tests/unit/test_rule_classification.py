"""T084 — exactly 5 conventions + 11 domain rules (commit 14 / FR-011 / CHK031-032).

Asserts the rule classification split per the feature 019 spec:
- 5 always-on convention rules in `rules/conventions/`
- 11 just-in-time domain rules in `rules/domain/`
- No rules in the legacy `rules/<name>.md` top-level location
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RULES_DIR = REPO / "rules"

EXPECTED_CONVENTIONS = frozenset(
    {
        "async-concurrency",
        "coding-style",
        "existing-projects",
        "security",
        "tool-calls",
    }
)

EXPECTED_DOMAIN = frozenset(
    {
        "api-design",
        "architecture",
        "configuration",
        "data-access",
        "error-handling",
        "localization",
        "multi-repo",
        "naming",
        "observability",
        "performance",
        "testing",
    }
)


def test_exactly_5_convention_rules() -> None:
    """rules/conventions/ MUST contain exactly 5 .md files per FR-011 / CHK031."""
    conv_dir = RULES_DIR / "conventions"
    assert conv_dir.is_dir(), "rules/conventions/ directory missing"
    md_files = {p.stem for p in conv_dir.glob("*.md")}
    assert md_files == EXPECTED_CONVENTIONS, (
        f"Convention rules mismatch.\n"
        f"  Expected: {sorted(EXPECTED_CONVENTIONS)}\n"
        f"  Found: {sorted(md_files)}"
    )


def test_exactly_11_domain_rules() -> None:
    """rules/domain/ MUST contain exactly 11 .md files per FR-011 / CHK032."""
    domain_dir = RULES_DIR / "domain"
    assert domain_dir.is_dir(), "rules/domain/ directory missing"
    md_files = {p.stem for p in domain_dir.glob("*.md")}
    assert md_files == EXPECTED_DOMAIN, (
        f"Domain rules mismatch.\n"
        f"  Expected: {sorted(EXPECTED_DOMAIN)}\n"
        f"  Found: {sorted(md_files)}"
    )


def test_no_legacy_top_level_rules() -> None:
    """rules/<name>.md (top-level) MUST be empty after the reclassification."""
    top_level_md = list(RULES_DIR.glob("*.md"))
    assert not top_level_md, (
        f"Legacy rules still at top level: {[p.name for p in top_level_md]}. "
        f"Move them to rules/conventions/ or rules/domain/."
    )


def test_total_16_rules_unchanged() -> None:
    """The 5+11 split MUST sum to 16 (the constitutional total)."""
    conv = len(list((RULES_DIR / "conventions").glob("*.md")))
    domain = len(list((RULES_DIR / "domain").glob("*.md")))
    assert conv + domain == 16, f"Total rule count is {conv + domain}, expected 16 per constitution"
