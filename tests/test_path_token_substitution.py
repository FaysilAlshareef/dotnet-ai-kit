"""T035 — FR-010 / FR-033 / SC-006 / SC-016: path-token substitution safety."""

from __future__ import annotations

import pytest

from dotnet_ai_kit.copier import DeploymentError, _resolve_detected_path_tokens

CONTENT = """---
name: aggregate-design
paths: ${detected_paths.aggregates}/**/*.cs
---
# body
"""


def test_all_keys_present_substituted() -> None:
    out = _resolve_detected_path_tokens(CONTENT, {"aggregates": "src/Foo.Commands/Aggregates"})
    assert "${detected_paths." not in out
    assert "src/Foo.Commands/Aggregates" in out


def test_missing_key_raises_deployment_error() -> None:
    with pytest.raises(DeploymentError) as exc:
        _resolve_detected_path_tokens(CONTENT, {})
    assert "aggregates" in str(exc.value)


def test_extra_unused_keys_ignored() -> None:
    out = _resolve_detected_path_tokens(
        CONTENT,
        {"aggregates": "src/A", "events": "src/E", "handlers": "src/H"},
    )
    assert "${detected_paths." not in out
    assert "src/A" in out


def test_empty_value_treated_as_missing() -> None:
    with pytest.raises(DeploymentError):
        _resolve_detected_path_tokens(CONTENT, {"aggregates": ""})
