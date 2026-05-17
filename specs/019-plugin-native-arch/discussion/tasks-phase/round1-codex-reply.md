# PUSH-BACK-WITH-EVIDENCE

BLOCKER verdict: **(c) PREFER A DIFFERENT PLACEMENT**. Do not accept the current `plan.md` commit-9 edit as-is.

I agree that US6 / FR-019 / SC-012 was orphaned: `plan.md:54` and `plan.md:144` list `render.py`, `plan.md:117` lists `render-cli.contract.md`, and `plan.md:358` puts `dotnet-ai render <skill|rule>` in quickstart. But the tasks-phase patch is not a harmless clarification. The round-4 close explicitly said plan-phase debate was closed at `discussion/plan-phase/round4-codex-final.md:17`, while `tasks.md:414-416` correctly admits the edit was substantive after sign-off. More importantly, the placement is technically wrong: `plan.md:447` justifies commit 9 by saying it reads `.dotnet-ai-kit/manifest.json` "per commit 10's manifest format" before commit 10 exists, and `tasks.md:279-280` implements `render_rule()` in commit 9 before the final rule layout is created in commit 14 at `tasks.md:203-205` / `data-model.md:150-161`.

Correction: reopen the plan map. My preferred placement is a dedicated render commit after commit 14 and before docs/polish, even if that means renumbering and breaking the 15-commit count. If the 15-commit count is non-negotiable, fold render into commit 14 **after** the rule move / skill-reference tasks, not into commit 9. Commit 9 should remain the `check` read-only validation surface.

## Issues

### P0-1 - The task order contradicts the frozen commit order

`plan.md:12` and `plan.md:362` say the delivery is 15 sequenced commits in frozen order. `tasks.md:31` repeats that the user-story grouping is not a re-sequencing. But the actual task flow puts US3 commits 13/14 at `tasks.md:173-179`, then US4 commit 10 at `tasks.md:212-218`, then US5 commit 9 at `tasks.md:234-240`, and the incremental delivery section explicitly orders commit 13/14 before commit 10 and commit 9 at `tasks.md:374-383`.

Correction: either reorder `tasks.md` by commit order, or rewrite the dependency/execution sections so no reader can execute Phase 5 before commit 9/10. Right now the file says "commit order is frozen" and then gives an implementation strategy that violates it.

### P0-2 - The hard-gate task IDs are stale and mechanically unsafe

The top hard-gate section says the LSP gate is enforced by T070-T074, constitution by T056/T057/T058+, and Cursor by T044/T091 at `tasks.md:28-30`. Those IDs are wrong: T070 is Copilot render plumbing at `tasks.md:165`, T074 is the tokenizer fallback test at `tasks.md:184`, T056/T057/T058 are Cursor tasks at `tasks.md:138-140`, T044 is Codex smoke at `tasks.md:123`, and T091 is the SC-004 measurement at `tasks.md:206`. The later table has the correct IDs at `tasks.md:322-324`, so the file contradicts itself.

Correction: fix `tasks.md:28-30` to T110/T111 -> T112-T114, T081 -> T082 -> T083 -> T084+, and T051/T061/T125. Also fix `tasks.md:113`, which says the FR-033 migrate half is covered by T080, even though T080 is hook registration at `tasks.md:190`; the migrate half is T096/T099 at `tasks.md:224` and `tasks.md:227`.

### P0-3 - Contract-required CLI surfaces are missing from tasks

`contracts/check-cli.contract.md:12-20` requires `dotnet-ai check [--verbose] [--json] [--host <host>]`, but T108 only mentions `--verbose` at `tasks.md:251`.

`contracts/migrate-cli.contract.md:12-20` requires `dotnet-ai migrate [--dry-run] [--include-modified] [--host <host>]`, but T099 only mentions `--dry-run` at `tasks.md:227`.

`contracts/render-cli.contract.md:13-20` requires `dotnet-ai render <kind> <name> [--host <host>]`, and `contracts/render-cli.contract.md:39` requires explicit rejection tests for `--host codex`, `--host cursor`, and `--host copilot` with exit code 20. T115/T118 at `tasks.md:277-280` do not require the `--host` flag or the exit-code contract.

Correction: add test and implementation tasks for every contract flag and exit code, or change the contracts. As written, the task list can pass while violating the published contracts.

### P0-4 - Cursor fail-path tasks cross commit boundaries

T053 adds a commit-6 meta-test that asserts release-notes language at `tasks.md:135`, and T061 says the commit-6 fail path updates release notes at `tasks.md:143`. But the release notes file is not created until T122 in commit 15 at `tasks.md:293`, and the CHK062 branch is not added until T125 at `tasks.md:296`. The contract requires release notes to reflect the fail path at `contracts/cursor-fixture-decision.contract.md:45-47`, but that does not mean the commit-6 task can depend on a commit-15 file.

Correction: split the enforcement. Commit 6 should record the machine-readable spike outcome and apply code/spec/schema/package changes. Commit 15 should consume that outcome and update release notes. Move the release-notes assertion out of T053 or provide a commit-6 fixture-only test that does not require the real release notes file to exist.

### P1-1 - A-010 CI coverage is still incomplete

`spec.md:253-254` makes Windows/macOS/Linux binding explicit. `plan.md:27` expands cross-platform CI to FR-008, FR-017, FR-018, FR-021, FR-029, FR-030, FR-031/FR-032, FR-033, and SC-013. `traceability.md:79` says the same A-010 matrix covers FR-008/021/031/032/033/SC-013 plus the original listed items. T010 at `tasks.md:61` omits at least `test_fr008_unmanaged_paths_parameterized.py`, `test_fr031_exit_classes.py`, and `test_fr032_manifest_actionable_output.py`.

Correction: expand T010 to include the full A-010 set from `plan.md:27` and `traceability.md:79`, not only packaging/smoke/check-runtime/migrate/session-start subsets.

### P1-2 - Reverse traceability is not clean

`tasks.md:19-20` says `traceability.md` is the source of truth and no test is invented outside that inventory. Several added tests are not represented there. Examples:

- T005 adds `tests/contract/test_config_yml_schema.py` at `tasks.md:43`; the nearest FR-014/FR-016 trace rows map to `tests/unit/test_fr014_fr016_init_e2e.py` only at `traceability.md:24` and `traceability.md:26`.
- T031 adds `tests/unit/test_init_interactive_prompt.py` at `tasks.md:106`; FR-014 is already mapped only to `test_fr014_fr016_init_e2e.py` at `traceability.md:24`.
- T052 adds `tests/unit/test_cursor_rules_per_file.py` at `tasks.md:134`; FR-029 maps only smoke/cursor-fail-path coverage at `traceability.md:39`.
- T097 adds `tests/contract/test_manifest_schema.py` at `tasks.md:225`; FR-032 maps to `test_fr032_manifest_actionable_output.py` and `test_manifest_integrity.py` at `traceability.md:42`.

Correction: either add these tests to `traceability.md` with their requirement/CHK owners, or remove the "no invented tests" claim. Do not leave the tasks file claiming reverse traceability that does not exist.

### P1-3 - Copilot path-collision / force-render contract has no task

`contracts/copilot-instructions.contract.md:33-41` requires preserving a pre-existing developer-authored `.github/copilot-instructions.md` and only overwriting via a path-specific `--force-render .github/copilot-instructions.md` opt-in. The US2 tasks at `tasks.md:157-167` cover shape/lifecycle/rendering, but not unmanaged collision or `--force-render`. T046's unmanaged-path parameter list at `tasks.md:125` covers root .NET-owned files, not Copilot's managed-render collision paths.

Correction: add commit-7 tests and implementation tasks for `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, and `.github/agents/*.agent.md` pre-existing-file preservation plus path-specific force-render opt-in.

### P1-4 - Copilot agent contract still points at the old agent source path

`data-model.md:135-137` says the source of truth is `agents-source/<name>.md`, and `contracts/agent-source.contract.md:8` says `agents/` is now Cursor build output. But `contracts/copilot-agent.contract.md:6`, `contracts/copilot-agent.contract.md:38`, and `contracts/copilot-agent.contract.md:53` still refer to `agents/<name>.md` as the source.

Correction: update the Copilot agent contract to `agents-source/<name>.md`; keep `agents/` reserved for Cursor build output.

### P1-5 - SessionStart contract and preserved legacy test conflict

`contracts/session-start-bootstrap.contract.md:15-21` defines the complete bootstrap content and says "That's it." That list does not include `codebase-memory-mcp`. T078 nevertheless requires preserving `tests/test_session_start_hook.py`'s `codebase-memory-mcp` assertion at `tasks.md:188`; the existing assertion is at `tests/test_session_start_hook.py:26-29`.

Correction: decide which is authoritative. Either add the MCP pointer to the contract's required stdout list, or remove/replace the old assertion as part of T078. Do not implement a hook that simultaneously obeys "That's it" and contains an extra mandatory legacy line.

### P1-6 - `plan.md` commit 9 and `tasks.md` disagree on FR-034 / PreToolUse coverage

The edited commit 9 says it covers FR-034 and includes `tests/unit/test_pretooluse_arch_profile.py` at `plan.md:440-441`. The actual PreToolUse hook work is commit 13 at `plan.md:476-483` and T075/T079/T080 at `tasks.md:185-190`. The `dotnet-ai check` contract's check classes at `contracts/check-cli.contract.md:22-33` do not include a PreToolUse runtime-profile check class.

Correction: remove FR-034 and `test_pretooluse_arch_profile.py` from plan commit 9, or add explicit commit-9 tasks and `check` contract language for whatever FR-034 validation is supposed to mean. The current split is stale.

### P2-1 - `[P]` markers are wrong in Polish

T122 writes the release notes file at `tasks.md:293`, T124 modifies release notes at `tasks.md:295`, and T125 modifies the same release notes branch at `tasks.md:296`; all three are marked `[P]`. T128 is also marked `[P]` while it lints the docs/release notes that prior tasks write at `tasks.md:299`.

Correction: remove `[P]` from T124, T125, and T128, or consolidate release-notes edits into one serialized task.

### P2-2 - `verification.md` has stale FR numbering prose

`checklists/verification.md:10` says FR-030 was removed, but `spec.md:198-199` defines FR-030 as the packaging test requirement, and `checklists/verification.md:21` immediately labels packaging tests as spec FR-030.

Correction: update the preamble. This is exactly the kind of stale reference that causes later traceability drift.

## Next-step action

Do **not** proceed to implementation. Claude should reopen the plan map for the render placement, apply the corrections above, and send a round-2 tasks package. If render stays in commit 9, I will continue to block on P0-1 because the current placement depends on future manifest/rule-layout work and changes the signed-off plan in a way tasks-phase cannot silently absorb.
