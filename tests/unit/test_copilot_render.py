"""T065 — Copilot render coverage (commit 7).

Asserts the Copilot render orchestrator covers the 3 logical content classes
per FR-007 / CHK019:
1. Repository-wide instructions (`.github/copilot-instructions.md`)
2. Path-scoped instructions (`.github/instructions/*.instructions.md`)
3. Per-agent custom-agent files (`.github/agents/*.agent.md`)

This test exercises the v1 minimal scope (only #1 is rendered in the
initial commit-7 implementation; #2 and #3 are staged follow-up).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.hosts.copilot import CopilotHost


def test_render_returns_result_object(tmp_path: Path) -> None:
    """The render orchestrator returns a `CopilotRenderResult` with partitions."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    result = CopilotHost().render(project_root)

    # Default partitions exist
    assert hasattr(result, "written")
    assert hasattr(result, "preserved")
    assert hasattr(result, "force_rendered")
    assert hasattr(result, "pending_user_consent")


def test_render_creates_minimal_content(tmp_path: Path) -> None:
    """Rendered file has the 4 required content sections per contract:33."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    CopilotHost().render(project_root)

    content = (project_root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")

    # Required sections per the contract
    assert "Project identity" in content
    assert "conventions" in content.lower()  # always-on conventions section
    assert "Path-scoped guidance" in content
    assert "Per-agent quick reference" in content


def test_render_substitutes_project_metadata(tmp_path: Path) -> None:
    """Render reads project metadata when present and substitutes values."""
    import yaml

    project_root = tmp_path / "project"
    config_dir = project_root / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)

    project_yml = config_dir / "project.yml"
    project_yml.write_text(
        yaml.dump(
            {
                "detected": {
                    "company": "ContosoCorp",
                    "domain": "Sales",
                    "side": "server",
                    "project_type": "command",
                    "architecture_branch": "microservice",
                    "detected_paths": {"controllers": "src/Web"},
                    "dotnet_version": "10.0",
                }
            }
        ),
        encoding="utf-8",
    )

    CopilotHost().render(project_root)

    content = (project_root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert "ContosoCorp" in content
    assert "Sales" in content


@pytest.mark.parametrize(
    "template_path",
    [
        "agents-copilot-templates/copilot-instructions.md.j2",
        "agents-copilot-templates/instructions-path.md.j2",
        "agents-copilot-templates/agent.md.j2",
    ],
)
def test_copilot_templates_exist_in_source(template_path: str) -> None:
    """The 3 jinja2 templates MUST exist under agents-copilot-templates/."""
    repo = Path(__file__).resolve().parent.parent.parent
    target = repo / template_path
    assert target.is_file(), f"Copilot template missing: {target}"


def test_render_emits_path_scoped_instructions(tmp_path: Path) -> None:
    """Per FR-007 / T070: `.github/instructions/*.instructions.md` files for
    each detected_paths entry in project.yml."""
    import yaml

    project_root = tmp_path / "project"
    config_dir = project_root / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)
    (config_dir / "project.yml").write_text(
        yaml.dump(
            {
                "company": "A",
                "domain": "B",
                "side": "C",
                "project_type": "api",
                "dotnet_version": "9.0",
                "detected_paths": {"testing": "tests/**"},
            }
        ),
        encoding="utf-8",
    )
    CopilotHost().render(project_root)
    instructions_dir = project_root / ".github" / "instructions"
    assert instructions_dir.is_dir() and any(instructions_dir.iterdir())


def test_render_emits_per_agent_files(tmp_path: Path) -> None:
    """Per FR-007 / T070: `.github/agents/*.agent.md` files for each agent
    in `agents-source/`."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    CopilotHost().render(project_root)
    agents_dir = project_root / ".github" / "agents"
    assert agents_dir.is_dir() and any(agents_dir.glob("*.agent.md"))
