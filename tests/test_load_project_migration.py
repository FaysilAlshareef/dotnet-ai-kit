"""T034 — FR-009: load_project handles nested + legacy YAML shapes."""

from __future__ import annotations

from pathlib import Path

from dotnet_ai_kit.config import load_project


def test_nested_detected_shape(tmp_path: Path) -> None:
    p = tmp_path / "project.yml"
    p.write_text(
        "detected:\n"
        "  project_type: command\n"
        "  confidence: high\n"
        "  detected_paths:\n"
        "    aggregates: src/Foo.Commands/Aggregates\n"
        "    events: src/Foo.Commands/Events\n",
        encoding="utf-8",
    )
    proj = load_project(p)
    assert proj.project_type == "command"
    assert proj.confidence == "high"
    assert proj.detected_paths == {
        "aggregates": "src/Foo.Commands/Aggregates",
        "events": "src/Foo.Commands/Events",
    }


def test_legacy_flat_shape(tmp_path: Path) -> None:
    p = tmp_path / "project.yml"
    p.write_text(
        "project_type: command\n"
        "confidence: high\n"
        "detected_paths:\n"
        "  aggregates: src/Foo.Commands/Aggregates\n",
        encoding="utf-8",
    )
    proj = load_project(p)
    assert proj.project_type == "command"
    assert proj.detected_paths == {"aggregates": "src/Foo.Commands/Aggregates"}


def test_nested_and_legacy_equivalent(tmp_path: Path) -> None:
    nested = tmp_path / "nested.yml"
    flat = tmp_path / "flat.yml"
    nested.write_text(
        'detected:\n  project_type: generic\n  detected_paths:\n    aggregates: "src/A"\n',
        encoding="utf-8",
    )
    flat.write_text(
        'project_type: generic\ndetected_paths:\n  aggregates: "src/A"\n',
        encoding="utf-8",
    )
    a = load_project(nested)
    b = load_project(flat)
    assert a.project_type == b.project_type
    assert a.detected_paths == b.detected_paths
