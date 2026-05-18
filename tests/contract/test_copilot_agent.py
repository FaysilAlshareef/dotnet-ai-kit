"""T064 — Copilot `.github/agents/*.agent.md` render contract.

Per `contracts/copilot-agent.contract.md`: per-agent files rendered with
the expanded allow-list. Each file:
- Has `name:`, `description:`, optionally `target:`/`tools:` frontmatter
- Carries the agent body from `agents-source/<name>.md`
"""

from __future__ import annotations

from pathlib import Path

from dotnet_ai_kit.hosts.copilot import CopilotHost


def _setup_project(tmp_path: Path) -> None:
    cfg = tmp_path / ".dotnet-ai-kit"
    cfg.mkdir(parents=True)
    (cfg / "project.yml").write_text(
        "company: A\ndomain: B\nside: C\nproject_type: api\n"
        "dotnet_version: '9.0'\ndetected_paths: {}\n",
        encoding="utf-8",
    )


def test_per_agent_files_emitted_for_each_agents_source(tmp_path: Path) -> None:
    """For each agent in `agents-source/`, a `.agent.md` file is emitted."""
    _setup_project(tmp_path)
    host = CopilotHost()
    host.render(tmp_path)
    agents_dir = tmp_path / ".github" / "agents"
    # The plugin's agents-source/ has at least dotnet-ai-architect.md
    assert agents_dir.is_dir()
    # At least one .agent.md file emitted
    emitted = list(agents_dir.glob("*.agent.md"))
    assert emitted, "render MUST emit per-agent files from agents-source/"


def test_per_agent_files_have_name_frontmatter(tmp_path: Path) -> None:
    """Each rendered .agent.md file MUST have `name:` in frontmatter."""
    _setup_project(tmp_path)
    host = CopilotHost()
    host.render(tmp_path)
    agents_dir = tmp_path / ".github" / "agents"
    for f in agents_dir.glob("*.agent.md"):
        body = f.read_text(encoding="utf-8")
        assert body.startswith("---"), f"{f.name}: frontmatter MUST start at line 0"
        assert "name:" in body
        assert "description:" in body


def test_per_agent_files_carry_body_from_source(tmp_path: Path) -> None:
    """The body of `<name>.agent.md` MUST come from `agents-source/<name>.md`."""
    _setup_project(tmp_path)
    host = CopilotHost()
    host.render(tmp_path)
    # dotnet-ai-architect.md is the canonical agent source
    target = tmp_path / ".github" / "agents" / "dotnet-ai-architect.agent.md"
    if target.is_file():
        body = target.read_text(encoding="utf-8")
        # The source body should appear somewhere in the rendered output
        repo = Path(__file__).resolve().parent.parent.parent
        source_path = repo / "agents-source" / "dotnet-ai-architect.md"
        if source_path.is_file():
            source = source_path.read_text(encoding="utf-8")
            # The first non-frontmatter sentence from source should appear in target
            import re

            m = re.match(r"^---\n.*?\n---\n(.*?)$", source, re.DOTALL)
            if m:
                body_sample = m.group(1).strip()[:40]
                if body_sample:
                    assert body_sample in body, (
                        f"Rendered agent file MUST carry body from agents-source/"
                    )
