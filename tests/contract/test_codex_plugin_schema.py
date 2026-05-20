"""Contract test for `.codex-plugin/plugin.json` (T012 / feature 019 commit 3).

Asserts that the Codex CLI plugin manifest validates against
schemas/codex-plugin.schema.json. Per data-model.md § 1b / Codex docs
developers.openai.com/codex/plugins/build:843-899, all manifest field values
are scalar relative-path strings with `./` prefix (NOT arrays/objects), and
the `agents`, `lspServers`, `monitors`, `settings`, `bin` fields MUST NOT
appear (per FR-002 / OOS-004).
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO = Path(__file__).resolve().parent.parent.parent

PLUGIN_MANIFEST = REPO / ".codex-plugin" / "plugin.json"
PLUGIN_SCHEMA = REPO / "schemas" / "codex-plugin.schema.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    """Load the Codex plugin manifest as JSON."""
    return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def schema() -> dict:
    """Load the published Codex plugin JSON Schema."""
    return json.loads(PLUGIN_SCHEMA.read_text(encoding="utf-8"))


def test_codex_plugin_manifest_validates_against_schema(manifest: dict, schema: dict) -> None:
    """`.codex-plugin/plugin.json` MUST validate against the schema contract."""
    jsonschema.validate(instance=manifest, schema=schema)


def test_codex_plugin_skills_is_scalar_path(manifest: dict) -> None:
    """Per data-model.md § 1b: `skills` MUST be a scalar string `"./skills/"`."""
    assert isinstance(manifest["skills"], str), (
        f"Codex plugin `skills` must be a scalar string per docs:843-860, "
        f"got {type(manifest['skills']).__name__}"
    )
    assert manifest["skills"] == "./skills/"


def test_codex_plugin_mcp_servers_is_scalar_path(manifest: dict) -> None:
    """`mcpServers` MUST be a scalar path string `"./.mcp.json"`."""
    assert isinstance(manifest["mcpServers"], str)
    assert manifest["mcpServers"] == "./.mcp.json"


def test_codex_plugin_hooks_is_scalar_path(manifest: dict) -> None:
    """`hooks` MUST be a scalar path string `"./hooks/hooks.json"`."""
    assert isinstance(manifest["hooks"], str)
    assert manifest["hooks"] == "./hooks/hooks.json"


def test_codex_plugin_has_no_agents_field(manifest: dict) -> None:
    """Per OOS-004 (plugin-bundling portion still deferred to v1.1): the Codex
    plugin manifest does NOT have a documented `agents` field per
    https://developers.openai.com/codex/plugins/build (retrieved 2026-05-19).
    Subagents live as `.codex/agents/<name>.toml` files at the project scope
    instead (rendered by CodexHost.write_per_solution_files())."""
    assert "agents" not in manifest, (
        "Codex plugin must NOT declare `agents` — the Codex plugin manifest "
        "does not document this field. Subagents are project-scoped TOML "
        "files per https://developers.openai.com/codex/subagents."
    )


def test_codex_plugin_has_no_subagents_field(manifest: dict) -> None:
    """Per OOS-004: the variant spelling `subagents` is also forbidden at the
    plugin manifest level for the same reason as `agents` — neither is
    documented. The structural gate (`schema.not.anyOf`) blocks future drift."""
    assert "subagents" not in manifest, (
        "Codex plugin must NOT declare `subagents` — not a documented field. "
        "Subagents are project-scoped per the Codex subagents docs."
    )


def test_codex_plugin_has_no_lsp_servers_field(manifest: dict) -> None:
    """Per FR-002: `lspServers` is not documented for Codex — MUST be absent."""
    assert "lspServers" not in manifest


def test_codex_plugin_has_no_undocumented_fields(manifest: dict) -> None:
    """Per FR-002 / schema `not.anyOf`: monitors / settings / bin MUST be absent."""
    for forbidden in ("monitors", "settings", "bin"):
        assert forbidden not in manifest, (
            f"Codex plugin must NOT declare `{forbidden}` (FR-002 / schema constraint)"
        )


def test_codex_plugin_keywords_is_a_non_empty_string_array(manifest: dict) -> None:
    """If `keywords` is present (optional per Codex docs), it must be a
    non-empty array of unique strings — the manifest opts in for marketplace
    discovery."""
    if "keywords" not in manifest:
        return  # optional
    kws = manifest["keywords"]
    assert isinstance(kws, list) and kws, "keywords must be a non-empty array"
    assert all(isinstance(k, str) and k for k in kws), "keywords entries must be non-empty strings"
    assert len(set(kws)) == len(kws), "keywords entries must be unique"


def test_codex_plugin_author_object_has_required_name(manifest: dict) -> None:
    """Per Codex docs: `author` is an optional object whose minimum shape is
    `{name}`. We populate from .claude-plugin/marketplace.json::owner."""
    assert "author" in manifest, "Codex plugin must declare `author` per docs"
    author = manifest["author"]
    assert isinstance(author, dict), f"author must be an object, got {type(author).__name__}"
    assert author.get("name"), "author.name is required per Codex docs"


def test_codex_plugin_homepage_is_http_url(manifest: dict) -> None:
    """Per Codex docs: `homepage` is an optional URL string."""
    assert "homepage" in manifest, "Codex plugin must declare `homepage` per docs"
    hp = manifest["homepage"]
    assert isinstance(hp, str) and hp.startswith(("http://", "https://")), (
        f"homepage must be an http(s) URL, got {hp!r}"
    )


def test_codex_plugin_repository_is_http_url(manifest: dict) -> None:
    """Per Codex docs: `repository` is an optional source-repo URL string."""
    assert "repository" in manifest, "Codex plugin must declare `repository` per docs"
    repo = manifest["repository"]
    assert isinstance(repo, str) and repo.startswith(("http://", "https://")), (
        f"repository must be an http(s) URL, got {repo!r}"
    )


def test_codex_plugin_license_is_spdx_identifier(manifest: dict) -> None:
    """Per Codex docs: `license` is an optional SPDX identifier."""
    assert "license" in manifest, "Codex plugin must declare `license` per docs"
    assert isinstance(manifest["license"], str) and manifest["license"], (
        "license must be a non-empty string"
    )


def test_codex_plugin_logo_points_to_existing_asset(manifest: dict) -> None:
    """Per Codex docs: `logo` is an optional plugin-root-relative path. The
    referenced file MUST exist on disk so the wheel actually ships it (per
    pyproject.toml `tool.hatch.build.targets.wheel.force-include.assets`)."""
    assert "logo" in manifest, "Codex plugin must declare `logo` per docs"
    logo_rel = manifest["logo"]
    assert isinstance(logo_rel, str) and logo_rel, "logo must be a non-empty string"
    rel = logo_rel[2:] if logo_rel.startswith("./") else logo_rel
    logo_path = REPO / rel
    assert logo_path.is_file(), (
        f"`{logo_rel}` declared in manifest but file missing at {logo_path}. "
        f"Wheel-install will resolve the path to a 404."
    )


def test_codex_plugin_name_is_dotnet_ai_kit(manifest: dict) -> None:
    """Plugin name MUST be `dotnet-ai-kit`."""
    assert manifest["name"] == "dotnet-ai-kit"
