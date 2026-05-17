# Contract: `.github/agents/<name>.agent.md`

**Spec source**: FR-004, FR-007 (per-agent files), FR-026, US2 (acceptance scenario 1)
**Render command**: `dotnet-ai upgrade --copilot`
**Render template**: `agents-copilot-templates/agent.md.j2`
**Source-of-truth**: `agents-source/<name>.md`

## Purpose

GitHub Copilot custom agents. One file per logical specialist agent (13 total per `CLAUDE.md` "13 specialist agents"). Read by GitHub Copilot CLI's custom-agent loader.

## File-name pattern

`.github/agents/<name>.agent.md` where `<name>` matches the agent's source-of-truth file name (no `.md`). The `.agent.md` extension is mandated by GitHub Copilot docs (`https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550): "Each custom agent is defined by a Markdown file with an `.agent.md` extension."

## Allowed frontmatter (per Copilot docs)

Per `https://docs.github.com/en/copilot/reference/custom-agents-configuration` lines 536-550, GitHub Copilot custom agents support the following frontmatter fields. The generator (`agent_generators.generate_copilot_agent()`) is allow-list based and MUST emit only these fields, omitting any field whose value is not provided by the source-of-truth or its `host_overrides.copilot`:

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string | yes | Agent name |
| `description` | string | yes | Short description |
| `target` | string | no | Routing target |
| `tools` | array | no | Allowed tools |
| `model` | string | no | Preferred model |
| `disable-model-invocation` | bool | no | Suppress auto-invocation |
| `user-invocable` | bool | no | Whether user can call directly |
| `mcp-servers` | array | no | MCP server references |
| `metadata` | object | no | Arbitrary metadata block |

The retired `infer` field MUST NOT be emitted (deprecated per Copilot docs).

Per FR-027, no field outside this allow-list may appear. Tests at `tests/unit/test_agent_generators.py` MUST assert no field leak for each of the 13 agents on the Copilot path.

## Required content blocks

1. The agent body from `agents-source/<name>.md` source-of-truth, with any `host_overrides.copilot` fields applied
2. Project-specific routing hints resolved from `ProjectMetadata` (e.g., which paths the agent should default to inspecting)

## Freshness contract

Same as `copilot-instructions.md`. The render is recorded in `.dotnet-ai-kit/manifest.json` with `host_owner: "copilot"`.

## Path collision rules

Per FR-008 / A-008, these files are owned by the tool's managed-file manifest. Pre-existing developer-authored `.agent.md` files in `.github/agents/` MUST be preserved per the manifest rule.

## Generator invariants (per FR-027, FR-028)

- The generator MUST NOT emit any field outside the Copilot documented frontmatter set
- Tests at `tests/unit/test_agent_generators.py` MUST assert no field leak for each of the 13 agents
- The same source-of-truth `agents-source/<name>.md` MUST produce structurally equivalent per-host outputs (Claude, Copilot, and Cursor when applicable) with only host-specific field differences
