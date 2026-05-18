"""T034 — SC-001: ≥90% file-count reduction after init for plugin-native hosts.

Per SC-001: a plugin-host init MUST produce ≤18 per-solution files
(vs. the feature-018 baseline of ~180 files per solution).

This is a fixture-based test — counts files written under the target
solution after `dotnet-ai init --ai claude` lands.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dotnet_ai_kit.cli import app

runner = CliRunner()

MAX_POST_INIT_FILES = 18
BASELINE_FEATURE_018_APPROX = 180  # pre-019 layout file count


def _create_dotnet_project(tmp_path: Path) -> None:
    (tmp_path / "MyApp.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "MyApp.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<TargetFramework>net8.0</TargetFramework>"
        "</PropertyGroup></Project>",
        encoding="utf-8",
    )


def _count_dotnet_ai_managed_files(target: Path) -> int:
    """Count files written under known managed paths."""
    managed_roots = (
        ".dotnet-ai-kit",
        ".claude",
        ".codex",
        ".cursor",
        ".github",
    )
    n = 0
    for root in managed_roots:
        root_path = target / root
        if not root_path.is_dir():
            continue
        for p in root_path.rglob("*"):
            if p.is_file():
                n += 1
    return n


def test_init_claude_writes_at_most_18_files(tmp_path: Path) -> None:
    """SC-001: post-init footprint for Claude plugin-native MUST be ≤18 files."""
    _create_dotnet_project(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    n = _count_dotnet_ai_managed_files(tmp_path)
    assert n <= MAX_POST_INIT_FILES, (
        f"SC-001 violation: init wrote {n} managed files, target ≤{MAX_POST_INIT_FILES}. "
        f"Listing:\n"
        + "\n".join(
            f"  {p.relative_to(tmp_path)}"
            for root in (".dotnet-ai-kit", ".claude")
            for p in (tmp_path / root).rglob("*")
            if (tmp_path / root).is_dir() and p.is_file()
        )
    )


def test_init_claude_reduction_from_baseline_is_at_least_90pct(tmp_path: Path) -> None:
    """SC-001: post-init file count MUST be ≥90% reduction from baseline."""
    _create_dotnet_project(tmp_path)

    result = runner.invoke(
        app,
        ["init", str(tmp_path), "--ai", "claude"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    n = _count_dotnet_ai_managed_files(tmp_path)
    reduction_pct = 100.0 * (BASELINE_FEATURE_018_APPROX - n) / BASELINE_FEATURE_018_APPROX
    assert reduction_pct >= 90.0, (
        f"SC-001 violation: {n} files = {reduction_pct:.1f}% reduction "
        f"from baseline ~{BASELINE_FEATURE_018_APPROX}; target ≥90%"
    )
