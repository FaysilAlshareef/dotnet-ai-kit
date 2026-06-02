# Prompt For /speckit.specify: 028-v2-expansion-skills-and-agents

Create a feature specification for `028-v2-expansion-skills-and-agents`.

The goal is to add the W7 expansion artifacts after the repair and delivery foundations are in place. Use `planning/29-v2-execution-plan-fidelity-and-enhancement.md` Phase J as the authority and `planning/28-v2-artifact-and-tooling-enhancement-plan.md` W7 as the source catalog.

Required scope:

- Re-confirm all external maturity/version claims during planning or implementation before authoring version-sensitive guidance. Use current official docs or primary sources for .NET, Microsoft packages, YARP, EF Core, Azure, and related ecosystems.
- Add the two new agents:
  - `mcp-engineer`
  - `performance-engineer`
- Add the 11 strong skills:
  - `ai/mcp-server`
  - `ai/extensions-ai-evaluation`
  - `ai/agent-framework`
  - `api/yarp-reverse-proxy`
  - `data/ef-vector-search`
  - `data/ef-advanced-mapping`
  - `performance/runtime-diagnostics`
  - `security/supply-chain`
  - `security/secrets-management`
  - `devops/container-hardening`
  - `devops/iac-bicep-azd`
- Add the 5 medium skills unless planning discovers a current reason to defer one:
  - `core/file-based-apps`
  - `messaging/kafka-confluent`
  - `messaging/event-hubs`
  - `api/webhooks`
  - `devops/native-aot-publishing`
- Every new skill must meet the description standard:
  - Action-verb-first description.
  - Explicit `Use when`.
  - Explicit `Do NOT use ... (use sibling)` boundary.
  - Correct owning agent metadata.
- Apply resource enrichment by archetype only:
  - Add `references/`, `examples/`, or `evals/` only where they add real value.
  - Do not add boilerplate resource folders to every new skill.
- Update manifest/corpus graph expectations and projections for all four hosts.
- Add selector evals for new confusable skills where needed.

Out of scope for this feature:

- Building the kit's own MCP server runtime. The `ai/mcp-server` skill teaches users how to build MCP servers; it is not the runtime server itself.
- Event-catalogue MCP tooling.
- `audit` CLI verb.
- Reopening rejected W7 items unless the maintainer explicitly changes scope.

The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish. That review must verify every new artifact is deduped against existing artifacts, descriptions select correctly, owner agents are correct, current-source claims are cited in research, generated host output is drift-clean, and all standing gates pass.

Success criteria must include:

- Corpus counts increase by the expected number of skills and agents.
- New artifacts project to Claude, Codex, Cursor, and Copilot.
- No broken graph edges are introduced.
- Version/maturity claims are current at authoring time.
- All standing gates pass.
