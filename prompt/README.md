# Spec Prompts

These prompts are intended to be pasted into `/speckit.specify` one at a time, in order.

Run the normal command flow for each feature:

```text
/speckit.specify -> /speckit.clarify -> /speckit.plan -> /speckit.tasks -> /speckit.analyze -> /speckit.implement
```

There is no separate `/speckit.review` command in `.claude/commands`. Each prompt therefore requires the generated `tasks.md` to include an explicit `Review & Verification` phase after implementation phases and before final polish.

Recommended order:

1. `023-v2-corpus-correctness-and-delivery-foundation.md` (implemented)
2. `024-v2-profile-rule-and-dynamic-delivery.md` (in progress)
3. `025-v2-dotnet-script-and-tooling-cleanup.md`
4. `026-v2-progressive-disclosure-and-triggering.md`
5. `027-v2-analyzers-and-deterministic-enforcement.md`
6. `028-v2-expansion-skills-and-agents.md`
7. `030-v2-release-distribution-and-fidelity-closeout.md`
8. `029-v2-kit-mcp-server.md`

`030` runs before `029` on purpose: it decides where installed tools resolve the corpus, and `029`'s `mcp serve` plan consumes that decision. `030` also owns the items no other feature covers — planning/27 A8/A9, the planning/29 Phase F refactors (R1–R5), cross-host load parity, the release/rollback plan (BD-3, AR-7d), and documentation-count truth.

## Amendments to apply when running the remaining prompts

Findings from the post-024 codebase review. Include each amendment in the feature's scope when pasting its prompt into `/speckit.specify`:

- `025`: bundled `.cs` scripts run inside user repos — require a .NET 10 SDK availability check (`dotnet run --file` is .NET 10+; a consumer `global.json` pinning an older SDK must fail with actionable guidance, not a raw error). Define the script-consent mechanism concretely (how consent is recorded and checked, not just "never auto-run").
- `026`: resource relocation is lossy on Cursor and Copilot today — their generated output carries only `evals/`, no `examples/`, `references/`, or `scripts/` (Claude and Codex carry all four). Require resource-projection parity, or an explicit documented per-host loss decision, before moving content out of `SKILL.md` bodies. Keep user stories independently deliverable (relocation vs. agent work vs. evals/descriptions) so a partial landing stays drift-clean.
- `027`: quantify the false-positive budget — new analyzers must report zero diagnostics on the kit's own `src/` and on the shipped golden examples.
- `028`: selector evals are mandatory, not "where needed", for the `ai/*` cluster (`mcp-server` vs `agent-framework` vs `extensions-ai-*`) and for the `mcp-engineer`/`ai-engineer` routing boundary, since expansion is where selector precision degrades.
- `029`: take the corpus-location decision from `030` as a plan input; add a read-only guarantee (no MCP tool mutates `artifacts/`), response-size limits for large skill bodies, and golden-JSON contract tests pinning the tool shapes.
