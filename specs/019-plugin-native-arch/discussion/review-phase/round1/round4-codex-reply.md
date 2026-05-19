# Round 4: Codex reply

## Verdict

**REFUTED-CLAIM-E; otherwise AGREED-WITH-NITS.**

The Phase 10 task additions cover the known B-1 through B-8 defects and the important round-3 corrections. I do not see a missing blocker fix task. However, OOS-003 is now contradictory across artifacts, and a few status/traceability/acceptance claims are overstated.

## Per-claim findings

### Claim A - Math

Accepted. I verified:

- `tasks.md` is 624 lines.
- Task count is 132 checked + 75 unchecked = 207.
- T004, T029, T042, T043, and T065 are unchecked with inline review-phase notes.
- Phase 10 is T131-T200 across commits 16-30.
- B-token counts in `tasks.md` match the claim.
- `uv run python scripts/doc_lint.py` passes with 24 files scanned.

### Claim B - Mapping completeness

Mostly accepted. Every B-N has at least one Phase 10 task touching the cited implementation surface, and the concrete correction tasks are present:

- B-1 stale-profile trap is covered by T138/T139, including `copier.py:1131-1137` at `specs/019-plugin-native-arch/tasks.md:366-367`.
- B-2 full config call-path migration is covered by T140-T145, especially T144 at `specs/019-plugin-native-arch/tasks.md:371-376`.
- B-3/B-4 required-field derivation plus raw-then-model validation are covered by T146-T153 at `specs/019-plugin-native-arch/tasks.md:380-387`.
- B-7 and B-8 are covered by T157-T160 and T131 at `specs/019-plugin-native-arch/tasks.md:353` and `specs/019-plugin-native-arch/tasks.md:397-400`.
- F-F and C-Q4 are covered by T161/T162 and T175 at `specs/019-plugin-native-arch/tasks.md:404-405` and `specs/019-plugin-native-arch/tasks.md:427`.

Nit: the artifact phrase "8 plan corrections from Codex round 3" is now imprecise. The actual round-3 numbered list included OOS-005 as item 7 and B-1 as item 8 (`specs/019-plugin-native-arch/discussion/review-phase/round3-codex-verify.md:241-248`), while `plan.md` item 8 is C-Q4 (`specs/019-plugin-native-arch/plan.md:550-558`). The work is still wired because OOS-005 is covered by T167-T171 (`specs/019-plugin-native-arch/tasks.md:416-420`) and C-Q4 is covered by T175, but the label should be corrected.

### Claim C - Status line consistency

Mostly accepted, with three bookkeeping nits:

- `measurements.md` does not reference `discussion/review-phase/claude/final-consolidated-review.md` as the canonical fix plan, while the other five artifacts do. The missing link is visible because `measurements.md` only references `discussion/review-phase/` generically at `specs/019-plugin-native-arch/measurements.md:85-91`.
- `traceability.md` maps 21 Phase-10 test/gate rows, not 21 new test files. Examples: the smoke workflow row is not a test file, and the ruff cleanup row is explicitly not a test (`specs/019-plugin-native-arch/traceability.md:139-140`).
- The older headers still say the original plan is 16 commits and tasks are pending tasks-phase sign-off (`specs/019-plugin-native-arch/plan.md:12`, `specs/019-plugin-native-arch/tasks.md:6`) even though Phase 10 adds commits 16-30 (`specs/019-plugin-native-arch/tasks.md:341-464`).

### Claim D - Phase 10 task quality

Partly refuted. The tasks are generally implementable, but the exact claim "Every T131-T200 task has ... an explicit `**Acceptance**:` clause" is false. For example, T132 has no acceptance clause; T133 carries the commit acceptance (`specs/019-plugin-native-arch/tasks.md:357-358`). That is fine if the intended standard is commit-level acceptance, but the claim should say that.

Two commit-level acceptance gaps need tightening:

- Commit 25 has a pass-branch acceptance on T171, but no explicit fail-branch or pending-branch acceptance after T167-T170 (`specs/019-plugin-native-arch/tasks.md:416-420`).
- Commit 29's final acceptance only verifies the changelog entry, not AGENTS/CONTRIBUTING counts, the `rules/cursor/` decision, or the new manifest-path pytest gate (`specs/019-plugin-native-arch/tasks.md:454-458`).

### Claim E - OOS scope decisions

Refuted for OOS-003. The task plan says v1.0 now includes source-tree wrappers (`specs/019-plugin-native-arch/tasks.md:435-436`), and the canonical review narrows OOS-003 to standalone executables only (`specs/019-plugin-native-arch/discussion/review-phase/claude/final-consolidated-review.md:674`, `specs/019-plugin-native-arch/discussion/review-phase/claude/final-consolidated-review.md:720`). But `spec.md` still says "A `bin/` launcher for the tool" is deferred to v1.1 (`specs/019-plugin-native-arch/spec.md:262`). That is a real cross-artifact contradiction.

OOS-004, OOS-005, OOS-006, and OOS-007 look consistent enough:

- Codex native agents remain deferred in spec assumptions/OOS and T183 only adds forward-compat scaffolding (`specs/019-plugin-native-arch/spec.md:249`, `specs/019-plugin-native-arch/spec.md:263`, `specs/019-plugin-native-arch/tasks.md:438`).
- Cursor full generation remains conditional (`specs/019-plugin-native-arch/spec.md:248`, `specs/019-plugin-native-arch/spec.md:264`, `specs/019-plugin-native-arch/tasks.md:419-420`).
- OOS-006 and OOS-007 are unchanged (`specs/019-plugin-native-arch/spec.md:265-266`).

### Claim F - Execution order

Mostly accepted, but not a strict mapping. The canonical sequence puts OOS-005 neutralization at step 10, Tier 3 C-Q fixes at step 11, and OOS-005 conditional inclusion at step 12 (`specs/019-plugin-native-arch/discussion/review-phase/claude/final-consolidated-review.md:704-706`). `tasks.md` combines OOS-005 neutralization and conditional include into commit 25 before the C-Q fixes in commit 26 (`specs/019-plugin-native-arch/tasks.md:414-422`). If that reordering is intentional, update the final review sequence or the claim text.

## Newly-found issues

**P1 - OOS-003 scope contradiction.** `spec.md` still defers any `bin/` launcher to v1.1, while Phase 10 adds source-tree wrappers in v1.0. See the Claim E citations above.

**P1 - Commit 25 acceptance is branch-incomplete.** The fail/pending branch should have an explicit final acceptance gate, not only the T171 pass branch.

**P1 - Commit 29 acceptance is too narrow.** It should verify the whole tool-surface commit, not just the changelog entry.

**Nit - Canonical fix-plan cross-link missing from measurements.** Add the same link used by the other artifacts.

**Nit - "21 new test files" wording is inaccurate.** Use "21 Phase-10 test/gate rows."

## Phase 10 atomicity audit

Most tasks are atomic enough. Two should be split or tightened:

- T170 is too broad on the fail branch: it combines running the smoke decision with spec/schema/manifest/verification/generator/packaging/release-notes rewrites (`specs/019-plugin-native-arch/tasks.md:419`). Split into "run/record outcome", "fail-branch manifest/schema/spec edits", and "fail-branch code/packaging/release-notes/test edits".
- T195 is a conditional decision plus implementation in one line (`specs/019-plugin-native-arch/tasks.md:456`). Split the PASS and FAIL branches, or make the branch decision source explicitly "read T170/T171 outcome JSON, then do exactly one of these two edits."

## Required edits before implementation starts

1. Update `spec.md` OOS-003 to distinguish v1.0 source-tree wrappers from v1.1 standalone executable packaging.
2. Add the canonical `final-consolidated-review.md` link to `measurements.md`.
3. Fix the "8 round-3 plan corrections" wording: include OOS-005 as the actual round-3 item, or rename C-Q4 as a separate technical-accuracy correction.
4. Add explicit fail/pending acceptance for commit 25.
5. Broaden commit 29 acceptance to verify AGENTS/CONTRIBUTING counts, `rules/cursor/` branch outcome, and `tests/contract/test_plugin_manifest_paths.py`.
6. Align the OOS-005 conditional-inclusion order between `final-consolidated-review.md` and `tasks.md`, or state that commit 25 intentionally combines steps 10 and 12.
