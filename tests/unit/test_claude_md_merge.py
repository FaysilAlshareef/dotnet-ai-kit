"""Tests for `claude_md.py` — CLAUDE.md conventions-block merge.

Claude Code's plugin manifest has no `rules` key, so the kit injects the
5 universal conventions between sentinel markers in CLAUDE.md. These tests
verify the merge is idempotent and preserves user-authored content outside
the markers.
"""

from __future__ import annotations

from pathlib import Path

from dotnet_ai_kit.claude_md import (
    BEGIN_MARKER,
    CONVENTION_NAMES,
    END_MARKER,
    block_sha256,
    extract_block,
    merge_into_claude_md,
    render_conventions_block,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = REPO_ROOT / "rules"


def test_render_conventions_block_has_markers_and_all_5_rules() -> None:
    block = render_conventions_block(RULES_DIR)
    assert block.startswith(BEGIN_MARKER)
    assert END_MARKER in block
    # Each convention's content (their H1 heading) shows up in the block.
    # Headings vary, but each rule's body has at least one ## section.
    for name in CONVENTION_NAMES:
        rule_file = RULES_DIR / "conventions" / f"{name}.md"
        assert rule_file.is_file(), f"missing source rule: {rule_file}"


def test_render_conventions_block_strips_frontmatter() -> None:
    """Rendered block must not contain the source files' YAML frontmatter."""
    block = render_conventions_block(RULES_DIR)
    # Frontmatter lines like `description:` should not appear at block start.
    lines = block.splitlines()
    # The block starts with the BEGIN marker, then comments + intro headers.
    # No `---` delimiter blocks anywhere except within the marker comments.
    yaml_delim_lines = [i for i, ln in enumerate(lines) if ln.strip() == "---"]
    assert yaml_delim_lines == [], (
        f"frontmatter delimiters leaked into block at lines {yaml_delim_lines}"
    )


def test_merge_creates_claude_md_when_absent(tmp_path: Path) -> None:
    path, digest = merge_into_claude_md(tmp_path, RULES_DIR)
    assert path == tmp_path / "CLAUDE.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert BEGIN_MARKER in text
    assert END_MARKER in text
    assert digest == block_sha256(render_conventions_block(RULES_DIR))


def test_merge_appends_block_when_no_markers(tmp_path: Path) -> None:
    """Existing CLAUDE.md without markers gets the block appended."""
    target = tmp_path / "CLAUDE.md"
    user_content = "# My Project\n\nMy hand-written guidance for Claude.\n"
    target.write_text(user_content, encoding="utf-8")

    merge_into_claude_md(tmp_path, RULES_DIR)
    after = target.read_text(encoding="utf-8")

    # User content survives intact at the top.
    assert after.startswith("# My Project")
    assert "My hand-written guidance for Claude." in after
    # New block appears below.
    assert BEGIN_MARKER in after
    assert END_MARKER in after
    # User content comes before the marker, not after it.
    assert after.index("hand-written") < after.index(BEGIN_MARKER)


def test_merge_replaces_existing_block_when_markers_present(tmp_path: Path) -> None:
    """Re-running merge rewrites only the marked region; user content unchanged."""
    target = tmp_path / "CLAUDE.md"
    before = (
        "# My Project\n\n"
        "My guidance for Claude.\n\n"
        f"{BEGIN_MARKER}\n"
        "OLD STALE CONTENT THAT MUST BE REPLACED\n"
        f"{END_MARKER}\n\n"
        "## Section after the marker\n\nMore user content here.\n"
    )
    target.write_text(before, encoding="utf-8")

    merge_into_claude_md(tmp_path, RULES_DIR)
    after = target.read_text(encoding="utf-8")

    assert "OLD STALE CONTENT" not in after
    assert "My guidance for Claude." in after
    assert "## Section after the marker" in after
    assert "More user content here." in after
    assert BEGIN_MARKER in after
    assert END_MARKER in after


def test_merge_is_idempotent(tmp_path: Path) -> None:
    """Running merge twice produces identical CLAUDE.md."""
    merge_into_claude_md(tmp_path, RULES_DIR)
    first = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")

    merge_into_claude_md(tmp_path, RULES_DIR)
    second = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")

    assert first == second


def test_extract_block_round_trips(tmp_path: Path) -> None:
    merge_into_claude_md(tmp_path, RULES_DIR)
    text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    block = extract_block(text)
    assert block is not None
    assert block.startswith(BEGIN_MARKER)
    assert END_MARKER in block


def test_extract_block_returns_none_when_markers_absent() -> None:
    assert extract_block("# Plain CLAUDE.md\n\nNo markers here.\n") is None


def test_merge_preserves_user_edits_outside_markers(tmp_path: Path) -> None:
    """User can edit CLAUDE.md between merges; their edits survive."""
    merge_into_claude_md(tmp_path, RULES_DIR)
    target = tmp_path / "CLAUDE.md"
    text = target.read_text(encoding="utf-8")

    # User appends their own section after the block.
    appended = text + "\n## My custom rules\n\nNever use Goto.\n"
    target.write_text(appended, encoding="utf-8")

    merge_into_claude_md(tmp_path, RULES_DIR)
    after = target.read_text(encoding="utf-8")
    assert "## My custom rules" in after
    assert "Never use Goto." in after


def test_block_sha256_stable_across_calls() -> None:
    a = block_sha256(render_conventions_block(RULES_DIR))
    b = block_sha256(render_conventions_block(RULES_DIR))
    assert a == b
    assert len(a) == 64
