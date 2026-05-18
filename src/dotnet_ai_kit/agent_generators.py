"""Per-host agent generators (feature 019 / FR-026 / FR-027 / T041).

Each generator takes a single source-of-truth agent markdown (under
`agents-source/<name>.md`) and emits the host-specific shape:

- `generate_claude_agent(source_path) -> str`: Claude allow-list frontmatter
  + verbatim body. Output target: `agents-claude/<name>.md`.
- `generate_codex_agent(source_path) -> None`: Codex native agents are
  deferred to v1.1 per OOS-004 — raises NotImplementedError to make the
  FR-035 admission gate explicit.
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


def generate_codex_agent(source_path: Path) -> None:
    """Codex native agents deferred to v1.1 per OOS-004 / FR-035 admission gate.

    Raises NotImplementedError explicitly to make the deferral observable in
    the type system. Commit 5 (T050) re-declares this raise to keep the
    admission gate visible.

    Feature 019 / commit 27 / T183 — forward-compat hook for v1.1: when
    Codex CLI exposes a sub-agent primitive in its plugin manifest, the
    v1.1 release will:
    1. Reserve the `host_overrides.codex:` block convention in
       `data-model.md` § 7 (already documented as a forward-compat note).
    2. Materialise this generator analogously to `generate_claude_agent`,
       reading the Codex allow-list from `host_overrides.codex.*` of each
       agents-source/*.md file.
    See `https://developers.openai.com/codex/plugins` (retrieved 2026-05-18)
    for the latest Codex plugin documentation — no `agents` primitive in
    Codex plugin manifest as of v0.117.0.
    """
    raise NotImplementedError(
        "Codex native plugin agents are deferred to v1.1 per OOS-004 — "
        "no `agents` primitive in the Codex plugin manifest as of v0.117.0 "
        "(see https://developers.openai.com/codex/plugins, retrieved 2026-05-18). "
        f"received {source_path}, no Codex agent file generated."
    )


def generate_cursor_agent(source_path: Path) -> str:
    """Render a Cursor-shape agent file (commit 6 T058 scope, T170c).

    Per data-model.md § 7 / cursor-fixture-decision.contract.md, the Cursor
    frontmatter allow-list is exactly {name, description, model, readonly}.

    **Feature 019 / commit 25 / T170c — OOS-005 fail-safe default:** until the
    A-005 spike fixture has demonstrably passed the Cursor CLI smoke test in
    CI (outcome JSON at `specs/019-plugin-native-arch/discussion/tasks-phase/
    cursor-subagent-outcome.json::outcome == "passed"`), this generator
    raises NotImplementedError. Once a CI run flips the JSON to `passed`,
    T171 unblocks the generation step (re-enable by restoring the
    pre-T170c implementation OR conditioning on the JSON outcome at call
    time). See `contracts/cursor-fixture-decision.contract.md` for the
    canonical decision rule.
    """
    raise NotImplementedError(
        "Cursor sub-agent generation is gated on the A-005 spike fixture "
        "outcome (cursor-subagent-outcome.json::outcome must be 'passed'). "
        f"Received {source_path}; ship the fail-safe default. See "
        "specs/019-plugin-native-arch/contracts/cursor-fixture-decision.contract.md "
        "for the gating rule and the v1.1 plan."
    )


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
