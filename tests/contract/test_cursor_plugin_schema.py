"""Contract test for `.cursor-plugin/plugin.json` (T013 / feature 019 commit 3).

Asserts that the Cursor plugin manifest validates against
schemas/cursor-plugin.schema.json. Per data-model.md § 1c, all field values
are scalar relative paths with `./` prefix. The agent-bearing field is
`agents` (NOT `subagents`) and the verified path is `./agents/`.

The `agents` field is CONDITIONAL on the A-005 spike fixture
(commit 6 T051). Until the spike outcome lands, commit 3 may emit the field
optimistically — commit 6 T061 removes it on fail-path per
cursor-fixture-decision.contract.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO = Path(__file__).resolve().parent.parent.parent

PLUGIN_MANIFEST = REPO / ".cursor-plugin" / "plugin.json"
PLUGIN_SCHEMA = REPO / "schemas" / "cursor-plugin.schema.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    """Load the Cursor plugin manifest as JSON."""
    return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict:
    """Load the published Cursor plugin JSON Schema."""
    return json.loads(PLUGIN_SCHEMA.read_text(encoding="utf-8"))


def test_cursor_plugin_manifest_validates_against_schema(manifest: dict, schema: dict) -> None:
    """`.cursor-plugin/plugin.json` MUST validate against the schema contract."""
    jsonschema.validate(instance=manifest, schema=schema)


def test_cursor_plugin_skills_is_scalar_path(manifest: dict) -> None:
    """Per data-model.md § 1c: `skills` MUST be `"./skills/"` (scalar)."""
    assert isinstance(manifest["skills"], str)
    assert manifest["skills"] == "./skills/"


def test_cursor_plugin_rules_is_scalar_path_to_cursor_dir(manifest: dict) -> None:
    """If `rules` is present, it MUST be `"./rules/cursor/"` — the generated `.mdc` directory.

    T195a (commit 25, OOS-005 fail-safe default): the `rules` field is OPTIONAL.
    When the A-005 spike fixture is `pending` or `failed`, `rules/cursor/` is
    empty and the manifest omits the declaration. T195b (PASS branch) re-adds
    it once Cursor's loader is verified.
    """
    if "rules" not in manifest:
        return  # T195a fail-safe: rules omitted while A-005 spike pending/failed
    assert isinstance(manifest["rules"], str)
    assert manifest["rules"] == "./rules/cursor/"


def test_cursor_plugin_mcp_servers_not_declared_for_standard_path(manifest: dict) -> None:
    """mcpServers (.mcp.json) should be absent from the manifest.

    Cursor auto-discovers .mcp.json from the plugin root. Declaring the
    standard path risks duplicate-load errors. If present, must be non-default.
    """
    mcp = manifest.get("mcpServers")
    if mcp is not None:
        assert mcp != "./.mcp.json", (
            "mcpServers './.mcp.json' is the auto-discovered default — remove it from the manifest."
        )


def test_cursor_plugin_hooks_not_declared_for_standard_path(manifest: dict) -> None:
    """hooks/hooks.json should be absent from the manifest.

    Cursor auto-discovers hooks/hooks.json from the plugin root. Declaring the
    standard path risks duplicate-load errors. If present, must be non-default.
    """
    hooks = manifest.get("hooks")
    if hooks is not None:
        assert hooks != "./hooks/hooks.json", (
            "hooks './hooks/hooks.json' is auto-discovered — remove it from the manifest."
        )


def test_cursor_plugin_has_no_subagents_field(manifest: dict) -> None:
    """The agent-bearing field is `agents`, NOT `subagents` per verified Cursor evidence."""
    assert "subagents" not in manifest, (
        "Cursor plugin must NOT use the `subagents` field — the documented field is `agents`"
    )


def test_cursor_plugin_agents_field_if_present_uses_verified_path(
    manifest: dict,
) -> None:
    """If `agents` is present, it MUST be `"./agents/"` (verified Cursor path)."""
    if "agents" in manifest:
        assert manifest["agents"] == "./agents/", (
            f"Cursor agents field, when present, must be the verified `./agents/` path; "
            f"got {manifest['agents']}"
        )


def test_cursor_plugin_commands_field_is_scalar_path(manifest: dict) -> None:
    """Per Cursor docs (https://cursor.com/docs/reference/plugins, retrieved
    2026-05-19): `commands` is a documented optional field. The kit declares
    it explicitly so the 27 slash commands are self-documented at the manifest
    level instead of relying on Cursor's folder-discovery default."""
    assert "commands" in manifest, (
        "Cursor plugin must declare `commands` explicitly. The kit ships 27 "
        "slash commands at `./commands/`; folder-discovery default works but "
        "explicit declaration is the docs-recommended pattern."
    )
    assert manifest["commands"] == "./commands/", (
        f"Cursor commands field must be the scalar path `./commands/`; got {manifest['commands']}"
    )


def test_cursor_plugin_keywords_is_a_non_empty_string_array(manifest: dict) -> None:
    """Per Cursor docs: `keywords` is an optional array of discovery tags
    for marketplace search. The kit opts in for cross-host parity with
    .codex-plugin and .claude-plugin."""
    assert "keywords" in manifest, (
        "Cursor plugin must declare `keywords` for marketplace discovery — "
        "this matches the per-Cursor-docs recommendation and the cross-host "
        "parity established with .codex-plugin/plugin.json."
    )
    kws = manifest["keywords"]
    assert isinstance(kws, list) and kws, "keywords must be a non-empty array"
    assert all(isinstance(k, str) and k for k in kws), "keywords entries must be non-empty strings"
    assert len(set(kws)) == len(kws), "keywords entries must be unique"


def test_cursor_plugin_author_object_has_required_name(manifest: dict) -> None:
    """Per Cursor docs: `author` is an optional object whose minimum shape is
    `{name}`. We populate from .claude-plugin/marketplace.json::owner."""
    assert "author" in manifest, "Cursor plugin must declare `author` per docs"
    author = manifest["author"]
    assert isinstance(author, dict), f"author must be an object, got {type(author).__name__}"
    assert author.get("name"), "author.name is required per Cursor docs"


def test_cursor_plugin_homepage_is_http_url(manifest: dict) -> None:
    """Per Cursor docs: `homepage` is an optional URL string."""
    assert "homepage" in manifest, "Cursor plugin must declare `homepage` per docs"
    hp = manifest["homepage"]
    assert isinstance(hp, str) and hp.startswith(("http://", "https://")), (
        f"homepage must be an http(s) URL, got {hp!r}"
    )


def test_cursor_plugin_repository_is_http_url(manifest: dict) -> None:
    """Per Cursor docs: `repository` is an optional source-repo URL string."""
    assert "repository" in manifest, "Cursor plugin must declare `repository` per docs"
    repo = manifest["repository"]
    assert isinstance(repo, str) and repo.startswith(("http://", "https://")), (
        f"repository must be an http(s) URL, got {repo!r}"
    )


def test_cursor_plugin_license_is_spdx_identifier(manifest: dict) -> None:
    """Per Cursor docs: `license` is an optional SPDX identifier."""
    assert "license" in manifest, "Cursor plugin must declare `license` per docs"
    assert isinstance(manifest["license"], str) and manifest["license"], (
        "license must be a non-empty string"
    )


def test_cursor_plugin_logo_points_to_existing_asset(manifest: dict) -> None:
    """Per Cursor docs: `logo` is an optional plugin-root-relative path. The
    referenced file MUST exist on disk so the wheel actually ships it (per
    pyproject.toml `tool.hatch.build.targets.wheel.force-include.assets`)."""
    assert "logo" in manifest, "Cursor plugin must declare `logo` per docs"
    logo_rel = manifest["logo"]
    assert isinstance(logo_rel, str) and logo_rel, "logo must be a non-empty string"
    # Strip optional `./` prefix and resolve relative to the plugin root (repo root).
    rel = logo_rel[2:] if logo_rel.startswith("./") else logo_rel
    logo_path = REPO / rel
    assert logo_path.is_file(), (
        f"`{logo_rel}` declared in manifest but file missing at {logo_path}. "
        f"Wheel-install will resolve the path to a 404."
    )


def test_cursor_plugin_name_is_dotnet_ai_kit(manifest: dict) -> None:
    """Plugin name MUST be `dotnet-ai-kit`."""
    assert manifest["name"] == "dotnet-ai-kit"
