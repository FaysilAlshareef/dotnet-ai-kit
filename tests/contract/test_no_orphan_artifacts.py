"""Detect orphan artifacts not declared in a manifest, and drift between
generated outputs and their sources (per codex round-2 review M-CX-7 + claude 11.1).

Three drift classes covered:
1. test_no_orphan_claude_agent_files — every file in agents-claude/ must
   appear in .claude-plugin/plugin.json.
2. test_generated_agents_match_sources — every agents-source/*.md
   re-rendered via the host generator must match the on-disk output
   byte-for-byte (Claude shape via generate_claude_agent, Cursor shape
   via generate_cursor_agent).
3. test_cursor_rules_match_renderer — every rules/cursor/*.mdc must match
   what write_cursor_rules_for_plugin() produces from current
   rules/conventions/ + rules/domain/.

These tests catch the "manifest one-way drift" + "generated artifact
staleness" patterns that no existing test covers.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent


def test_no_orphan_claude_agent_files() -> None:
    """Every .md file in agents-claude/ must be reachable from the Claude manifest.

    When agents is a directory path (e.g. './agents-claude/'), Claude Code loads
    all .md files in that directory — no orphans possible by definition.
    When agents is an array of explicit paths, every file in agents-claude/ must
    appear in the array.

    The directory-path form is the correct Claude Code v2.1+ format per
    https://code.claude.com/docs/en/plugins-reference#component-path-fields.
    """
    manifest_path = REPO / ".claude-plugin" / "plugin.json"
    agents_claude_dir = REPO / "agents-claude"

    if not manifest_path.is_file():
        pytest.skip("Claude manifest not present")
    if not agents_claude_dir.is_dir():
        pytest.skip("agents-claude/ not present")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    agents_field = manifest.get("agents")

    if isinstance(agents_field, str):
        # Directory-path form: Claude loads all .md files in the directory.
        # No orphans are possible — pass unconditionally.
        return

    # Legacy array form: every file on disk must be in the declared list.
    declared = {Path(p).name for p in (agents_field or [])}
    disk = {f for f in os.listdir(agents_claude_dir) if f.endswith(".md")}
    EXEMPTIONS: set[str] = set()
    orphans = (disk - declared) - EXEMPTIONS
    assert not orphans, (
        f"Orphan agent files in agents-claude/ not declared in Claude manifest: "
        f"{sorted(orphans)}. Switch to directory-path format './agents-claude/' "
        f"or add the files to the agents array."
    )


def test_generated_agents_match_sources() -> None:
    """Every agents-source/*.md re-rendered through the host generator
    must match the corresponding on-disk file in agents-claude/ + agents/.

    Catches the drift class where a maintainer edits an agents-source
    file without re-running the generator, leaving stale build outputs."""
    from dotnet_ai_kit.agent_generators import (
        generate_claude_agent,
        generate_cursor_agent,
    )

    sources_dir = REPO / "agents-source"
    if not sources_dir.is_dir():
        pytest.skip("agents-source/ not present")

    drifted: list[str] = []

    for src in sorted(sources_dir.glob("*.md")):
        # Claude shape: only check when agents-claude/<name>.md exists
        # AND the source actually declares host_overrides.claude (the
        # post-B-1-fix shape may omit Claude overrides for Cursor-only sources).
        claude_out = REPO / "agents-claude" / src.name
        if claude_out.is_file():
            try:
                expected = generate_claude_agent(src)
            except ValueError:
                # Source has no Claude overrides; the file SHOULDN'T exist
                drifted.append(
                    f"agents-claude/{src.name} exists but source lacks host_overrides.claude"
                )
                continue
            actual = claude_out.read_text(encoding="utf-8")
            if expected != actual:
                drifted.append(
                    f"agents-claude/{src.name} drifted from agents-source/{src.name} "
                    f"(re-run the generator)"
                )

        # Cursor shape: every source has a Cursor build output
        cursor_out = REPO / "agents" / src.name
        if cursor_out.is_file():
            expected = generate_cursor_agent(src)
            actual = cursor_out.read_text(encoding="utf-8")
            if expected != actual:
                drifted.append(
                    f"agents/{src.name} drifted from agents-source/{src.name} "
                    f"(re-run the generator)"
                )

    assert not drifted, "Generator-output drift detected:\n  - " + "\n  - ".join(drifted)


def test_cursor_rules_match_renderer(tmp_path: Path) -> None:
    """rules/cursor/*.mdc must be byte-identical to what
    write_cursor_rules_for_plugin() produces from the current
    rules/conventions/ + rules/domain/ source files.

    Catches drift where a maintainer edits a source rule without
    re-running the Cursor renderer."""
    from dotnet_ai_kit.render import write_cursor_rules_for_plugin

    conv_dir = REPO / "rules" / "conventions"
    dom_dir = REPO / "rules" / "domain"
    cur_dir = REPO / "rules" / "cursor"
    if not (conv_dir.is_dir() and dom_dir.is_dir() and cur_dir.is_dir()):
        pytest.skip("rule directories not present")

    # Copy sources into tmp so we don't pollute the repo
    shutil.copytree(conv_dir, tmp_path / "rules" / "conventions")
    shutil.copytree(dom_dir, tmp_path / "rules" / "domain")

    written = write_cursor_rules_for_plugin(tmp_path)
    drifted: list[str] = []

    for mdc_path in written:
        rel = mdc_path.relative_to(tmp_path / "rules" / "cursor")
        disk = cur_dir / rel
        if not disk.is_file():
            drifted.append(f"Renderer produced rules/cursor/{rel} but no such file exists on disk")
            continue
        expected = mdc_path.read_text(encoding="utf-8")
        actual = disk.read_text(encoding="utf-8")
        if expected != actual:
            drifted.append(
                f"rules/cursor/{rel} drifted from rules/conventions/ or rules/domain/ "
                f"(re-run write_cursor_rules_for_plugin)"
            )

    assert not drifted, "Cursor rule renderer drift:\n  - " + "\n  - ".join(drifted)
