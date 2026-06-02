# Prompt For /speckit.specify: 024-v2-profile-rule-and-dynamic-delivery

Create a feature specification for `024-v2-profile-rule-and-dynamic-delivery`.

The goal is to make authored profiles and dynamic guidance delivery real while reducing duplicate or misleading rule/profile injection. Use `planning/29-v2-execution-plan-fidelity-and-enhancement.md` as the authority for scope and sequencing, especially Phase C and Phase D. Use `planning/28-v2-artifact-and-tooling-enhancement-plan.md` as supporting design context for W1 and W5.

Required scope:

- Deliver profiles to supported hosts instead of only loading them into the corpus.
- Split profile delivery into two tiers:
  - Architecture-tier profiles: `clean-arch`, `ddd`, `modular-monolith`, `vsa`, `hybrid`, `generic`. Select one from `.dotnet-ai-kit/project.yml` `architecture:` and deliver it as always-on project context.
  - Role/band-tier profiles: `command`, `query-cosmos`, `query-sql`, `gateway`, `processor`, `controlpanel`. Keep these additive and path-scoped; do not always-on inject all of them.
- Resolve the Claude output-style bug where it names an architecture profile without delivering profile content.
- Define the actual delivery channel per host:
  - Claude: supported always-on or hook/output-style profile content delivery.
  - Codex: static guidance where no dynamic profile gating exists.
  - Cursor: `.mdc` or equivalent projected profile guidance.
  - Copilot: `.instructions.md` with `applyTo` where supported.
- Deduplicate profiles against universal rules before always-on profile delivery so the same generic constraints are not injected twice.
- Apply rule/profile coherence work:
  - Narrow the agreed broad globs from `planning/29` M1.
  - Make `deterministic-enforcement` universal/doc-only rather than a fake path-scoped rule.
  - Trim v1 Python residue from testing rules.
  - Keep broad rules broad only where `planning/29` says coverage is more important than idle-token economy.
- Project MCP/LSP configuration as static delivery artifacts only:
  - Generate `.mcp.json` or equivalent host config from one descriptor where supported.
  - Generate `.lsp.json` for hosts where agent-facing LSP is supported or preview-supported.
  - Update relevant agents to prefer symbol-precise navigation when LSP is available.

Out of scope for this feature:

- Building the kit's own MCP server runtime.
- Adding new W7 skills/agents.
- Porting scripts to C#.
- Analyzer expansion beyond metadata or registry updates needed for rule/profile coherence.

The generated `tasks.md` must include a dedicated `Review & Verification` phase after implementation phases and before final polish. That review must verify profile content actually reaches initialized/projected host outputs, no duplicate profile/rule injection is introduced, generated MCP/LSP files are deterministic, and all standing gates pass.

Success criteria must include:

- A profile-delivery test after init or projection.
- A rule/profile deduplication check.
- Generated host outputs are drift-clean.
- MCP/LSP projection is present where in scope and explicitly marked unsupported where not.
