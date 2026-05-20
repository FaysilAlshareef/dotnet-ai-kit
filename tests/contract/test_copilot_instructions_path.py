"""T063 — Copilot `.github/instructions/*.instructions.md` render contract.

Per `contracts/copilot-instructions-path.contract.md`: rendered ONLY for
detected project paths (from project.yml.detected_paths). Each file:
- Has `applyTo:` frontmatter with the glob pattern
- Inlines the matching domain rule body
- Includes a pointer back to `.github/copilot-instructions.md`
"""

from __future__ import annotations

from pathlib import Path

from dotnet_ai_kit.hosts.copilot import CopilotHost


def _setup_project(tmp_path: Path, detected_paths: dict[str, str]) -> Path:
    cfg = tmp_path / ".dotnet-ai-kit"
    cfg.mkdir(parents=True)
    lines = [
        "company: A",
        "domain: B",
        "side: C",
        "project_type: api",
        "dotnet_version: '9.0'",
        "detected_paths:",
    ]
    for key, val in detected_paths.items():
        lines.append(f"  {key}: '{val}'")
    (cfg / "project.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_path


def test_path_scoped_instructions_rendered_for_detected_paths(tmp_path: Path) -> None:
    """For each entry in detected_paths, a `.instructions.md` file is emitted."""
    _setup_project(tmp_path, {"testing": "tests/**", "data-access": "**/repositories/**"})
    host = CopilotHost()
    host.render(tmp_path)
    inst_dir = tmp_path / ".github" / "instructions"
    assert (inst_dir / "testing.instructions.md").is_file()
    assert (inst_dir / "data-access.instructions.md").is_file()


def test_path_scoped_instructions_carry_apply_to_frontmatter(tmp_path: Path) -> None:
    """Each rendered file has applyTo: frontmatter with the glob."""
    _setup_project(tmp_path, {"testing": "tests/**"})
    host = CopilotHost()
    host.render(tmp_path)
    body = (tmp_path / ".github" / "instructions" / "testing.instructions.md").read_text(
        encoding="utf-8"
    )
    assert body.startswith("---"), "frontmatter MUST start at line 0"
    assert "applyTo:" in body
    assert "tests/**" in body


def test_path_scoped_instructions_skip_paths_without_matching_rule(tmp_path: Path) -> None:
    """When `detected_paths` has a key with NO matching domain rule, the file
    is still rendered but `domain_rule_body` is empty (template-graceful)."""
    _setup_project(tmp_path, {"nonexistent-area": "some/**"})
    host = CopilotHost()
    host.render(tmp_path)
    # Should still render (template handles empty body)
    inst_file = tmp_path / ".github" / "instructions" / "nonexistent-area.instructions.md"
    assert inst_file.is_file()


def test_path_scoped_instructions_pointer_back_to_top_level(tmp_path: Path) -> None:
    """Each file MUST contain a pointer back to .github/copilot-instructions.md."""
    _setup_project(tmp_path, {"testing": "tests/**"})
    host = CopilotHost()
    host.render(tmp_path)
    body = (tmp_path / ".github" / "instructions" / "testing.instructions.md").read_text(
        encoding="utf-8"
    )
    assert "copilot-instructions.md" in body
