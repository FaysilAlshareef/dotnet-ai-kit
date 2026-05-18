"""T032 — FR-014 / FR-016: end-to-end init with interactive prompt.

Asserts:
(a) Interactive prompt shows all 4 supported hosts (CHK037).
(b) Selecting a subset writes per-solution files only for selected hosts
    (CHK038).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dotnet_ai_kit.agents import SUPPORTED_AI_TOOLS
from dotnet_ai_kit.cli import app

runner = CliRunner()


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text(
        "Microsoft Visual Studio Solution File\n", encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_prompt_offers_all_four_supported_hosts() -> None:
    """CHK037: the interactive prompt MUST offer all 4 hosts in
    SUPPORTED_AI_TOOLS (claude, codex, cursor, copilot)."""
    observed_choices: list[str] = []

    fake_qy = type("FakeQy", (), {})()

    class FakeAsk:
        def ask(self) -> list[str]:
            return ["claude"]

    class FakeChoice:
        def __init__(self, title: str, value: str, checked: bool = False) -> None:
            self.title = title
            self.value = value
            self.checked = checked
            observed_choices.append(value)

    def fake_checkbox(_q: str, choices: list) -> object:
        # choices is already built — values were captured in __init__
        return FakeAsk()

    fake_qy.Choice = FakeChoice  # type: ignore[attr-defined]
    fake_qy.checkbox = fake_checkbox  # type: ignore[attr-defined]

    with patch.dict("sys.modules", {"questionary": fake_qy}):
        from dotnet_ai_kit.cli import _prompt_for_hosts  # noqa: PLC0415

        _prompt_for_hosts(["claude"])

    assert set(observed_choices) == set(SUPPORTED_AI_TOOLS), (
        f"prompt offered hosts {observed_choices}, expected SUPPORTED_AI_TOOLS"
    )


def test_init_with_subset_writes_only_selected_hosts(tmp_path: Path) -> None:
    """CHK038: init --ai with a subset of hosts MUST NOT write files for
    unselected hosts.

    With --ai claude only, the .codex-plugin / .cursor-plugin paths in the
    target solution MUST stay absent.
    """
    _create_dotnet_project(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Plugin-native hosts: NO per-solution files except `.claude/settings.json`
    # if permissions were set. The marker we check is the host-specific
    # per-solution directories that would only exist if init wrote there.
    # For unselected hosts (codex, cursor, copilot), NO host-specific files
    # should be created by init.
    assert not (tmp_path / ".codex").is_dir(), (
        "init --ai claude MUST NOT create .codex/ for unselected host"
    )
    # .cursor/ would be created if cursor was selected; absent for claude-only
    assert not (tmp_path / ".cursor").is_dir(), (
        "init --ai claude MUST NOT create .cursor/ for unselected host"
    )
    # .github/copilot-instructions.md (copilot render) should not exist
    assert not (tmp_path / ".github" / "copilot-instructions.md").is_file(), (
        "init --ai claude MUST NOT render .github/copilot-instructions.md "
        "for unselected copilot host"
    )
