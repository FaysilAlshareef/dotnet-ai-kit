# PUSH-BACK-WITH-EVIDENCE

Round 2 fixed most of the round-1 substance, and I agree with the new **commit 14b** placement: after commit 14's finalized rule layout and before commit 15 docs/polish is the right location for `render`.

This is **not clean enough to unblock `/speckit.implement`**. The patch still leaves stale 15-commit / commit-9-render references in current source-of-truth files, and the Cursor spike outcome handoff is mechanically incomplete on the pass path.

## Round-1 Correction Verification

| Round-1 issue | Verification |
|--|--|
| BLOCKER (render placement) | Mostly landed. `plan.md:12` now declares 16 commits; `plan.md:436-445` keeps commit 9 check-only and explicitly excludes render/FR-034; `plan.md:492-499` adds commit 14b; `tasks.md:306-313` maps T115-T118 to commit 14b with `--host` and exit-code coverage. **But stale contradictory references remain; see P0-1/P1-1 below.** |
| P0-1 task order vs commit order | Mostly landed. `tasks.md:26-57` adds a binding commit-order table; `tasks.md:341-358` and `tasks.md:405-433` now describe commit-sequential execution. **But stale ordering prose remains at `tasks.md:367` and `tasks.md:380`; see P1-1.** |
| P0-2 stale hard-gate task IDs | Landed. `tasks.md:54-56` now uses T110/T111 -> T112-T114, T081 -> T082 -> T083 -> T084+, and T051/T061/T125. `tasks.md:139` fixes the FR-033 migrate half to T096/T099. |
| P0-3 missing CLI flags / exit codes | Landed. `tasks.md:281-282` covers `check --verbose/--json/--host` and all check exit codes; `tasks.md:256-257` covers `migrate --dry-run/--include-modified/--host`; `tasks.md:310-313` covers render `--host` plus exit codes 0/20/21/22/23. |
| P0-4 Cursor fail-path cross-commit | Incomplete. `tasks.md:161` correctly makes T053 fixture-only, and `tasks.md:169` correctly says commit 6 must not touch release notes. But T125 reads `.dotnet-ai-kit/spike-outcomes/cursor-subagent.json` at `tasks.md:329`; only the fail-path T061 writes that JSON at `tasks.md:169`. The pass-path T060 writes only a markdown outcome at `tasks.md:168`, so T125 has no machine-readable JSON to read when the Cursor fixture passes. |
| P1-1 A-010 CI matrix | Partially landed. `tasks.md:87` now lists the broad cross-platform set. However it still conflicts with `plan.md:378` and `traceability.md:13/40/59`, which name `tests/integration/test_packaging_linux.py`; tasks only create/run `tests/test_packaging.py`, `test_packaging_macos.py`, and `test_packaging_windows.py` at `tasks.md:83-87`. |
| P1-2 reverse traceability | Landed for the cited added tests. `traceability.md:98-117` adds rows for T005/T021/T031/T045/T052/T081/T087/T097/T099a/T108a/T072a/T072b/T125a. |
| P1-3 Copilot path collision / `--force-render` | Landed. `tasks.md:194-196` covers preservation for `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.github/agents/*.agent.md`, plus path-specific `--force-render` for both `init` and `upgrade --copilot`. The existing contract text at `contracts/copilot-instructions.contract.md:33-41` is sufficient; no separate contract edit is required unless you want the CLI spelling locked more formally. |
| P1-4 Copilot agent source path | Landed. `contracts/copilot-agent.contract.md:6`, `:38`, and `:53` now use `agents-source/<name>.md`. |
| P1-5 SessionStart vs legacy MCP assertion | Landed. `contracts/session-start-bootstrap.contract.md:20-22` adds the persistent-memory line and keeps the ≤500-token constraint explicit. |
| P1-6 commit 9 FR-034 inconsistency | Landed. `plan.md:440-445` excludes FR-034 and `test_pretooluse_arch_profile.py` from commit 9 and points FR-034 to commit 13. |
| P2-1 `[P]` markers in Polish | Landed. `tasks.md:328-330` and `tasks.md:333` serialize T124/T125/T128 around the release-notes file. |
| P2-2 `verification.md` FR-030 stale prose | Landed for the requested line. `checklists/verification.md:10` now states FR-030 is present at `spec.md:198-199`. |

## Remaining Blocking Issues

### P0-1 - Cursor spike outcome handoff is still not mechanically safe

`tasks.md:329` makes T125 read `.dotnet-ai-kit/spike-outcomes/cursor-subagent.json` and branch on `outcome == "passed"` vs `"failed"`. But `tasks.md:169` writes that JSON only in T061, which is explicitly **FAIL-PATH ONLY**. The pass path has T060 at `tasks.md:168`, but that task records only `specs/019-plugin-native-arch/discussion/plan-phase/cursor-spike-outcome.md`.

Correction: make one machine-readable source of truth exist on both pass and fail paths. Preferred placement: `planning/cursor-subagent-spike-outcome.json` or `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json`, not `.dotnet-ai-kit/...`. Then update T060, T061, T125, T125a, and the open item at `tasks.md:491` to use that path. If you keep `.dotnet-ai-kit/...`, T060 must also write it on pass, and the tasks must stop calling it "per-solution data" at `tasks.md:491`.

### P1-1 - 16-commit conversion is incomplete

Current source files still state the old 15-commit reality:

- `plan.md:77` says each commit in the 15-commit order ships tests first.
- `plan.md:362` says the 15-commit order is frozen.
- `plan.md:514` says all 15 commits land in one PR.
- `plan.md:518` says `/speckit.tasks` decomposes 15 commits.
- `plan.md:524` still asks whether the 15-commit order is byte-identical to FINAL-REPORT.
- `tasks.md:5` calls `plan.md` a 15-commit map.
- `tasks.md:13` says `(commit N)` preserves the frozen 15-commit order.
- `tasks.md:367` says commits `1..15` land in sequence.
- `tasks.md:451` repeats the frozen 15-commit note.
- `checklists/verification.md:6` still cites the converged 15-commit order.
- `checklists/requirements.md:73` still says the architecture-phase folder carries the 15-commit order.

Correction: update current planning/checklist artifacts to say "original 15-commit architecture order plus tasks-phase commit 14b" or simply "16-commit order: 1..14, 14b, 15". Historical discussion files do not need edits.

### P1-2 - Commit 9 render-bundling text still survives

Two current task lines directly contradict the accepted round-2 placement:

- `tasks.md:272` says commit 9 is "the check-half of the bundled check+render commit".
- `tasks.md:456` says `plan.md` commit 9 was patched to bundle `render` alongside `check`.

Correction: remove both statements or rewrite them to say commit 9 is check-only and render moved to commit 14b.

### P1-3 - A-010 packaging test names still drift

`plan.md:378` says commit 2 tests are `tests/integration/test_packaging_linux.py`, `test_packaging_macos.py`, and `test_packaging_windows.py`. `traceability.md:13`, `traceability.md:40`, and `traceability.md:59` also use `test_packaging_{windows,macos,linux}.py`. But `tasks.md:83-87` modifies `tests/test_packaging.py` and only adds macOS/Windows integration tests; no Linux integration test appears.

Correction: either add a T006/T007/T008-style task for `tests/integration/test_packaging_linux.py`, or change `plan.md` and `traceability.md` to make `tests/test_packaging.py` the Linux/default matrix test. Do not leave the traceability inventory naming a test the task plan never creates.

## Open Item Answers

1. Commit 14b placement is correct: after commit 14 and before commit 15.
2. The binding Commit Execution Order table is acceptable; do not reorder the SDD user-story phases just to satisfy commit order.
3. The spike outcome file approach is not acceptable as currently written because the pass path lacks JSON and `.dotnet-ai-kit` is the wrong namespace for release-planning state.
4. `contracts/copilot-instructions.contract.md:33-41` is enough for T072c; the tasks lock the `--force-render <path>` spelling sufficiently.
5. T125a belongs in commit 15 because it validates the real release-notes artifact after release notes exist.

## Next-Step Action

Do **not** proceed to implementation. Apply the four corrections above, then send a round-3 verification package. This should be a small cleanup pass, not a reopened placement debate.
