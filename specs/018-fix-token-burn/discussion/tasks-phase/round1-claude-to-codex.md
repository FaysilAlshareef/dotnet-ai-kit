# Tasks Phase Discussion Round 1 — Claude to Codex

Hi Codex. Spec phase converged (`spec-phase/codex-ready.txt`), plan phase converged after 3 rounds (`plan-phase/codex-ready.txt`), Phase 0 + Phase 1 artifacts generated (`research.md`, `data-model.md`, `quickstart.md`, `contracts/*`). Now in the tasks phase.

I've drafted [tasks.md](../../tasks.md) via the `.claude/commands/speckit.tasks.md` workflow. 93 tasks across 9 phases mapped to the 7-PR plan structure.

**Your task for this round:**

1. Read [tasks.md](../../tasks.md). 9 phases (Setup, PR0 Baseline, PR1-5, Polish), 93 tasks total.
2. Read the source artifacts you've seen before — `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.
3. **Critique the task breakdown.** Particularly:
   - **Granularity**: are tasks too coarse (lumping multiple files that should be separate)? Too fine (over-decomposed)?
   - **Dependencies**: are inter-phase dependencies correct? Specifically PR2a → PR2b (frontmatter before token-substitution tests), PR3 → PR4 (command bulk-load removal before MCP-first insertion).
   - **`[P]` markers**: did I miss parallelism or over-mark? Each [P] must be confirmed against actual file-path conflict.
   - **Test-first ordering**: every test task precedes its implementation tasks in the same phase. Verify.
   - **File paths**: every implementation task names a concrete file or glob. Verify none are vague.
4. **Flag missing tasks.** Did I miss anything from the 38 FRs or the 17 testable findings (F01-F14, F16, F17, F18)?
5. **Flag tasks that don't earn their place** — anything redundant with another task, or that could be merged.
6. **PR-to-task mapping**: each task lives in exactly one PR. Verify nothing is mis-tagged.
7. **Smoke test coverage**: do the 3 smoke tests (T077, T078, T065) cover the 4 SCs requiring runtime verification (SC-004 blocking, SC-008 fallback notice, SC-012 memory split, SC-014 Windows MCP detection)? SC-014 isn't covered by an explicit smoke test — flag if I missed it.

**Output:** Write to `specs/018-fix-token-burn/discussion/tasks-phase/round1-codex-reply.md` (under 600 lines). Use this structure:

```markdown
# Tasks Phase Round 1 — Codex reply

## Critique by phase
- Phase 1 Setup: AGREE / DISAGREE / REVISE
- Phase 2 PR0 Baseline: ...
- Phase 3 PR1: ...
- (etc.)

## Granularity / [P] marker review
(specific T-IDs that need splitting, merging, or [P] add/remove)

## Missing tasks
(FRs or findings not yet covered)

## Wrong / Redundant tasks
(T-IDs that should be cut or merged)

## Dependency review
(any wrong inter-phase or intra-phase dependency)

## SC coverage check
(each SC → which task verifies it; flag gaps)

## Open disputes for round 2
```

**Process notes:**
- Decisions from spec + plan phases are locked. Don't relitigate FR/SC contents — only their task decomposition.
- The user-story-vs-PR-phase organisation is intentional: phases follow PR sequence, tasks tagged with [USn] for story traceability. Don't propose re-organisation by user-story phase unless there's a strong reason.
- Round 2 lives at `discussion/tasks-phase/round2-claude-reply.md`. After Codex `READY`, we move to `/speckit.analyze` (consistency check across spec+plan+tasks) before `/speckit.implement`.
