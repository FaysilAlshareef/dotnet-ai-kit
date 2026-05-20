"""T195b — Cursor `.mdc` rule renderer (commit 33+34 coverage close-out).

Tests for `render.render_cursor_rule_mdc()` and
`render.write_cursor_rules_for_plugin()` added in commit 31 (OOS-005 PASS
branch). The shipped artifacts under `rules/cursor/*.mdc` are produced
by this renderer; the tests below pin the contract per research R12
(https://cursor.com/docs/context/rules):

- ``rules/conventions/<name>.md``  → ``alwaysApply: true`` (no globs)
- ``rules/domain/<name>.md``       → ``alwaysApply: false`` + ``globs:``
  (comma-separated, from the source's ``paths:`` list)
- Defensive fallback: rule outside conventions/ or domain/ → always-apply.
- Errors: missing frontmatter, missing ``paths:`` on a domain rule,
  ``paths:`` not a list.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dotnet_ai_kit.render import (
    _parse_rule_frontmatter,
    render_cursor_rule_mdc,
    write_cursor_rules_for_plugin,
)


def _write_rule(
    target: Path,
    relative: str,
    frontmatter: dict | None,
    body: str = "# Rule body\n\nContent here.\n",
) -> Path:
    """Write a rule source file with the given frontmatter + body."""
    path = target / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if frontmatter is None:
        path.write_text(body, encoding="utf-8")
    else:
        fm_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        path.write_text(f"---\n{fm_yaml}---\n\n{body}", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# _parse_rule_frontmatter
# ---------------------------------------------------------------------------


def test_parse_rule_frontmatter_returns_dict_and_body(tmp_path: Path) -> None:
    path = _write_rule(
        tmp_path,
        "rules/conventions/sample.md",
        {"description": "Sample rule"},
        body="# Sample\n\nBody.\n",
    )
    fm, body = _parse_rule_frontmatter(path)
    assert fm == {"description": "Sample rule"}
    assert "# Sample" in body


def test_parse_rule_frontmatter_rejects_missing_delimiters(tmp_path: Path) -> None:
    path = _write_rule(tmp_path, "rules/conventions/no-fm.md", None, body="just body\n")
    with pytest.raises(ValueError, match="no YAML frontmatter"):
        _parse_rule_frontmatter(path)


def test_parse_rule_frontmatter_rejects_non_mapping(tmp_path: Path) -> None:
    # Frontmatter is a YAML list instead of a mapping
    path = tmp_path / "rules" / "conventions" / "list-fm.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n- item1\n- item2\n---\n\nbody\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a YAML mapping"):
        _parse_rule_frontmatter(path)


# ---------------------------------------------------------------------------
# render_cursor_rule_mdc — conventions branch
# ---------------------------------------------------------------------------


def test_render_cursor_rule_mdc_convention_emits_alwaysapply_true(tmp_path: Path) -> None:
    """Universal rule → alwaysApply: true, no globs."""
    src = _write_rule(
        tmp_path,
        "rules/conventions/async-concurrency.md",
        {"description": "Async correctness"},
        body="# Async rules\n\nContent.\n",
    )
    output = render_cursor_rule_mdc(src)
    # Parse the rendered frontmatter
    assert output.startswith("---\n")
    fm_block = output.split("---", 2)[1]
    fm = yaml.safe_load(fm_block)
    assert fm == {"description": "Async correctness", "alwaysApply": True}
    # Body preserved
    assert "# Async rules" in output


def test_render_cursor_rule_mdc_convention_without_description(tmp_path: Path) -> None:
    """A convention rule without `description:` still gets alwaysApply: true."""
    src = _write_rule(
        tmp_path,
        "rules/conventions/no-desc.md",
        {},  # empty frontmatter
        body="# Body\n",
    )
    output = render_cursor_rule_mdc(src)
    fm_block = output.split("---", 2)[1]
    fm = yaml.safe_load(fm_block)
    assert fm == {"alwaysApply": True}


# ---------------------------------------------------------------------------
# render_cursor_rule_mdc — domain branch
# ---------------------------------------------------------------------------


def test_render_cursor_rule_mdc_domain_emits_globs_and_alwaysapply_false(tmp_path: Path) -> None:
    """Domain rule → alwaysApply: false + comma-separated globs from `paths:`."""
    src = _write_rule(
        tmp_path,
        "rules/domain/testing.md",
        {
            "description": "Testing rules",
            "paths": ["tests/**/*.cs", "**/*.Tests/**/*.cs", "tests/**/*.py"],
        },
        body="# Testing\n",
    )
    output = render_cursor_rule_mdc(src)
    fm_block = output.split("---", 2)[1]
    fm = yaml.safe_load(fm_block)
    assert fm["description"] == "Testing rules"
    assert fm["globs"] == "tests/**/*.cs,**/*.Tests/**/*.cs,tests/**/*.py"
    assert fm["alwaysApply"] is False


def test_render_cursor_rule_mdc_domain_single_path(tmp_path: Path) -> None:
    """Domain rule with a single path: globs is that path, no trailing comma."""
    src = _write_rule(
        tmp_path,
        "rules/domain/architecture.md",
        {"description": "Architecture", "paths": ["src/**/*.cs"]},
    )
    output = render_cursor_rule_mdc(src)
    fm = yaml.safe_load(output.split("---", 2)[1])
    assert fm["globs"] == "src/**/*.cs"
    assert fm["alwaysApply"] is False


def test_render_cursor_rule_mdc_domain_missing_paths_raises(tmp_path: Path) -> None:
    """Domain rule without `paths:` → ValueError with actionable message."""
    src = _write_rule(
        tmp_path,
        "rules/domain/no-paths.md",
        {"description": "Missing paths"},
    )
    with pytest.raises(ValueError, match="no `paths:` list"):
        render_cursor_rule_mdc(src)


def test_render_cursor_rule_mdc_domain_paths_must_be_list(tmp_path: Path) -> None:
    """Domain rule with `paths:` as scalar string → ValueError."""
    src = _write_rule(
        tmp_path,
        "rules/domain/bad-paths.md",
        {"description": "Bad paths", "paths": "src/**/*.cs"},  # scalar, not list
    )
    with pytest.raises(ValueError, match="must be a list"):
        render_cursor_rule_mdc(src)


# ---------------------------------------------------------------------------
# render_cursor_rule_mdc — defensive (rule not in conventions/ or domain/)
# ---------------------------------------------------------------------------


def test_render_cursor_rule_mdc_defensive_path_falls_back_to_alwaysapply(tmp_path: Path) -> None:
    """A rule not under conventions/ or domain/ falls back to alwaysApply: true."""
    src = _write_rule(
        tmp_path,
        "rules/orphan.md",  # no conventions/ or domain/ in the path
        {"description": "Orphan rule"},
    )
    output = render_cursor_rule_mdc(src)
    fm = yaml.safe_load(output.split("---", 2)[1])
    assert fm == {"description": "Orphan rule", "alwaysApply": True}


# ---------------------------------------------------------------------------
# write_cursor_rules_for_plugin
# ---------------------------------------------------------------------------


def test_write_cursor_rules_for_plugin_emits_per_rule_mdc_files(tmp_path: Path) -> None:
    """End-to-end: seed conventions + domain sources; assert .mdc files written."""
    _write_rule(
        tmp_path,
        "rules/conventions/async.md",
        {"description": "Async"},
    )
    _write_rule(
        tmp_path,
        "rules/conventions/security.md",
        {"description": "Security"},
    )
    _write_rule(
        tmp_path,
        "rules/domain/testing.md",
        {"description": "Tests", "paths": ["tests/**/*.cs"]},
    )

    written = write_cursor_rules_for_plugin(tmp_path)
    # 2 conventions + 1 domain = 3 files
    assert len(written) == 3
    names = sorted(p.name for p in written)
    assert names == ["async.mdc", "security.mdc", "testing.mdc"]

    # Verify the convention output has alwaysApply: true
    async_mdc = tmp_path / "rules" / "cursor" / "async.mdc"
    fm = yaml.safe_load(async_mdc.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm["alwaysApply"] is True
    assert "globs" not in fm

    # Verify the domain output has alwaysApply: false + globs
    testing_mdc = tmp_path / "rules" / "cursor" / "testing.mdc"
    fm = yaml.safe_load(testing_mdc.read_text(encoding="utf-8").split("---", 2)[1])
    assert fm["alwaysApply"] is False
    assert fm["globs"] == "tests/**/*.cs"


def test_write_cursor_rules_for_plugin_handles_empty_subdir(tmp_path: Path) -> None:
    """If conventions/ is empty (or missing), domain/ alone still writes."""
    # Only seed domain/, leave conventions/ absent.
    _write_rule(
        tmp_path,
        "rules/domain/single.md",
        {"description": "Solo", "paths": ["src/**/*.cs"]},
    )
    written = write_cursor_rules_for_plugin(tmp_path)
    assert len(written) == 1
    assert written[0].name == "single.mdc"


def test_write_cursor_rules_for_plugin_idempotent_overwrites(tmp_path: Path) -> None:
    """Running twice does not duplicate; second run overwrites with current content."""
    src = _write_rule(
        tmp_path,
        "rules/conventions/x.md",
        {"description": "First version"},
        body="# Original\n",
    )
    first = write_cursor_rules_for_plugin(tmp_path)
    assert len(first) == 1
    # Mutate the source and re-run
    fm_yaml = yaml.dump({"description": "Second version"}, sort_keys=False)
    src.write_text(f"---\n{fm_yaml}---\n\n# Updated\n", encoding="utf-8")
    second = write_cursor_rules_for_plugin(tmp_path)
    assert len(second) == 1
    out = (tmp_path / "rules" / "cursor" / "x.mdc").read_text(encoding="utf-8")
    assert "Second version" in out
    assert "# Updated" in out
    assert "First version" not in out
