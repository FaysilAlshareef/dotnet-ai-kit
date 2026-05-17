# Contract: `agents-source/<name>.md`

**Spec source**: FR-026, FR-027
**Per-host generators**: `src/dotnet_ai_kit/agent_generators.py`

## Purpose

Source-of-truth markdown body per logical specialist agent. **One file per agent**, used as input to per-host generators that produce host-specific output files. Renamed from current `agents/` to `agents-source/` (per round-3 correction: `agents/` becomes the Cursor build-output directory, so source-of-truth needs its own name).

## File format

Standard markdown with YAML frontmatter. The frontmatter contains structured fields; the markdown body is the **document body** (everything after the closing `---`), not a frontmatter field.

### Required frontmatter

```yaml
---
name: <agent-name>
description: <short description>
---
```

### Optional frontmatter

```yaml
host_overrides:
  claude:
    role: <claude-specific role>
    expertise: [...]
    complexity: <low|medium|high>
    max_iterations: <int>
  cursor:
    model: <preferred-model>
    readonly: <bool>
  copilot:
    target: <routing-target>
    tools: [...]
    model: <preferred-model>
    disable-model-invocation: <bool>
    user-invocable: <bool>
    mcp-servers: [...]
    metadata: { ... }
```

Each `host_overrides.<host>` key MUST be one of the allow-listed frontmatter fields for that host. Unknown fields are rejected at generator time per FR-027.

### Markdown body

Everything after the closing `---` is the agent's actual prose. This is the body that gets included in all generated host-specific files. It can include H1/H2/H3 headings, bullet lists, code samples, etc.

## Example

Matches the shape of existing `agents/dotnet-architect.md:1-25` (which moves to `agents-source/dotnet-architect.md` in commit 4):

```markdown
---
name: dotnet-architect
description: Leads overall .NET solution architecture and design patterns
host_overrides:
  claude:
    role: advisory
    expertise:
      - clean-architecture
      - vertical-slice
      - ddd-patterns
      - modular-monolith
    complexity: high
    max_iterations: 20
  cursor:
    model: claude-sonnet-4
    readonly: false
  copilot:
    target: solution-root
---

# .NET Architecture Specialist

**Role**: Expert in generic .NET architecture patterns (VSA, Clean Arch, DDD, Modular Monolith)

## Responsibilities
...
```

## Generator behavior

`src/dotnet_ai_kit/agent_generators.py` exposes:

- `generate_claude_agent(source_path: Path) -> str` — emits to `agents-claude/<name>.md`. Frontmatter contains `name`, `description`, plus `host_overrides.claude.*` fields lifted to top level. Body copied verbatim.
- `generate_cursor_agent(source_path: Path) -> str` — emits to `agents/<name>.md` (the Cursor manifest's path). Frontmatter contains `name`, `description`, `model`, `readonly` (Cursor's allow-list per `cursor/plugins/agent-compatibility/agents/startup-review.md`). Body copied verbatim.
- `generate_copilot_agent(source_path: Path, project_metadata: dict) -> str` — emits to `.github/agents/<name>.agent.md` at deploy time. Frontmatter contains the Copilot allow-list (`name`, `description`, `target`, `tools`, `model`, `disable-model-invocation`, `user-invocable`, `mcp-servers`, `metadata`) lifted from `host_overrides.copilot.*`. Body interpolated with `project_metadata` substitutions.

## Invariants (tested in `tests/unit/test_agent_generators.py`)

- Each generator emits ONLY fields documented for its host
- No field listed in `host_overrides.<other_host>` leaks into another host's output
- The markdown body is identical across all hosts for the same source agent
- The Claude path MUST NOT introduce a `skills:` preload field (regression guard per FR-027)
