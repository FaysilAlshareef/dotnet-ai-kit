"""CLAUDE.md merge for universal conventions (feature: always-on rules).

Claude Code's plugin manifest has no `rules` key — only commands/skills/agents/
hooks/mcpServers. To deliver the 5 universal convention rules as always-on
context (the way `rules/conventions/*.md` was always intended), this module
merges their bodies into the project's `CLAUDE.md` between sentinel markers.

Behavior:
- If CLAUDE.md exists with markers → replace content between them.
- If CLAUDE.md exists without markers → append a fresh block at the end.
- If CLAUDE.md does not exist → create a minimal file with just the block.

The user's hand-authored CLAUDE.md content outside the markers is preserved
across re-runs. Re-running `dotnet-ai init` or `dotnet-ai upgrade` rewrites
only the marked region.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

BEGIN_MARKER = "<!-- BEGIN dotnet-ai-kit conventions -->"
END_MARKER = "<!-- END dotnet-ai-kit conventions -->"

# The 5 universal conventions per constitution v1.0.8.
# Order matters — emitted in this sequence inside the marked block.
CONVENTION_NAMES: tuple[str, ...] = (
    "existing-projects",
    "coding-style",
    "async-concurrency",
    "security",
    "tool-calls",
)

_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def _strip_frontmatter(text: str) -> str:
    """Drop the leading YAML frontmatter block from a rule body."""
    return _FRONTMATTER_RE.sub("", text, count=1).lstrip("\n")


def render_conventions_block(rules_dir: Path) -> str:
    """Render the 5 universal conventions into a single Markdown block.

    `rules_dir` is the kit's `rules/` directory (contains `conventions/`).
    The block starts and ends with sentinel markers and is the exact content
    that gets dropped into CLAUDE.md.
    """
    conv_dir = rules_dir / "conventions"
    parts: list[str] = [
        BEGIN_MARKER,
        "",
        "<!-- This block is managed by dotnet-ai-kit. Re-running",
        "     `dotnet-ai init` or `dotnet-ai upgrade` will rewrite it.",
        "     Content outside the markers is preserved. -->",
        "",
        "## Project Conventions (always-on)",
        "",
        (
            "The following universal rules apply to every change. "
            "Path-scoped domain rules are injected by the PreToolUse hook "
            "when matching files are edited."
        ),
        "",
    ]

    for name in CONVENTION_NAMES:
        rule_path = conv_dir / f"{name}.md"
        if not rule_path.is_file():
            # Defensive: skip silently rather than crash init/upgrade for
            # a missing optional rule. `dotnet-ai check` surfaces it.
            continue
        body = _strip_frontmatter(rule_path.read_text(encoding="utf-8"))
        parts.append(body.rstrip())
        parts.append("")

    parts.append(END_MARKER)
    return "\n".join(parts) + "\n"


def block_sha256(block: str) -> str:
    """Return sha256 of the rendered block (used for drift detection)."""
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


def _splice_block(existing: str, new_block: str) -> str:
    """Replace content between markers, or append if markers absent."""
    begin_idx = existing.find(BEGIN_MARKER)
    end_idx = existing.find(END_MARKER)

    if begin_idx != -1 and end_idx != -1 and end_idx > begin_idx:
        before = existing[:begin_idx]
        after_start = end_idx + len(END_MARKER)
        # Consume trailing newline that belongs to the old end marker line
        if after_start < len(existing) and existing[after_start] == "\n":
            after_start += 1
        after = existing[after_start:]
        # Ensure single blank line separates before/after sections
        before = before.rstrip("\n")
        if before:
            before += "\n\n"
        return before + new_block + ("\n" + after.lstrip("\n") if after.strip() else "")

    # No markers — append fresh block, preserving existing content.
    trimmed = existing.rstrip("\n")
    if trimmed:
        return trimmed + "\n\n" + new_block
    return new_block


def merge_into_claude_md(project_root: Path, rules_dir: Path) -> tuple[Path, str]:
    """Merge the conventions block into the project's CLAUDE.md.

    Returns (path, sha256_of_block). The hash is the block's hash, not the
    whole file — so user edits outside the markers don't appear as drift.

    Creates a minimal CLAUDE.md if absent.
    """
    target = project_root / "CLAUDE.md"
    block = render_conventions_block(rules_dir)
    digest = block_sha256(block)

    if target.is_file():
        existing = target.read_text(encoding="utf-8")
    else:
        existing = (
            "# CLAUDE.md\n\n"
            "Guidance for Claude Code (claude.ai/code) when working in this repository.\n\n"
        )

    merged = _splice_block(existing, block)

    # Idempotency: only write if content actually changed
    if not target.is_file() or merged != existing:
        target.write_text(merged, encoding="utf-8")

    return target, digest


def extract_block(claude_md_text: str) -> str | None:
    """Return the marked block from a CLAUDE.md text, or None if absent.

    Used by `dotnet-ai check` to verify the block matches the current kit.
    """
    begin_idx = claude_md_text.find(BEGIN_MARKER)
    end_idx = claude_md_text.find(END_MARKER)
    if begin_idx == -1 or end_idx == -1 or end_idx <= begin_idx:
        return None
    end_after = end_idx + len(END_MARKER)
    if end_after < len(claude_md_text) and claude_md_text[end_after] == "\n":
        end_after += 1
    return claude_md_text[begin_idx:end_after]
