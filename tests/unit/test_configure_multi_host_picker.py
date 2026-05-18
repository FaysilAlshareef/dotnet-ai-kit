"""T132 (commit 17, B-6): configure interactive picker shows all 4 hosts.

Per FR-016 / CHK037 the `dotnet-ai configure` interactive flow must offer all
four supported hosts (`claude`, `codex`, `cursor`, `copilot`) as toggleable
checkboxes in the questionary multi-select. This test inspects the choices
that get passed to `questionary.checkbox` and asserts all four host values
appear.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()


def _setup_config_dir(tmp_path: Path) -> Path:
    """Create a .dotnet-ai-kit dir with a minimal config and return config_path."""
    config_dir = tmp_path / ".dotnet-ai-kit"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yml"
    config_path.write_text(
        "version: '1.0'\nai_tools:\n  - claude\npermissions_level: minimal\n"
        "command_style: both\ncompany:\n  name: ''\n  github_org: ''\n  default_branch: main\n",
        encoding="utf-8",
    )
    return config_path


def test_configure_picker_shows_all_four_hosts(tmp_path: Path, monkeypatch) -> None:
    """Configure questionary.checkbox MUST list claude/codex/cursor/copilot."""
    _setup_config_dir(tmp_path)
    monkeypatch.chdir(tmp_path)

    captured_choices: list = []

    def _capture_choice(label, value=None, checked=False, **_kw):
        captured_choices.append({"label": label, "value": value, "checked": checked})
        return label

    def _capture_checkbox(_prompt, choices=None, **_kw):
        cb = MagicMock()
        cb.ask.return_value = ["claude"]
        # remember the choices that were passed in (the unit under test)
        if choices is not None:
            for c in choices:
                # c is a return value of our patched Choice — already a label string
                # but each entry was already appended via _capture_choice
                _ = c
        return cb

    with (
        patch("dotnet_ai_kit.cli.Prompt.ask") as mock_prompt,
        patch("dotnet_ai_kit.cli.questionary") as mock_q,
    ):
        mock_prompt.side_effect = [
            "Acme",  # company name
            "acme-org",  # github org
            "main",  # default branch
            "2",  # permission level
            "3",  # command style
        ]
        mock_q.checkbox.side_effect = _capture_checkbox
        mock_q.Choice = MagicMock(side_effect=_capture_choice)

        result = runner.invoke(app, ["configure"], catch_exceptions=False)

    assert result.exit_code == 0, result.output

    host_values = [c["value"] for c in captured_choices]
    for required in ("claude", "codex", "cursor", "copilot"):
        assert required in host_values, (
            f"Configure picker missing host {required!r}; "
            f"saw values={host_values} (FR-016 / CHK037)"
        )
