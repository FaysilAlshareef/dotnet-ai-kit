"""T155 (commit 21, B-5): Copilot freshness check detects plugin-source staleness.

When the plugin source for a Copilot template changes (e.g., a managed
instructions template body is updated), `check` should report the render
as stale even if project.yml metadata is unchanged.

This is unit-level — it directly exercises
`CopilotHost.re_render_for_freshness` with a swapped plugin_root.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from dotnet_ai_kit.hosts.copilot import CopilotHost


def _build_plugin_root(plugin_root: Path, instructions_text: str = "ORIGINAL BODY\n") -> None:
    """Materialise a minimal plugin-source tree the Copilot renderer can read."""
    (plugin_root / "agents-copilot-templates").mkdir(parents=True, exist_ok=True)
    # instructions-path.md.j2
    (plugin_root / "agents-copilot-templates" / "instructions-path.md.j2").write_text(
        "---\napply_to: {{ apply_to_globs[0] }}\n---\n\n# {{ area_title }}\n\n"
        "{{ domain_rule_body }}\n",
        encoding="utf-8",
    )
    (plugin_root / "agents-copilot-templates" / "agent.md.j2").write_text(
        "---\nname: {{ name }}\n---\n\n{{ description }}\n",
        encoding="utf-8",
    )
    # rules/conventions and domain (minimal)
    (plugin_root / "rules" / "conventions").mkdir(parents=True, exist_ok=True)
    (plugin_root / "rules" / "domain").mkdir(parents=True, exist_ok=True)
    (plugin_root / "rules" / "domain" / "naming.md").write_text(
        f"## Naming Rule\n\n{instructions_text}",
        encoding="utf-8",
    )


def _build_project(project_root: Path, plugin_root: Path) -> None:
    """Init a minimal project layout."""
    cfg_dir = project_root / ".dotnet-ai-kit"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.yml").write_text(
        "company: Acme\n"
        "domain: Sales\n"
        "side: server\n"
        "project_type: generic\n"
        "architecture_branch: generic\n"
        "dotnet_version: '8.0'\n"
        "detected_paths:\n"
        "  naming: src/Naming\n",
        encoding="utf-8",
    )


def test_re_render_detects_template_body_change(tmp_path: Path) -> None:
    """Render once → snapshot hash → mutate plugin source → re-render → expect different hash."""
    project = tmp_path / "project"
    plugin = tmp_path / "plugin"
    _build_plugin_root(plugin, instructions_text="ORIGINAL BODY\n")
    _build_project(project, plugin)

    rendered_a = CopilotHost.re_render_for_freshness(
        project,
        ".github/instructions/naming.instructions.md",
        plugin_root=plugin,
    )
    assert rendered_a is not None, "re_render_for_freshness returned None on baseline render"
    sha_a = hashlib.sha256(rendered_a.encode("utf-8")).hexdigest()

    # Mutate the plugin's domain rule (source) → re-render should differ
    (plugin / "rules" / "domain" / "naming.md").write_text(
        "## Naming Rule\n\nUPDATED BODY\n",
        encoding="utf-8",
    )

    rendered_b = CopilotHost.re_render_for_freshness(
        project,
        ".github/instructions/naming.instructions.md",
        plugin_root=plugin,
    )
    assert rendered_b is not None
    sha_b = hashlib.sha256(rendered_b.encode("utf-8")).hexdigest()

    assert sha_a != sha_b, (
        f"B-5 violation: re-render produced identical SHA after source change. "
        f"sha_a={sha_a[:12]} sha_b={sha_b[:12]}"
    )
