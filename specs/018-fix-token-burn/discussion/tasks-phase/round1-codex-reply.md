# Tasks Phase Round 1 — Codex reply

Overall: **REVISE**. The PR structure is sound and most tasks are at the right scale, but several verification tasks are in the wrong PR, a few `[P]` markers conflict with actual file paths, and there are missing tasks around dynamic hook migration, `/dai.upgrade` wiring, MCP config persistence, SC-014, and selective memory reads.

## Critique by phase

- Phase 1 Setup: **REVISE**. Good shared scaffolding. T001 and T005 both register the smoke marker; keep marker registration in `pyproject.toml` and let `tests/smoke/conftest.py` own skip-gating. Also decide now whether `scripts/check.py` supports a target root, because T076 later needs to run it against a synthetic violation fixture.

- Phase 2 PR0 Baseline: **AGREE**. Baseline-before-behaviour-change ordering is correct. T006 should explicitly support all four scenarios and median-of-3 output, not just `claude --headless -p '/cost'`; otherwise T007-T010 become manual one-offs.

- Phase 3 PR1: **REVISE**. Hook/packaging coverage mostly matches the plan, but FR-001 lacks a test task for the SessionStart script body. The dynamic `_source: dotnet-ai-kit-arch` hook path in `src/dotnet_ai_kit/copier.py` is tested later in T064 but has no implementation task and is misplaced if FR-005 is PR1 scope. Add/update tasks here for dynamic hook `if:` migration and Claude Code version detection, or explicitly move that slice out of PR1.

- Phase 4 PR2a: **REVISE**. Mechanical rewrite tasks are mostly right. Problems: T022 uses a brittle `description >=20 chars` assertion despite the spec saying no brittle minimum-character test; T031 and T032 are both `[P]` but edit the same two agent files; and profile `paths:` / FR-017 is ambiguously split between PR2a and PR3.

- Phase 5 PR2b: **REVISE**. The tests-first structure is good, and PR2a -> PR2b dependency is correct. Missing: task to wire the new `upgrade.py` orchestrator into the existing CLI `/dotnet-ai upgrade` path; tests for dry-run, user-modified checksum mismatch, `--force`, and legacy-no-manifest behavior; an end-to-end `/dai.init` token-substitution verification for SC-006.

- Phase 6 PR3: **REVISE**. The PR3 -> PR4 dependency is correct in concept, but T047 violates it by adding MCP-first assertions in PR3 before PR4 implements them. T050/T051 are marked parallel while both claim `rules/*.md`; enumerate disjoint files or serialize. T058 is too broad and qualitative for a single task.

- Phase 7 PR4: **REVISE**. Core MCP and memory split tasks are present, but T069 conflicts with T072 on `commands/learn.md`. SC-014 is not actually covered. Add tasks for Windows MCP detection persistence, `.mcp.json` merge/no-clobber deployment behavior, and `/dai.plan` / `/dai.review` selective topic-file reads.

- Phase 8 PR5: **REVISE**. Measurement and traceability sequencing is right. Add a CI-config test for FR-029 instead of only editing `.github/workflows/ci.yml`. T087 should be a scripted/temp-fixture violation harness, not "17 PRs on a throwaway branch".

- Phase 9 Polish: **REVISE**. T089 is not safely `[P]` because it can touch `src/`, `tests/`, and `scripts/` while T091 adds tests. T091 is a real integration test and probably belongs in PR5 if it must gate the final feature; Polish should not be the first place required test coverage appears.

## Granularity / [P] marker review

- T001: split marker registration from smoke skip-gating, or remove marker registration from T001 because T005 owns `pyproject.toml`.

- T006: slightly too coarse/vague. Make it "create `scripts/measure.py` with subcommands/scenario flags for SC-001/002/003/007, median-of-3 aggregation, and append/report modes".

- T013: add concrete checks for `hooks/session-start-bootstrap.sh` forbidden eager-loading phrases and positive lazy/MCP-first language, or create a separate test task. Current PR1 has T015 implementation without a preceding test.

- T018/T064: T064 tests dynamic arch hook behavior, but no matching implementation task exists. Add a task against `src/dotnet_ai_kit/copier.py` and place it in the same PR as its test.

- T022: replace the `>=20 chars` check with a trigger-sentence check such as `description.startswith("Use when ")` or an agreed wording-tolerant predicate. Also remove FR-014/FR-015 from T022's coverage note; those are agent-body requirements covered by T024.

- T023/T049/T052: add an explicit profile-path assertion. Current tests check rules outside the whitelist but do not assert every `profiles/**/*.md` has `paths:`.

- T031 + T032: not parallel. Both edit `agents/dotnet-architect.md` and `agents/reviewer.md`. Merge T032 into T031 or remove `[P]` from T032.

- T039/T040: line references are stale relative to the current repo. Reword as "replace every raw `project.yml` `yaml.safe_load` consumer with `load_project()`" and identify current consumers by grep, not approximate line numbers. In `copier.py`, there is one raw `project.yml` load with three consumers, not three independent loads.

- T042/T045: explicitly include manifest root fields from `contracts/manifest.schema.json`: `schema_version`, `created_at`, and `last_upgrade_at`. T045 currently lists only file-entry fields.

- T047: split it. PR3 should only test removal of bulk-load instructions. Move MCP-first and fallback-line assertions to T063 in PR4.

- T050 + T051: over-marked as `[P]` as written because both end with `rules/*.md`. They are only parallel if T050 enumerates the 12 non-universal rule files and T051 enumerates the 4 universal files.

- T051: says "move pattern examples to corresponding skills" but only names `rules/*.md`. Either change to "remove" or add concrete skill destination paths/tasks.

- T058: too coarse. Split into an audit/list task plus concrete edits for known files, or define a deterministic static check for the duplicated architecture narrative being removed.

- T069 + T072: not parallel. Both edit `commands/learn.md`. Either exclude `learn.md` from T069 and let T072 add its MCP block, or serialize.

- T072: path list is incomplete if it updates `/dai.plan` and `/dai.review` references. Add `commands/plan.md` and `commands/review.md` or move that part to a separate task.

- T073: "and any other consumers" is vague. Current grep shows at least `README.md`, `commands/plan.md`, and `skills/workflow/plan-templates/SKILL.md` reference the monolithic constitution. Name the files or make T073 an audit task followed by concrete edits.

- T076: depends on `scripts/check.py` being able to run checks against a fixture or temp root. Add a T003/T076 contract for `--root` or an equivalent env var; otherwise the known-violation fixture cannot be tested without mutating the repo.

- T087: too operationally heavy and not a good task unit. Replace "17 PRs" with an automated script or pytest helper that mutates a temp copy once per violation class and asserts the named test failure.

- T089: remove `[P]`; broad lint/format fixes can overlap with any `src/`, `tests/`, or `scripts/` task.

## Missing tasks

- Add PR1 test coverage for FR-001/F01: `hooks/session-start-bootstrap.sh` must not contain the eager-load phrases and must contain the positive lazy-default/MCP-first replacement.

- Add implementation for dynamic architecture hook migration in `src/dotnet_ai_kit/copier.py`: preserve `_source: dotnet-ai-kit-arch`, but use handler-level `if:` when Claude Code v2.1.85+ is detected. T064 currently only tests this.

- Add Claude Code version detection. Research/plan say runtime detect v2.1.85+ in `mcp_check.py` or a sibling, but T067 only checks `codebase-memory-mcp --version`.

- Add PR2a or PR3 test coverage that every `profiles/**/*.md` has top-level `paths:` after the agreed phase. This closes FR-017 directly.

- Add a deterministic FR-016/F12 task. T058 says to strip duplicate architecture narrative but does not define the target files or a verification mechanism.

- Add CLI integration for `src/dotnet_ai_kit/upgrade.py`: existing `cli.py::upgrade` must call `run_upgrade()` and return the non-zero failure status from atomic rollback.

- Add `/dai.upgrade` tests for: dry-run writes nothing, user-modified managed file aborts without `--force`, `--force` behavior, legacy install with no manifest, and backup rotation retaining last 3 runs.

- Add a task to ensure `.dotnet-ai-kit/.gitignore` is created/updated during both `/dai.init` and `/dai.upgrade`, not only init. Legacy projects need it too.

- Add an end-to-end SC-006 test: run init/deploy on the non-default fixture layout and grep deployed skills for literal `${detected_paths.` returning zero.

- Add `.mcp.json` merge/deploy behavior. T061 asserts no clobber with pre-existing servers, but T066 only edits the root `.mcp.json`; there is no task for how installed projects merge the MCP entry while preserving unrelated servers.

- Add `cli.py::configure` implementation if T071 keeps saying `/dai.configure` invokes `mcp_check.run()`. As written T071 is command-template documentation only.

- Add SC-014 coverage: Windows-style `codebase-memory-mcp --version` detection, result recorded in `.dotnet-ai-kit/config.yml`, and rerun does not re-prompt or change state unexpectedly. This can be a Windows-marked smoke test plus a mocked unit test.

- Add memory split downstream edits for `commands/plan.md`, `commands/review.md`, and README's memory section. Current T072/T073 do not name all current monolithic-constitution references.

- Extend T065 to assert `constitution.md <= 100` physical lines and that plan/review load only the relevant topic file, not the full topic set. Current T065 only checks file existence and `commands/learn.md` wording.

- Add FR-029 CI-config verification, e.g. `tests/test_ci_config.py` parsing `.github/workflows/ci.yml` to assert static/unit runs on PRs and smoke is gated by label/nightly.

- Add `tests/integration/` directory setup if T091 stays, or move T091 into PR5 so the integration test is part of final CI gates.

## Wrong / Redundant tasks

- T022's `description >=20 chars` is wrong for the accepted spec wording. Use trigger semantics, not length.

- T047's MCP-first assertions are redundant with T063 and wrong in PR3 because PR4 owns the MCP block insertion.

- T064 is mis-phased if it verifies FR-005 dynamic hook filtering. It belongs with PR1 hook work or with a newly explicit PR2b upgrade-migration task, not PR4 MCP/memory.

- T087's "one PR each on a throwaway branch" does not earn its operational cost. A temp-copy mutation harness gives the same SC-010 evidence without 17 throwaway PRs.

- T001 marker registration is redundant with T005 unless T001 only handles skip gating.

## Dependency review

- PR2a -> PR2b: **correct**. Frontmatter canonicalization before token-substitution/upgrade tests is a reasonable dependency.

- PR3 -> PR4: **correct**, but T047 breaks the boundary. PR3 must remove bulk-load prose first; PR4 should then add MCP-first prose and fallback-line tests/implementation.

- PR1 vs PR4: dynamic hook `if:` migration should not wait until PR4 unless the plan reclassifies it. It is part of FR-005/FR-034 hook correctness, not MCP behavior.

- PR2b ordering: `manifest.py` should land before `upgrade.py`, and `upgrade.py` should land before CLI wiring. The task list has the first two but lacks the CLI wiring step.

- PR5 vs Polish: T091 is a gating integration test if it verifies end-to-end install/upgrade migration. Put it in PR5 or explicitly mark it non-gating exploratory validation.

- Test-first ordering is mostly good, except T047 contains assertions for PR4 implementation while listed as a PR3 test that must pass in PR3.

## SC coverage check

- SC-001: T007 baseline + T080 post-fix + T084 verdict. Covered, assuming T006/T084 compute median and reduction consistently.

- SC-002: T008 + T081 + T084. Covered.

- SC-003: T009 + T082 + T084. Covered.

- SC-004: T012 unit plus T077 smoke. Covered for runtime blocking.

- SC-005: T012 unit. Covered for the mocked formatter scenario specified by the SC; optional full formatter smoke is not explicitly tasked.

- SC-006: T035 covers token substitution at unit level, but end-to-end `/dai.init` on a non-default fixture layout is missing. Add an integration/smoke task.

- SC-007: T010 baseline + T083 post-fix measurement. Add explicit answer-quality parity recording to T083/T084; token measurement alone is incomplete.

- SC-008: T063 static template check + T078 smoke. Covered.

- SC-009: T003/T076/T086. Covered if `scripts/check.py` excludes smoke reliably and T086 records the <=30s result.

- SC-010: T075/T079/T087. Covered in intent, but T087 should be scripted/temp-fixture based.

- SC-011: T048 + T060 + T086. Covered.

- SC-012: T065/T072/T073 cover part of it. Gaps: assert `constitution.md <=100`, and verify `/dai.plan` / `/dai.review` read only needed topic files.

- SC-013: T037/T043/T046 cover atomic rollback/idempotency. Add dry-run, user-modified, force, and legacy-no-manifest cases for full FR-031/032 confidence.

- SC-014: **gap**. T062 mocks MCP version parsing and T068 records init outcomes, but no Windows fixture/runtime detection and no reproducible config.yml rerun check are tasked.

- SC-015: T013/T018 cover config-level `if:` filters. If the "hook-invocation log" part is required, add a small smoke/integration task that proves non-`.cs` Edit/Write does not spawn `dotnet format`.

- SC-016: T035 + T041 cover fail-closed substitution. Covered.

Runtime smoke summary for the four called out in the prompt:

- SC-004 -> T077: yes.
- SC-008 -> T078: yes.
- SC-012 -> T065: partial; file creation yes, selective reads and line ceiling missing.
- SC-014 -> missing explicit smoke/integration task.

## Open disputes for round 2

- Decide whether profile `paths:` (FR-017) is PR2a or PR3. The current tasks put it in PR3 while some PR2a text claims FR-017.

- Decide where dynamic `_source: dotnet-ai-kit-arch` hook migration and Claude Code version detection live. My preference: PR1, because it is hook correctness.

- Decide whether `.mcp.json` only needs root plugin packaging or also installed-project merge/no-clobber behavior. T061 currently implies the latter.

- Decide whether FR-016/F18 can be satisfied by an audit/checklist, or whether tasks need deterministic static tests for known duplication patterns.

- Move PR4-only command-body tests out of T047 before implementation starts. This is the main test-first/dependency correction.
