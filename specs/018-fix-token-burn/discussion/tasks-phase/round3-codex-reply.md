# Tasks Phase Round 3 - Codex reply

Not ready for `/speckit.analyze` yet. Most round-1 corrections are applied, but three mechanical issues remain in `tasks.md`.

## Remaining issues

### 1. `[P]` conflict: T037 and T037a

Both tasks are marked `[P]` and both edit `tests/test_upgrade_atomic.py`:

- T037 writes the initial `tests/test_upgrade_atomic.py`
- T037a extends the same file with more cases

This violates the `[P]` rule for disjoint file ownership. Fix by either:

- merging T037a into T037, or
- removing `[P]` from T037a and making it explicitly follow T037.

### 2. PR5 test-first ordering: T091 is in Implementation

T091 writes `tests/integration/test_end_to_end_install.py`, but it appears under "Implementation for PR5" after implementation tasks.

Because round 2 states all test tasks precede implementation in the same phase, move T091 into "Tests for PR5 (write first)" before T079.

### 3. SC-015 matrix references an assertion not present in T064

The SC coverage matrix says:

`SC-015 | T013 + T018 + (hook-invocation log assertion in T064)`

But T064 currently only checks:

- dynamic arch hook injection still works
- v2.1.85+ emits handler-level `if:` for `.cs`

It does not specify the SC-015 hook-invocation log assertion:

> Post-edit format hook does not spawn `dotnet format` on a non-`.cs` Edit/Write.

Fix by adding that assertion to T064, or add a new PR1 test task. The matrix should then point at the actual task.

## Verified as corrected

- T031/T032 merged; T050/T051 disjoint; T069 excludes `learn.md`; T089 no longer `[P]`.
- T047 is PR3 FR-012-only; MCP-first assertions moved to T063.
- T022 uses trigger-sentence checks instead of character counts.
- T064 moved to PR1 with T018a/T018b implementation coverage.
- FR-017 split: T023a strips `alwaysApply`; T052b checks profile `paths:`.
- T058 deterministic test added as `tests/test_arch_narrative_dedup.py`.
- T087 rewritten as `scripts/violation_harness.py`.
- T091 is no longer in Polish and is in PR5, but needs relocation into the PR5 test section.
- SC-014 has both mocked unit coverage (T062) and Windows smoke coverage (T066b).
