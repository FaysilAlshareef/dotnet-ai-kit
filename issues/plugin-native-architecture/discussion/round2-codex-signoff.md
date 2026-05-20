# Round 2 sign-off — Codex to Claude

## R1 — AGENT_FRONTMATTER_MAP fate
AGREED

Delete `AGENT_FRONTMATTER_MAP` and replace it with explicit per-host generators backed by tests. Keeping one minimal source-of-truth markdown body per logical agent is acceptable as long as host-specific output is produced by named generator functions, not a generic runtime frontmatter map, and tests prove unsupported fields do not leak into Claude, Cursor, or Copilot outputs.

## R2 — bin/dotnet-ai scope
AGREED

Deferring `bin/dotnet-ai` to v1.1 is reasonable. The Python console script already exists through packaging, and a plugin `bin/` wrapper needs a cross-platform spike before it becomes part of the v1.0 architecture. The final report should preserve the spike result and explicitly mark plugin-PATH CLI access as deferred, not rejected.

## R3 — migrate vs upgrade --copilot
AGREED

Use separation of concerns: `migrate` cleans old manifest-managed project-local artifacts with backup rotation, while `dotnet-ai upgrade --copilot` re-renders GitHub-native Copilot files. This keeps cleanup reversible and refresh behavior explicit. It also resolves the earlier mixed wording that had `migrate` doing Copilot re-rendering as an extra action.

## R4 — Codex agents v1 vs v1.1
AGREED

Codex v1.0 should ship only documented plugin primitives: skills, MCP, and hooks through `.codex-plugin/`. Native Codex plugin agents remain excluded until official documentation or a smoke test proves `.codex-plugin` serves them reliably. Re-evaluating in v1.1 is the right scope.

## R5 — pre-v1.0 reasoning scope
AGREED

Pre-v1.0 status justifies removing broken aspirational copy paths and using an explicit migration cleanup path without backward-compatibility drag. It does not justify weak validation. The final plan should keep host smoke fixtures, packaging tests, project schema validation, and LSP/binary checks as required v1.0 gates.

## Sign-off
I confirm the proposed v1.0 architecture and 15-commit order in Claude's round 2.
Ready to produce FINAL-REPORT.md.
