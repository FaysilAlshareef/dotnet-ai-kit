# Prompt For /speckit.specify: 029-v2-kit-mcp-server

Create a feature specification for `029-v2-kit-mcp-server`.

The goal is to add the kit's own MCP server runtime as a new live surface over the authored corpus. Use `planning/29-v2-execution-plan-fidelity-and-enhancement.md` Phase K as the authority. This feature should be planned after the MCP/LSP projection work and after the `ai/mcp-server` skill exists, but the spec should still define the runtime clearly.

Required scope:

- Add a new runtime surface for MCP, not a static `IHostProjector`.
- Introduce a new project or equivalent cleanly layered component for the MCP server that depends inward on Application/Core and reuses the existing artifact repository/corpus loading path.
- Add a CLI command:
  - `dotnet-ai mcp serve`
  - Long-running stdio server lifecycle.
  - Graceful shutdown behavior.
- Expose MCP tools over the corpus:
  - `search_skills`
  - `get_skill`
  - `search_knowledge`
  - `get_rule`
  - `list_agents`
  - `get_profile`
- Keep tool contracts versioned and stable enough for external MCP clients.
- Use the current GA MCP .NET SDK package only after verifying current official package guidance during planning or implementation.
- Wire install/config output so supported host configurations can point at `dotnet-ai mcp serve`.
- Tests must cover:
  - Tool contract shape.
  - Served corpus equals loaded corpus.
  - `mcp serve` smoke behavior.
  - Failure behavior for missing or invalid corpus.
- Keep no-network requirements scoped correctly: local one-shot verbs remain no-network; the MCP server is a runtime service and must be documented separately.

Out of scope for this feature:

- `event-catalogue` MCP tool.
- `audit` CLI verb.
- HTTP transport unless specifically approved during planning.
- Rewriting static projection as MCP-only delivery.

The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish. That review must verify the runtime is not mistakenly modeled as a static projector, MCP tool contracts are stable, shutdown behavior is safe, install config is deterministic, and all standing gates pass.

Success criteria must include:

- `dotnet-ai mcp serve` starts and exposes the expected tools.
- MCP tools can search and fetch the same corpus loaded from `artifacts/`.
- Host install/config output can reference the server command.
- Build, tests, format, and `generate --check` all pass.
