"""T031 — `dotnet-ai init` without `--ai` launches interactive host-selection
prompt (commit 4 / FR-014 / clarify Q4).

Asserts the cli.py init flow invokes a `questionary` checkbox prompt when
`--ai` is absent and stdin is a TTY. JSON mode and non-TTY contexts MUST
skip the prompt (CI safety).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dotnet_ai_kit.cli import _prompt_for_hosts, app

runner = CliRunner()


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def test_prompt_helper_returns_user_selection() -> None:
    """When the questionary prompt returns a list, _prompt_for_hosts must
    pass it through (lowercased)."""
    fake_qy = type("FakeQy", (), {})()

    class FakeAsk:
        def __init__(self, value: list[str]) -> None:
            self.value = value

        def ask(self) -> list[str]:
            return self.value

    class FakeChoice:
        def __init__(self, title: str, value: str, checked: bool = False) -> None:
            self.title = title
            self.value = value
            self.checked = checked

    fake_qy.Choice = FakeChoice  # type: ignore[attr-defined]
    fake_qy.checkbox = lambda _q, choices: FakeAsk(["Claude", "Codex"])  # type: ignore[attr-defined]

    with patch.dict("sys.modules", {"questionary": fake_qy}):
        result = _prompt_for_hosts(["claude"])
    assert result == ["claude", "codex"]


def test_prompt_helper_falls_back_when_user_cancels() -> None:
    """When the user picks nothing, the helper returns the auto-detected
    default (or ['claude'] if nothing detected)."""
    fake_qy = type("FakeQy", (), {})()

    class FakeAsk:
        def ask(self) -> list[str]:
            return []

    class FakeChoice:
        def __init__(self, title: str, value: str, checked: bool = False) -> None:
            self.title = title
            self.value = value
            self.checked = checked

    fake_qy.Choice = FakeChoice  # type: ignore[attr-defined]
    fake_qy.checkbox = lambda _q, choices: FakeAsk()  # type: ignore[attr-defined]

    with patch.dict("sys.modules", {"questionary": fake_qy}):
        result = _prompt_for_hosts(["claude", "codex"])
    assert result == ["claude", "codex"]


def test_init_without_ai_in_json_mode_skips_prompt(tmp_path: Path) -> None:
    """Per FR-014: JSON mode is non-interactive — no prompt MUST fire."""
    _create_dotnet_project(tmp_path)

    with patch("dotnet_ai_kit.cli._prompt_for_hosts") as mock_prompt:
        result = runner.invoke(
            app,
            ["init", str(tmp_path), "--json"],
            catch_exceptions=False,
        )

    mock_prompt.assert_not_called()
    assert result.exit_code == 0


def test_init_without_ai_in_non_tty_skips_prompt(tmp_path: Path) -> None:
    """When stdin is NOT a TTY (CI, piped), MUST skip the prompt."""
    _create_dotnet_project(tmp_path)

    with (
        patch("dotnet_ai_kit.cli._stdin_is_tty", return_value=False),
        patch("dotnet_ai_kit.cli._prompt_for_hosts") as mock_prompt,
    ):
        result = runner.invoke(app, ["init", str(tmp_path)], catch_exceptions=False)

    mock_prompt.assert_not_called()
    assert result.exit_code == 0


def test_init_without_ai_in_tty_fires_prompt(tmp_path: Path) -> None:
    """When stdin IS a TTY and --ai is absent, the prompt MUST fire."""
    _create_dotnet_project(tmp_path)

    with (
        patch("dotnet_ai_kit.cli._stdin_is_tty", return_value=True),
        patch("dotnet_ai_kit.cli._prompt_for_hosts", return_value=["claude"]) as mock_prompt,
    ):
        result = runner.invoke(app, ["init", str(tmp_path)], catch_exceptions=False)

    mock_prompt.assert_called_once()
    assert result.exit_code == 0
