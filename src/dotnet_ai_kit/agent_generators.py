"""Per-host agent generators (feature 019 / FR-026 / FR-027 / T041).

Each generator takes a single source-of-truth agent markdown (under
`agents-source/<name>.md`) and emits the host-specific shape:

- `generate_claude_agent(source_path) -> str`: Claude allow-list frontmatter
  + verbatim body. Output target: `agents-claude/<name>.md`.
- `generate_codex_agent(source_path) -> str`: Codex subagent TOML body
  per `https://developers.openai.com/codex/subagents`. Output target:
  `.codex/agents/<name>.toml` (per-project, written by `CodexHost`).
  OOS-004 partial lift (May 2026): plugin-manifest-bundled subagents
  remain deferred (Codex docs don't support an `agents` field); per-project
  subagent files ARE supported and shipped here.
- `generate_cursor_agent(source_path) -> str`: Cursor allow-list frontmatter
  + verbatim body. Output target: `agents/<name>.md` (Cursor's manifest
  path). Added in commit 6 (T058).
- `generate_copilot_agent(source_path, project_metadata) -> str`: Copilot
  allow-list frontmatter + interpolated body. Output target:
  `.github/agents/<name>.agent.md`. Added in commit 7 (T071).

All generators:
- Use the markdown body verbatim (T037 invariant: body identical across hosts).
- Reject `host_overrides.<other>` keys leaking into this host's output.
- Per FR-027: NEVER emit a Claude `skills:` preload field.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Frontmatter parsing helpers
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)\Z", re.DOTALL)


@dataclass
class AgentSource:
    """A parsed source-of-truth agent file (per data-model.md § 7)."""

    name: str
    description: str
    frontmatter: dict
    body: str
    source_path: Path

    @classmethod
    def from_file(cls, path: Path) -> AgentSource:
        """Load and parse an agent markdown file.

        Raises ValueError if the file lacks the required `name`/`description`
        frontmatter or has a malformed structure.
        """
        text = path.read_text(encoding="utf-8")
        match = _FRONTMATTER_RE.match(text)
        if not match:
            raise ValueError(
                f"Agent file {path} has no YAML frontmatter. Expected '---' "
                f"delimiters at file start."
            )
        try:
            fm = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Agent file {path} has invalid frontmatter YAML: {exc}") from exc

        if not isinstance(fm, dict):
            raise ValueError(f"Agent file {path} frontmatter must be a YAML mapping")

        name = fm.get("name")
        description = fm.get("description")
        if not name or not isinstance(name, str):
            raise ValueError(f"Agent file {path} missing required `name` string in frontmatter")
        if not description or not isinstance(description, str):
            raise ValueError(
                f"Agent file {path} missing required `description` string in frontmatter"
            )

        body = match.group(2)
        return cls(
            name=name,
            description=description,
            frontmatter=fm,
            body=body,
            source_path=path,
        )


# ---------------------------------------------------------------------------
# Host-specific allow-lists per `contracts/agent-source.contract.md`
# ---------------------------------------------------------------------------
#
# Each set is the union of (the contract's base fields {name, description})
# and the documented allow-list fields for that host.

_CLAUDE_ALLOW_LIST: frozenset[str] = frozenset(
    {"name", "description", "role", "expertise", "complexity", "max_iterations"}
)

_CURSOR_ALLOW_LIST: frozenset[str] = frozenset({"name", "description", "model", "readonly"})

# Codex subagent allow-list per `https://developers.openai.com/codex/subagents`
# (retrieved 2026-05-19). The Codex docs document these optional fields on top
# of the required {name, description, developer_instructions} triplet.
# `nickname_candidates` (array) and `skills_config` (sub-table) are
# documented but deferred to a follow-up commit — no current source agent
# uses them.
_CODEX_ALLOW_LIST: frozenset[str] = frozenset(
    {"name", "description", "model", "model_reasoning_effort", "sandbox_mode", "mcp_servers"}
)

_COPILOT_ALLOW_LIST: frozenset[str] = frozenset(
    {
        "name",
        "description",
        "target",
        "tools",
        "model",
        "disable-model-invocation",
        "user-invocable",
        "mcp-servers",
        "metadata",
    }
)


def _render_frontmatter(fields: dict) -> str:
    """Render an ordered frontmatter dict to a YAML block with `---` delimiters."""
    body = yaml.dump(fields, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return f"---\n{body}---\n\n"


def _build_host_frontmatter(src: AgentSource, host: str, allow_list: frozenset[str]) -> dict:
    """Compose the host's frontmatter from the source's name/description plus
    its `host_overrides.<host>` fields.

    Per FR-027: unknown fields are rejected.
    Per FR-027 (regression guard): Claude path MUST NOT emit `skills:`.
    """
    fm: dict = {"name": src.name, "description": src.description}

    host_overrides = src.frontmatter.get("host_overrides", {}) or {}
    if not isinstance(host_overrides, dict):
        raise ValueError(
            f"{src.source_path}: `host_overrides` must be a mapping if present, "
            f"got {type(host_overrides).__name__}"
        )

    host_fields = host_overrides.get(host, {}) or {}
    if not isinstance(host_fields, dict):
        raise ValueError(
            f"{src.source_path}: `host_overrides.{host}` must be a mapping, "
            f"got {type(host_fields).__name__}"
        )

    for key, value in host_fields.items():
        if key not in allow_list:
            raise ValueError(
                f"{src.source_path}: `host_overrides.{host}.{key}` is not in the "
                f"documented allow-list for host '{host}'. Allowed: "
                f"{sorted(allow_list - {'name', 'description'})}. (per FR-027)"
            )
        fm[key] = value

    # FR-027 regression guard: Claude has no `skills:` agent field; lifting
    # `expertise` (a Claude-allow-listed field) into `skills` is forbidden.
    if host == "claude":
        assert "skills" not in fm, "FR-027 regression: Claude agent must not emit `skills:` field"

    return fm


# ---------------------------------------------------------------------------
# Public generators
# ---------------------------------------------------------------------------


def generate_claude_agent(source_path: Path) -> str:
    """Render a Claude-shape agent file from an `agents-source/<name>.md` file.

    Returns the full file content (frontmatter + body) ready to be written to
    `agents-claude/<name>.md` (the path declared by the Claude plugin manifest).

    Per FR-026 (per-host generation) / FR-027 (allow-listed fields only).
    """
    src = AgentSource.from_file(source_path)
    fm = _build_host_frontmatter(src, "claude", _CLAUDE_ALLOW_LIST)
    return _render_frontmatter(fm) + src.body.lstrip("\n")


def _toml_quote_basic(value: str) -> str:
    """Render a string as a TOML basic string with proper escaping.

    Used for short scalar values where we want minimal output (single-line).
    Markdown bodies use `_toml_literal_multiline` instead.
    """
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _toml_literal_multiline(value: str) -> str:
    """Render a string as a TOML multi-line literal string (`'''...'''`).

    TOML literal strings do NOT process escape sequences, so markdown bodies
    containing `\\n`, `\\t`, dollar signs, quotes, etc. survive verbatim.
    The only forbidden content is the closing delimiter `'''` itself.
    """
    assert "'''" not in value, (
        "Codex subagent body contains the TOML literal-string terminator `'''`; "
        "this would break the emitted TOML. Rewrite the body to avoid triple "
        "single-quotes."
    )
    # Leading newline after `'''` is permitted and ignored by TOML parsers;
    # we add one so the body starts on its own line for readability.
    return f"'''\n{value.rstrip()}\n'''"


def _toml_render_scalar(value: object) -> str:
    """Render a Python scalar to its TOML representation."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return _toml_quote_basic(value)
    raise ValueError(f"unsupported TOML scalar type: {type(value).__name__}")


def generate_codex_agent(source_path: Path) -> str:
    """Render a Codex-shape subagent TOML body from an `agents-source/<name>.md`.

    Returns the full TOML content ready to be written to
    `.codex/agents/<name>.toml` in the target project (per
    `https://developers.openai.com/codex/subagents`, retrieved 2026-05-19).

    Output shape (kebab-case `name` preserved across hosts):

    ```toml
    name = "api-designer"
    description = "Designs REST and gRPC API contracts and endpoint conventions"
    # optional Codex fields lifted from host_overrides.codex.*:
    # model = "..."
    # model_reasoning_effort = "..."
    # sandbox_mode = "..."
    # [mcp_servers.<name>] tables (if present)
    developer_instructions = '''
    <markdown body verbatim>
    '''
    ```

    Per FR-026 (per-host generation) / FR-027 (allow-listed fields only).
    Per OOS-004 (partial lift, May 2026): plugin-manifest-bundled subagents
    are still OOS — Codex docs don't define an `agents` field on the plugin
    manifest, so subagents are project-scoped TOML files instead.
    """
    src = AgentSource.from_file(source_path)

    # Validate host_overrides.codex.* against the documented allow-list.
    host_overrides = src.frontmatter.get("host_overrides", {}) or {}
    if not isinstance(host_overrides, dict):
        raise ValueError(
            f"{source_path}: `host_overrides` must be a mapping if present, "
            f"got {type(host_overrides).__name__}"
        )
    codex_fields = host_overrides.get("codex", {}) or {}
    if not isinstance(codex_fields, dict):
        raise ValueError(
            f"{source_path}: `host_overrides.codex` must be a mapping, "
            f"got {type(codex_fields).__name__}"
        )
    for key in codex_fields:
        if key not in _CODEX_ALLOW_LIST:
            raise ValueError(
                f"{source_path}: `host_overrides.codex.{key}` is not in the "
                f"documented allow-list for host 'codex'. Allowed: "
                f"{sorted(_CODEX_ALLOW_LIST - {'name', 'description'})}. (per FR-027)"
            )

    # Compose TOML output. Order matches the Codex docs examples:
    # required identity → optional scalars → optional mcp_servers tables → body.
    lines: list[str] = []
    # Identity (kebab-case preserved — cross-host UX consistency; same agent is
    # `@api-designer` in Claude/Cursor/Codex).
    lines.append(f"name = {_toml_quote_basic(src.name)}")
    lines.append(f"description = {_toml_quote_basic(src.description)}")

    # Optional scalar fields from host_overrides.codex.* (in stable order).
    for key in ("model", "model_reasoning_effort", "sandbox_mode"):
        if key in codex_fields:
            lines.append(f"{key} = {_toml_render_scalar(codex_fields[key])}")

    # Body as a TOML multi-line literal string (TOML rule: literal strings do
    # NOT process escapes, so markdown survives verbatim).
    body = src.body.lstrip("\n")
    lines.append(f"developer_instructions = {_toml_literal_multiline(body)}")

    # Optional [mcp_servers.<name>] tables.
    mcp_servers = codex_fields.get("mcp_servers")
    if mcp_servers is not None:
        if not isinstance(mcp_servers, dict):
            raise ValueError(
                f"{source_path}: `host_overrides.codex.mcp_servers` must be a "
                f"mapping of server-name to server-config, "
                f"got {type(mcp_servers).__name__}"
            )
        for server_name, server_cfg in mcp_servers.items():
            if not isinstance(server_cfg, dict):
                raise ValueError(
                    f"{source_path}: `host_overrides.codex.mcp_servers.{server_name}` "
                    f"must be a mapping, got {type(server_cfg).__name__}"
                )
            lines.append("")  # blank line separates tables
            lines.append(f"[mcp_servers.{server_name}]")
            for k, v in server_cfg.items():
                lines.append(f"{k} = {_toml_render_scalar(v)}")

    return "\n".join(lines) + "\n"


def generate_cursor_agent(source_path: Path) -> str:
    """Render a Cursor-shape agent file (commit 6 T058 scope; T171 PASS branch).

    Per data-model.md § 7 / cursor-fixture-decision.contract.md, the Cursor
    frontmatter allow-list is exactly {name, description, model, readonly}.

    **Feature 019 / commit 25 / T171 — OOS-005 PASS branch (reinstated):**
    the A-005 spike fixture outcome has flipped to `passed` in
    `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json`.
    Per `contracts/cursor-fixture-decision.contract.md:27-31`, full Cursor
    sub-agent generation is in scope: this generator lifts the source's
    `host_overrides.cursor.*` fields into the output and writes the body
    verbatim. Sources without a `host_overrides.cursor` block emit only
    `{name, description}` — Cursor's `model` and `readonly` are optional
    per the verified `cursor/plugins/agent-compatibility/agents/startup-review.md`
    shape.
    """
    src = AgentSource.from_file(source_path)
    fm = _build_host_frontmatter(src, "cursor", _CURSOR_ALLOW_LIST)
    return _render_frontmatter(fm) + src.body.lstrip("\n")


def generate_copilot_agent(
    source_path: Path,
    project_metadata: Optional[dict] = None,
) -> str:
    """Render a Copilot-shape agent file (commit 7 T071 scope).

    Per data-model.md § 7 / contracts/copilot-agent.contract.md, the Copilot
    frontmatter allow-list includes routing/tool/model metadata. The body is
    optionally interpolated with `project_metadata` values via simple
    `{Company}` / `{Domain}` substitution (commit 7 will add full jinja2
    interpolation if needed).

    Args:
        source_path: Path to `agents-source/<name>.md`.
        project_metadata: Optional dict of substitution values. When None,
            the body is left verbatim.
    """
    src = AgentSource.from_file(source_path)
    fm = _build_host_frontmatter(src, "copilot", _COPILOT_ALLOW_LIST)

    body = src.body
    if project_metadata:
        # Minimal substitution (commit 7 can extend to jinja2):
        for key, value in project_metadata.items():
            body = body.replace(f"{{{key}}}", str(value))

    return _render_frontmatter(fm) + body.lstrip("\n")
