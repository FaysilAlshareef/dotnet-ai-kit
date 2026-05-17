"""T062 — Copilot instructions render contract (commit 7).

Asserts the `.github/copilot-instructions.md` rendered structure per
`contracts/copilot-instructions.contract.md`:

1. Required content blocks: project identity, always-on conventions,
   path-scoped pointers, architecture profile, per-agent quick reference.
2. Path collision rules per FR-008 / A-008: pre-existing file preserved.
3. The render is recorded in the managed-file manifest with
   `host_owner: "copilot"` (manifest write happens in commit 10 migrate
   wiring — this test asserts the render-side contract only).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dotnet_ai_kit.hosts import get_host
from dotnet_ai_kit.hosts.copilot import CopilotHost, CopilotRenderResult


def test_copilot_host_registered() -> None:
    """CopilotHost MUST be registered alongside the other 3 hosts."""
    host = get_host("copilot")
    assert isinstance(host, CopilotHost)
    assert host.name == "copilot"


def test_copilot_render_writes_instructions_to_github_dir(tmp_path: Path) -> None:
    """Render writes `.github/copilot-instructions.md` per FR-007."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    host = CopilotHost()
    result = host.render(project_root)

    instructions = project_root / ".github" / "copilot-instructions.md"
    assert instructions.is_file()
    assert instructions in result.written


def test_copilot_render_preserves_existing_file_by_default(tmp_path: Path) -> None:
    """FR-008: pre-existing developer file MUST be preserved, render blocked."""
    project_root = tmp_path / "project"
    (project_root / ".github").mkdir(parents=True)
    existing = project_root / ".github" / "copilot-instructions.md"
    user_content = "# User authored instructions\nDO NOT TOUCH\n"
    existing.write_text(user_content, encoding="utf-8")

    host = CopilotHost()
    result = host.render(project_root)

    # User file preserved verbatim
    assert existing.read_text(encoding="utf-8") == user_content
    assert existing in result.pending_user_consent
    assert result.has_conflicts


def test_copilot_render_force_overrides_existing(tmp_path: Path) -> None:
    """--force-render allows explicit opt-in to overwrite a specific file."""
    project_root = tmp_path / "project"
    (project_root / ".github").mkdir(parents=True)
    existing = project_root / ".github" / "copilot-instructions.md"
    existing.write_text("# User authored\n", encoding="utf-8")

    host = CopilotHost()
    result = host.render(project_root, force_render_paths=[existing])

    # File now reflects the tool's render
    new_content = existing.read_text(encoding="utf-8")
    assert "Repository-wide Copilot Instructions" in new_content
    assert existing in result.force_rendered


def test_copilot_render_creates_github_dir_if_missing(tmp_path: Path) -> None:
    """Render creates `.github/` if missing (default behavior)."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    assert not (project_root / ".github").exists()

    CopilotHost().render(project_root)

    assert (project_root / ".github").is_dir()


def test_copilot_install_paths_empty_per_fr_004() -> None:
    """Copilot has NO plugin install path per FR-004."""
    paths = CopilotHost().install_paths()
    assert paths == []


def test_copilot_verify_install_reports_github_presence(tmp_path: Path) -> None:
    """`verify_install` returns installed=True iff `.github/` exists in cwd.

    Uses monkeypatch on cwd to isolate the test.
    """
    import os

    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".github").mkdir()

    cwd_before = os.getcwd()
    try:
        os.chdir(project_root)
        status = CopilotHost().verify_install()
        assert status.installed is True
    finally:
        os.chdir(cwd_before)
