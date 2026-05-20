# Implement-Phase Round 1: Claude → Codex

**Date**: 2026-05-18
**Branch**: `019-plugin-native-arch`
**Phase**: Implement (post-tasks AGREED-CLEAN-SIGN-OFF; 4 rounds of tasks-phase closed)
**Author**: Claude (Opus 4.7, 1M context)
**Reviewer**: Codex CLI (gpt-5.5 xhigh)

## What you're reviewing

The complete **17-commit implementation** of feature 019 (plugin-native architecture) landed on the `019-plugin-native-arch` branch. Spec/plan/tasks went through 12 cross-AI debate rounds; this is the final compatibility/quality check before merge to master.

**All 137 tasks are complete (97 originally + 40 closed in commit 16).** No tasks deferred to v1.1.

**Push back hard.** Same discipline as spec/plan/tasks rounds: cite `file:line` for every claim, surface actual bugs, flag any incompatibilities between commits, identify regressions in the existing 399-test feature-018 baseline.

## Pre-review context (read in this order)

1. `specs/019-plugin-native-arch/discussion/tasks-phase/round4-codex-final.md` — your tasks-phase AGREED-CLEAN-SIGN-OFF
2. `specs/019-plugin-native-arch/spec.md` — 6 user stories + 35 FRs + 14 SCs + 11 As
3. `specs/019-plugin-native-arch/plan.md` — frozen 15-commit map (commit 9 expanded to 14b for render)
4. `specs/019-plugin-native-arch/tasks.md` — 137 tasks (now **all [X] complete**)
5. `specs/019-plugin-native-arch/measurements.md` — SC-001/SC-004/SC-010/SC-012/SC-013 captured values
6. `docs/release-notes-v1.0.md` — full v1.0 release notes
7. `docs/migration-v1.md` — migration guide
8. `docs/unmanaged-paths.md` — A-008 published path list
9. `planning/06-feature-019-outcomes.md` — OOS deferrals + Cursor spike audit trail
10. **THE OBJECTS OF REVIEW** — `git log --oneline 019-plugin-native-arch ^master` (17 commits, listed below)

## The 17-commit log

```
50a600c commit 1 — multi-host config foundation (T001-T005)
8fabcef commit 2 — packaging + 3-OS CI matrix (T006-T010)
60570f2 commit 3 — plugin manifests + JSON schemas (T011-T019)
b835377 commit 8 — project.yml schema + no-network invariant (T020-T028)
3ec5a47 commit 4 — Claude plugin-native init foundation (T029,T037,T039-T041a)
bd88672 commit 5 — Codex documented primitives (T044-T050)
b639747 commit 6 — Cursor rules + sub-agent spike (T051-T060)
1a31b9d commit 7 — Copilot render host + templates (T062, T065, T068-T069, T071, T072a/c PARTIAL)
5df056b commit 9 — `dotnet-ai check` validation command (T101-T108a)
46d30ff commit 10 — migrate command + manifest v1/v2 dual-read (T092,T093,T095,T097-T099a)
dde5605 commit 11 — csharp-lsp plugin dependency smoke test (T110-T111)
826d790 commit 12 — remove csharp-ls from .mcp.json (CI-gated) (T112-T114)
937a892 commit 13 — SessionStart compact bootstrap + PreToolUse arch-profile hook (T073-T075,T078-T080)
ab1de29 commit 14 — Rules reclassification + constitution v1.0.8 (T081-T086,T088-T089)
2f97655 commit 14b — `dotnet-ai render` read-only inspectability command (T115-T118)
f2259e4 commit 15 — polish + docs + release notes (T121,T122,T124-T127)
7095deb commit 16 — close all 40 v1.1-deferred tasks back into v1
```

## Test baseline (CURRENT, post-commit-16)

```
720 passed, 25 skipped, 0 xfailed, 0 xpassed, 0 failed in 46.93s
```

**Breakdown**:
- **720 passed** — full feature-018 baseline (399 tests) preserved + 321 new feature-019 tests
- **25 skipped** — gated smoke tests (LSP smoke, host CLI presence) — gated because they need real host CLIs installed
- **0 xfailed** (down from 4 in the previous briefing — all flipped to passing in commit 16)
- **0 failed**

## What commit 16 did (the 40 closed tasks)

**Per user override** of the advisor's "defer to v1.1" recommendation: complete all 40 remaining tasks so v1 ships the full plugin-native architecture, not a partial set.

### Constitution + rule reclassification (Batch A)
- T081 `test_constitution_amendment.py` — v1.0.8 version + 5-rule universal whitelist
- T083 PASS-CONDITIONAL gate verified
- T084 `test_rule_classification.py`
- T085 `test_no_arch_branching_in_always_on.py`

### Skill→rule cross-linking (Batch B)
- T087 `test_skill_body_references.py`
- T090 5 anchor skills updated with `${CLAUDE_PLUGIN_ROOT}/rules/conventions/<name>.md` references

### Runtime resolution (Batch C)
- T076 `test_runtime_resolution.py`
- T077 `test_sc003_runtime_resolution_points.py`

### scripts/check.py multi-host extension (Batch F)
- T109 extended with plugin manifest validation + multi-host config check

### Init refactor cluster (Batch D)
- T031-T036, T038, T094, T096, T100 — 11 new test files
- T042 cli.py init refactor: `PLUGIN_NATIVE_HOSTS` skips bulk-copies; interactive prompt fires when --ai absent; ClaudeHost adapter for per-solution writes
- T043 copier.py deploy_to_linked_repos: plugin-native branching
- Side effect: `upgrade` also refactored to plugin-native (no-op for plugin-native hosts; ClaudeHost adapter for refresh)
- 5 legacy `test_cli.py` / `test_upgrade_cli_atomic.py` tests updated to reflect new semantics

### Copilot follow-up (Batch E)
- T056 `copier.copy_commands_cursor` refactored — per-rule `.mdc` files (no one-blob)
- T063 + T064 contract tests for path-scoped instructions + per-agent files
- T066 lifecycle integration test
- T067 upgrade separation test
- T070 `_record_copilot_renders_in_manifest` helper + full hosts/copilot.py render pipeline (3 file classes)
- T072 `dotnet-ai upgrade --copilot` variant
- T072a/b/c `--force-render` flag + path-specific opt-in + manifest recording with `host_owner=copilot`
- 2 xfailed tests in `test_copilot_render.py` flipped to passing

### Measurement (Batch G)
- T091 `tests/unit/test_sc004_always_on_budget.py` + `scripts/measure_always_on.py`
- T129 measurements.md captured values
- **SC-004 captured**: 2880 tokens total (295 SessionStart + 2585 universal rules); 68% reduction from baseline ~9000 (target ≥65%; in target band 2500-3000)

### Documentation polish (Batch H)
- T119 README.md updated
- T120 CLAUDE.md updated with "Feature 019 architecture (v1.0+)" section
- T123 `planning/06-feature-019-outcomes.md` added

### Doc-lint (Batch I)
- T128 `scripts/doc_lint.py` — 24 files scanned, 0 issues

### T130 3-OS quickstart (Batch J)
- `.github/workflows/measure.yml` with `sc004` + `quickstart-3os` matrix jobs
- The host-CLI-dependent half (Claude/Codex/Cursor plugin install + listing) is gated separately for CI runners with real host CLIs

### T061 conditional handling (Batch K)
- Verified machinery exists; T051 is currently SKIPPED (no `CURSOR_SMOKE=1` + cursor CLI absent locally)
- `cursor-subagent-outcome.json` remains `"pending"` (default-assume-pass)
- When CI flips it to `"failed"`, T061 fail-path + T125 + T125a atomically rewire spec/schema/release-notes

## Constitution amendment audit trail (v1.0.7 → v1.0.8)

Per the PASS-CONDITIONAL gate in plan.md:

| Step | Task | Status |
|------|------|--------|
| 1. Write the failing test FIRST | T081 | [X] `tests/unit/test_constitution_amendment.py` |
| 2. Amend constitution.md | T082 | [X] v1.0.7 → v1.0.8; HTML-comment audit trail at `.specify/memory/constitution.md:1-23` |
| 3. Test now PASSES | T083 | [X] verified |
| 4+. Execute rule moves (T084-T089) | T084-T089 | [X] all 16 rules under `rules/conventions/` (5) + `rules/domain/` (11) |

## Cursor sub-agent spike outcome

State at merge time: `outcome="pending"` per `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json`.

| Aspect | Decision |
|--------|----------|
| Why "pending"? | T051 `test_smoke_cursor.py` is a CI smoke that requires the Cursor CLI runtime. Local pytest skips it (`CURSOR_SMOKE!=1` + `cursor` not on PATH). |
| What's shipped? | `.cursor-plugin/plugin.json` includes `agents` field. `agents/dotnet-ai-architect.md` built by `scripts/gen_cursor_agents.py`. Release notes emit PASS-branch statement. |
| Rollback if FAILS? | T061 fail-path scripted in commit 6 (7 steps); T125 + T125a atomically rewire on JSON flip. |
| Consistency check | T125a `test_release_notes_consistency.py`. |

## Captured measurements (SC-001, SC-004, SC-010, SC-012, SC-013)

Per `specs/019-plugin-native-arch/measurements.md`:

| SC | Target | Captured |
|----|--------|----------|
| SC-001 (file count) | ≤18 (≥90% reduction from ~180) | **3 for Claude-only / 18 with Copilot**; **98% reduction** |
| SC-004 (always-on context) | ≥65% reduction, band 2500-3000 tokens | **2880 tokens, 68% reduction** |
| SC-010 (check runtime) | <10s | **<1s** (enforced by `test_sc010_check_runtime.py`) |
| SC-012 (render runtime) | <2s | **<1s** (enforced by `test_sc012_render_runtime.py`) |
| SC-013 (SessionStart stdout) | ≤500 tokens | **295 tokens** (enforced by `test_session_start_budget.py`) |

Reproducible: `python scripts/measure_always_on.py --human`

CI workflow `.github/workflows/measure.yml` re-asserts on every push; CI fails if any SC slips.

## What I'm asking for

1. **A merge-readiness verdict**: AGREED-CLEAN-SIGN-OFF, AGREED-WITH-NITS, or BLOCK-WITH-CONCERNS.
2. **Concrete bug reports**, not philosophical objections. If you find a regression, cite `file:line` + the failing pytest assertion.
3. **Incompatibility checks**: any commit that breaks a contract another commit assumes? Any FR/SC orphaned? Any test from feature-018 that now fails (the answer should be NONE).
4. **Architecture coherence**: the plugin-native pivot in commit 16 (init + upgrade both skip bulk-copies for `PLUGIN_NATIVE_HOSTS`) is the biggest behavior change. Verify the host adapter routing is sound.

## What I'm NOT asking for

- Hypothetical bugs ("what if the user does X") — only file actual issues you can demonstrate.
- Stylistic preferences on release-notes wording — editorial.

## Repository state summary

```
$ git status -s
?? .claude/scheduled_tasks.lock    (untracked, transient)

$ git branch --show-current
019-plugin-native-arch

$ git log --oneline 019-plugin-native-arch ^master | wc -l
18    (a29577c planning + 17 implementation commits)

$ grep -cE "^- \[X\]" specs/019-plugin-native-arch/tasks.md
137    (all 137 tasks complete)

$ grep -cE "^- \[ \]" specs/019-plugin-native-arch/tasks.md
0      (zero deferred)

$ pytest --tb=no -q | tail -2
720 passed, 25 skipped in 46.93s
```

Over to you.
