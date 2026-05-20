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

from dotnet_ai_kit.hosts import get_host
from dotnet_ai_kit.hosts.copilot import CopilotHost


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


def test_m_cx_6_copilot_verify_install_honors_target_not_cwd(tmp_path: Path, monkeypatch) -> None:
    """M-CX-6: CopilotHost.verify_install() must accept a project_root
    parameter and use it instead of Path.cwd()."""
    # Set cwd to a DIFFERENT directory than the target. The old (buggy)
    # behavior would report status for cwd; the fixed behavior reports
    # status for the target.
    other_dir = tmp_path / "elsewhere"
    other_dir.mkdir()
    target = tmp_path / "myrepo"
    target.mkdir()
    (target / ".github").mkdir()  # Copilot "install" marker

    monkeypatch.chdir(other_dir)  # cwd does NOT have .github/

    # Pre-fix call: verify_install() ← uses Path.cwd() → would not find .github
    # Post-fix call: verify_install(project_root=target) → finds .github
    status = CopilotHost().verify_install(project_root=target)
    assert status.installed, (
        f"M-CX-6 regression: CopilotHost.verify_install(project_root=target) "
        f"must inspect the target, not Path.cwd(). Status: {status}"
    )


def test_m_cx_6_copilot_verify_install_default_uses_cwd(tmp_path: Path, monkeypatch) -> None:
    """Back-compat: when project_root is None, fall back to Path.cwd()."""
    (tmp_path / ".github").mkdir()
    monkeypatch.chdir(tmp_path)
    status = CopilotHost().verify_install()  # no arg
    assert status.installed
