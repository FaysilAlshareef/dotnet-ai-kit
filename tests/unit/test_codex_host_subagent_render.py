"""OOS-004 partial lift (May 2026): CodexHost renders subagents per-project.

Asserts that `CodexHost.write_per_solution_files()` materialises
`.codex/agents/<name>.toml` files from `agents-source/<name>.md`, per
`https://developers.openai.com/codex/subagents` (retrieved 2026-05-19).

Conflict policy (v1.0 contract): pre-existing files are PRESERVED (user
customizations win) — the adapter skips them and proceeds.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.hosts.codex import CodexHost


def _write_source(plugin_root: Path, name: str, frontmatter: str = "", body: str = "Body.") -> Path:
    """Write a minimal agents-source/<name>.md file under the fake plugin root."""
    src_dir = plugin_root / "agents-source"
    src_dir.mkdir(parents=True, exist_ok=True)
    src = src_dir / f"{name}.md"
    fm_block = (
        f"---\n{frontmatter}---\n\n"
        if not frontmatter.strip() == ""
        else (f"---\n{frontmatter}---\n\n")
    )
    src.write_text(
        fm_block + body + "\n",
        encoding="utf-8",
    )
    return src


def test_codex_host_writes_toml_for_each_source(tmp_path: Path) -> None:
    """Each agents-source/<name>.md is rendered to .codex/agents/<name>.toml."""
    plugin_root = tmp_path / "plugin"
    _write_source(
        plugin_root,
        "api-designer",
        frontmatter="name: api-designer\ndescription: API design specialist\n",
        body="# API Designer\n\nFollow REST conventions.\n",
    )
    _write_source(
        plugin_root,
        "command-architect",
        frontmatter="name: command-architect\ndescription: CQRS command side architect\n",
        body="# Command Architect\n\nDesign aggregates.\n",
    )

    project_root = tmp_path / "solution"
    project_root.mkdir()

    host = CodexHost()
    written = host.write_per_solution_files(project_root, plugin_root=plugin_root)

    assert len(written) == 2
    out_dir = project_root / ".codex" / "agents"
    assert (out_dir / "api-designer.toml").is_file()
    assert (out_dir / "command-architect.toml").is_file()

    api_toml = (out_dir / "api-designer.toml").read_text(encoding="utf-8")
    assert 'name = "api-designer"' in api_toml
    assert 'description = "API design specialist"' in api_toml
    assert "developer_instructions = '''" in api_toml
    assert "# API Designer" in api_toml


def test_codex_host_preserves_existing_user_customizations(tmp_path: Path) -> None:
    """v1.0 conflict policy: pre-existing .codex/agents/<name>.toml is NEVER
    overwritten. The user's content wins."""
    plugin_root = tmp_path / "plugin"
    _write_source(
        plugin_root,
        "api-designer",
        frontmatter="name: api-designer\ndescription: API design specialist\n",
        body="# Plugin default body\n",
    )

    project_root = tmp_path / "solution"
    agents_dir = project_root / ".codex" / "agents"
    agents_dir.mkdir(parents=True)
    user_file = agents_dir / "api-designer.toml"
    user_customized = 'name = "api-designer"\ndescription = "my custom override"\n'
    user_file.write_text(user_customized, encoding="utf-8")

    host = CodexHost()
    written = host.write_per_solution_files(project_root, plugin_root=plugin_root)

    # File was preserved → NOT in `written` list
    assert written == []
    # File content is unchanged
    assert user_file.read_text(encoding="utf-8") == user_customized


def test_codex_host_writes_kebab_case_filenames(tmp_path: Path) -> None:
    """Output filenames preserve the source's kebab-case stem — cross-host
    UX consistency (same agent name in Claude, Cursor, Codex)."""
    plugin_root = tmp_path / "plugin"
    _write_source(
        plugin_root,
        "controlpanel-architect",
        frontmatter="name: controlpanel-architect\ndescription: Blazor admin UI\n",
    )
    project_root = tmp_path / "solution"
    project_root.mkdir()

    host = CodexHost()
    written = host.write_per_solution_files(project_root, plugin_root=plugin_root)

    assert len(written) == 1
    assert written[0].name == "controlpanel-architect.toml"


def test_codex_host_no_source_dir_returns_empty(tmp_path: Path) -> None:
    """No agents-source/ in the plugin → no files written, no exception."""
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir()
    project_root = tmp_path / "solution"
    project_root.mkdir()

    host = CodexHost()
    written = host.write_per_solution_files(project_root, plugin_root=plugin_root)
    assert written == []
    # Importantly: we don't create an empty `.codex/agents/` dir when nothing
    # to write.
    assert not (project_root / ".codex").exists()


def test_codex_host_skips_malformed_source_continues_others(tmp_path: Path) -> None:
    """A source file with bad frontmatter is logged and skipped — other
    sources still render successfully."""
    plugin_root = tmp_path / "plugin"
    src_dir = plugin_root / "agents-source"
    src_dir.mkdir(parents=True)
    # Malformed: no frontmatter delimiters
    (src_dir / "broken.md").write_text("Just a body, no frontmatter.\n", encoding="utf-8")
    # Valid
    _write_source(
        plugin_root,
        "good",
        frontmatter="name: good\ndescription: A good agent\n",
    )

    project_root = tmp_path / "solution"
    project_root.mkdir()

    host = CodexHost()
    written = host.write_per_solution_files(project_root, plugin_root=plugin_root)

    # Only the good one rendered
    assert len(written) == 1
    assert written[0].name == "good.toml"


def test_codex_host_uses_real_bundled_agents_source_path(tmp_path: Path) -> None:
    """End-to-end smoke: when called without plugin_root, the host
    auto-detects the bundled agents-source/ and renders all of them."""
    project_root = tmp_path / "solution"
    project_root.mkdir()

    host = CodexHost()
    written = host.write_per_solution_files(project_root)

    # 14 agents in agents-source/ at the time of this test (1 spike fixture +
    # 13 specialists per OOS-005 PASS branch). Assert at-least to avoid
    # brittleness on future additions.
    assert len(written) >= 13, f"expected ≥13 subagent TOML files, got {len(written)}"
    # Spot-check one known agent
    api_toml = project_root / ".codex" / "agents" / "api-designer.toml"
    assert api_toml.is_file()
    content = api_toml.read_text(encoding="utf-8")
    assert 'name = "api-designer"' in content
    assert "developer_instructions = '''" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
