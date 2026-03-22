"""Detection helpers for dotnet-ai-kit.

Project type detection is now handled by the AI smart-detect skill
(skills/detection/smart-detect/SKILL.md) and the /dotnet-ai.detect command.

This module provides only helper utilities used by other parts of the codebase.
"""

from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dotnet_ai_kit.models import DetectedProject


class DetectionError(Exception):
    """Raised when project detection fails."""


# ---------------------------------------------------------------------------
# grep helpers
# ---------------------------------------------------------------------------


def grep_file(file_path: Path, pattern: str) -> list[str]:
    """Search a file's contents for lines matching a regex pattern.

    Args:
        file_path: Path to the file to search.
        pattern: Regular expression pattern to search for.

    Returns:
        List of matching lines (stripped). Empty list if file cannot be read.
    """
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    compiled = re.compile(pattern)
    return [line.strip() for line in text.splitlines() if compiled.search(line)]


def grep_files(directory: Path, pattern: str, glob_pattern: str = "*.cs") -> list[str]:
    """Search all matching files in a directory tree for a regex pattern.

    Args:
        directory: Root directory to search.
        pattern: Regular expression pattern.
        glob_pattern: File glob pattern (default: *.cs).

    Returns:
        List of matching lines across all files.
    """
    matches: list[str] = []
    for file_path in directory.rglob(glob_pattern):
        matches.extend(grep_file(file_path, pattern))
    return matches


# ---------------------------------------------------------------------------
# Architecture descriptions
# ---------------------------------------------------------------------------


def describe_architecture(mode: str, project_type: str) -> str:
    """Produce a human-readable architecture description."""
    descriptions = {
        "command": "Event-sourced Command service (CQRS write side)",
        "query-sql": "SQL Server Query service (CQRS read side)",
        "query-cosmos": "Cosmos DB Query service (CQRS read side)",
        "processor": "Background event Processor service",
        "gateway": "REST API Gateway with gRPC backends",
        "controlpanel": "Blazor WASM Control Panel",
        "hybrid": "Hybrid CQRS service (command + query in same project)",
        "vsa": "Vertical Slice Architecture",
        "clean-arch": "Clean Architecture",
        "ddd": "Domain-Driven Design",
        "modular-monolith": "Modular Monolith",
        "generic": "Generic .NET project",
    }
    return descriptions.get(project_type, f"{mode} - {project_type}")


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def display_detection_summary(result: DetectedProject, console: Console) -> None:
    """Display a rich Panel summarizing detection results.

    Args:
        result: The detected project information.
        console: Rich Console instance for output.
    """
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="bold")
    table.add_column("Value")

    table.add_row("Mode", result.mode)
    table.add_row("Project Type", result.project_type)
    table.add_row("Architecture", result.architecture)
    table.add_row(".NET Version", result.dotnet_version or "(not detected)")

    confidence_style = {
        "high": "green",
        "medium": "yellow",
        "low": "red",
    }.get(result.confidence, "dim")

    confidence_display = result.confidence or "unknown"
    if result.confidence_score > 0:
        confidence_display += f" ({result.confidence_score:.0%})"
    table.add_row("Confidence", f"[{confidence_style}]{confidence_display}[/{confidence_style}]")

    if result.top_signals:
        signal_lines: list[str] = []
        for i, sig in enumerate(result.top_signals[:3], 1):
            neg = " (negative)" if sig.get("is_negative") else ""
            signal_lines.append(
                f"  {i}. {sig.get('pattern_name', '?')} "
                f"[dim]({sig.get('confidence', '?')}{neg})[/dim]"
            )
        table.add_row("Top Signals", "\n".join(signal_lines))

    if result.user_override:
        table.add_row("User Override", result.user_override)

    panel = Panel(
        table,
        title="Detection Summary",
        border_style="blue",
        expand=False,
    )
    console.print(panel)
