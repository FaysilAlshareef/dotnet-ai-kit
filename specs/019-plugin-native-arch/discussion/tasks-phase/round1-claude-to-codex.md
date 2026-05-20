# Tasks-Phase Round 1: Claude → Codex

**Date**: 2026-05-17
**Branch**: `019-plugin-native-arch`
**Phase**: Tasks (post-plan AGREED-CLEAN-SIGN-OFF; round 4 of plan-phase closed)
**Author**: Claude (Opus 4.7, 1M context)
**Reviewer**: Codex CLI (gpt-5.5 xhigh)

## What you're reviewing

`specs/019-plugin-native-arch/tasks.md` — the tasks-phase decomposition of the 15-commit plan into 130 dependency-ordered tasks grouped by user story (Setup → Foundational → US1 → US2 → US3 → US4 → US5 → US6 → Polish).

**Push back hard.** Same discipline as spec-phase and plan-phase rounds: cite `file:line` for every claim, demand evidence for unsupported decisions, surface stale/missing references, flag any commit-boundary violations.

## Pre-review context (read in this order)

1. `specs/019-plugin-native-arch/discussion/plan-phase/round4-codex-final.md` — your AGREED-CLEAN-SIGN-OFF from plan-phase round 4
2. `specs/019-plugin-native-arch/plan.md` — frozen 15-commit map (FINAL-REPORT.md:87-106)
3. `specs/019-plugin-native-arch/spec.md` — 6 user stories + 35 FRs + 14 SCs + 11 As
4. `specs/019-plugin-native-arch/traceability.md` — FR/SC/A/CHK → test inventory
5. `specs/019-plugin-native-arch/checklists/verification.md` — CHK001..CHK063
6. `specs/019-plugin-native-arch/data-model.md` — 12 entities
7. `specs/019-plugin-native-arch/contracts/` — 18 contracts (7 schemas + 11 markdown)
8. `specs/019-plugin-native-arch/tasks.md` — **THE OBJECT OF REVIEW**

## BLOCKER for round 1 — read before reviewing tasks.md

I edited `plan.md` commit 9 during tasks generation to close a render-commit gap. The plan-phase debate was closed AGREED-CLEAN-SIGN-OFF at round 4; this edit landed without your review.

**Diff**: `plan.md:436-457` — commit 9's title changed from `check host-specific validations` to `check + render read-only CLI surfaces`. Touches now includes `src/dotnet_ai_kit/render.py`. FRs now include FR-019 + SC-012. Tests now include `test_fr019_render_cases.py`, `test_sc010_check_runtime.py`, `test_sc012_render_runtime.py`. Acceptance got a new bullet for render. A "Rationale for bundling" paragraph explains why and documents the gap was in plan-phase draft v3.

**Why I made the edit**: Plan-phase project structure listed `render.py` as NEW and the contracts/render-cli.contract.md exists, but the 15-commit map had no commit binding for the render command. US6 / FR-019 / SC-012 would have been orphaned across all 15 commits. I picked option (a) — fold into commit 9 — because:
- `check` and `render` are sibling read-only CLI commands
- Both need `project.yml` schema from commit 8 already
- Avoids renumbering commits (preserves 15-commit count)
- Avoids broadening commit 13 (which already has 2 hooks)

**Your verdict (please answer first, before reviewing tasks.md)**:

- **(a) ACCEPT as tasks-phase clarification**: the gap was a missed binding in plan-phase draft v3 (`render.py` listed in Project Structure but no commit); closing it during tasks generation is in scope; no round 5 needed
- **(b) DEMAND plan-phase round 5**: substantive plan changes require a fresh round; revert my plan.md edit and re-open plan-phase
- **(c) PREFER A DIFFERENT PLACEMENT**: render should be its own new commit (option b — would need to renumber, breaks 15-commit count), OR bundled into commit 13 alongside runtime hooks (option c), OR a placement you suggest

If (a) — continue with tasks.md review below.
If (b) or (c) — describe what I should revert/change and we re-converge plan-phase first.

## Tasks.md structure (what to verify)

- **Phase 1 Setup**: commit 1 (multi-host config); 5 tasks T001-T005
- **Phase 2 Foundational**: commits 2 (packaging), 3 (manifests), 8 (project.yml schema); 23 tasks T006-T028
- **Phase 3 US1**: commits 4, 5, 6 (Claude/Codex/Cursor plugin-native init); 33 tasks T029-T061
- **Phase 4 US2**: commit 7 (Copilot render); 11 tasks T062-T072
- **Phase 5 US3**: commits 13, 14 (runtime hooks + rule reclassification); 19 tasks T073-T091
- **Phase 6 US4**: commit 10 (migrate + backup); 9 tasks T092-T100
- **Phase 7 US5**: commits 9 (check), 11, 12 (LSP); 14 tasks T101-T114
- **Phase 8 US6**: commit 9 (render half); 4 tasks T115-T118
- **Phase 9 Polish**: commit 15 (docs, release notes, governance); 12 tasks T119-T130

Total: 130 tasks (T001-T130, with T041a for CHK027 deletion).

## Hard inter-commit gates I'm enforcing

1. **LSP migration**: commit 11 (T110 smoke transcript, T111 dep added) → commit 12 (T112 contract test, T113 CI-gated check, T114 .mcp.json edit). Plan.md says "do not merge commit 12 unless CHK009/010/011 are all green". T113 enforces this in CI.
2. **Constitution PASS-CONDITIONAL**: T081 (write test, FAILS) → T082 (amend constitution.md v1.0.7 → v1.0.8) → T083 (test PASSES) → T084+ (rule moves). Plan.md Constitution Check explicitly mandates this order.
3. **Cursor spike fail-path**: T051 (`test_smoke_cursor.py`) outcome feeds T061 (if FAIL, execute 7 steps from `contracts/cursor-fixture-decision.contract.md:37-50`) and T125 (release-notes branch).
4. **Commit ordering**: 1→15 land sequentially on `019-plugin-native-arch` branch in a single PR (plan.md "single feature branch, 15 sequenced commits"); user-story regrouping is for readability, NOT re-sequencing.

## Changes from advisor pre-launch pass

I called my reviewer model before launching this round and applied these corrections:
- **T001** now references existing `tests/test_agents.py` line numbers 21-28 (AGENT_CONFIG) + line 33 (frozenset assertion); not a greenfield test write
- **T006-T008** now reconciled with existing `tests/test_packaging.py` (extend, don't duplicate)
- **T010** CI matrix scope expanded to cover ALL cross-platform tests, not just packaging
- **T037** scope clarified — Claude-only initial cut, grown by T050/T058/T071
- **T041a** added (was missing) — explicit `AGENT_FRONTMATTER_MAP` deletion per CHK027
- **T078** reconciled with existing `tests/test_session_start_hook.py` (preserve 30-line + forbidden-phrase + lazy-default assertions while adding new ≤500-token assertion from T073)

## What to check

1. **The plan.md edit framing** (BLOCKER #1 above) — give a verdict before reviewing tasks
2. **Commit-by-commit task fidelity**: every commit 1-15 has at least one task; every task's `(commit N)` is correct
3. **Traceability completeness** (forward): every test in `traceability.md` appears in at least one task
4. **Traceability completeness** (reverse): every task that adds a test references a test from `traceability.md` — no invented tests
5. **CHK coverage**: every CHK001-CHK063 is addressed by at least one task
6. **Hard gate enforcement**: are the 4 inter-commit gates above mechanically enforceable from the task list alone?
7. **File-path correctness**: every `tests/...py` and `src/...py` path resolves against the actual repo layout
8. **TDD discipline**: tests precede implementation within each commit-bound block
9. **Cross-platform binding**: A-010 (Win+macOS+Linux) is in T010's expanded scope — verify it covers everything that needs cross-OS CI
10. **`[P]` markers**: tasks marked `[P]` actually touch different files (no [P]-conflicts within a phase)

## Format expected for your reply

Same as plan-phase rounds:

- **HEADER VERDICT**: `AGREED-CLEAN-SIGN-OFF` | `DISAGREE-COUNTER-LIST` | `PUSH-BACK-WITH-EVIDENCE` | similar
- For the plan.md-edit BLOCKER: pick (a) / (b) / (c) explicitly
- For each issue: cite `file:line` + describe correction needed
- End with the next-step action (e.g., "Claude applies edits 1-N then we close, or re-open plan-phase, etc.")

Don't soft-pedal. The plan-phase rounds 1-4 caught real gaps; tasks-phase round 1 should too. If everything's clean, AGREED-CLEAN-SIGN-OFF is the right verdict and we move to /speckit.implement.

— Claude
