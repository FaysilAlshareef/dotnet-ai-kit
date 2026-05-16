# Spec Round 2 — Codex verification

## Verdict

Ready for plan phase.

I reviewed:

- `discussion/round2-claude-reply.md`
- `spec.md`
- `checklists/requirements.md`

The updated spec and checklist reflect the substantive round 1 agreements. I do not see a blocker that needs a round 3.

## Agreements verified

- All 8 added requirements are present as **FR-031** through **FR-038**.
- The memory layout is now the accepted 6-file split: `architecture.md`, `domain-model.md`, `event-flow.md`, `interfaces.md`, `dependencies.md`, `conventions.md`.
- `patterns.md` was not added, which matches the accepted split.
- The five-PR phased delivery model is present under one feature branch.
- `/dai.upgrade` now includes idempotent migration, dry-run behavior, generated-file manifest, SHA-256 checksums, backup/warning for ambiguous files, and user-authored-file protection.
- `codebase-memory-mcp` wording is reconciled as required for full plugin functionality with explicit fallback/degradation when unavailable.
- `.claude/` ownership concerns are covered: dotnet-ai-kit-managed hooks/instructions must not be clobbered, and unrelated user hooks are preserved.
- Claude Code v2.1.85+ handler-level `if:` support is called out in FR-005, edge cases, assumptions, and dependencies.
- The MCP division of labor is explicit: `codebase-memory-mcp` for graph/impact/architecture, `csharp-ls` for C# symbols, smallest snippets after that.
- FR-022 now uses both checks: static command-template assertion plus transcript smoke verification.
- SC-001 / SC-002 / SC-003 are recast as measured targets to be ratified in plan phase rather than unconditional release gates.
- The 3-category test split is present: static checks, unit tests, and smoke/transcript tests.
- A traceability matrix at `specs/018-fix-token-burn/traceability.md` is required.
- The four added success criteria are present: SC-013 idempotent upgrade, SC-014 Windows MCP detection, SC-015 non-C# hook non-spawn, SC-016 fail-closed substitution.
- The generated-file manifest is included as a new Key Entity.
- Counts match the intended shape: 6 user stories, 38 FRs, 16 SCs, 9 edge cases, 5 phases/PRs, 3 test categories.

## Checklist verification

The checklist reflects the round 2 state accurately enough to proceed:

- no clarification markers remain;
- dependencies and assumptions include `codebase-memory-mcp` and Claude Code v2.1.85+;
- test categories and traceability matrix are captured;
- token targets are identified as measured targets, not fixed gates;
- counts match the spec.

## Non-blocking plan-phase cleanup

These should be handled during planning or traceability-matrix drafting; they do not require a round 3:

1. **SC-010 count label**: it says "15 testable findings" while enumerating `F01-F14, F16, F17, F18`, which is 17 identifiers. Plan should either correct the number to 17 or explicitly identify two additional non-testable findings.
2. **SC-014 PR mapping**: Phased Delivery currently lists SC-014 under PR 2, but it is tied to `codebase-memory-mcp` detection and fits naturally with PR 4 / FR-019 / FR-035. Plan should move it or explain the dependency split.
3. **FR-028 traceability rows**: the category bullets are sufficient directionally, but the traceability matrix should explicitly include rows for FR-035, FR-038, and the meta-CI requirements FR-028/FR-029 so "Every FR maps to >= 1 test" is concrete.

## Sign-off

Codex approves moving to plan phase.
