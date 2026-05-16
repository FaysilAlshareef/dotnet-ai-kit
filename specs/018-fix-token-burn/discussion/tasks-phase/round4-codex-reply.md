# Round 4 Codex Verification

Status: NOT READY

Verified `specs/018-fix-token-burn/tasks.md` for the three round 3 mechanical fixes.

## Findings

1. T037/T037a merge is still incomplete.
   - `T037a` is no longer present as a task row, but stale references remain:
     - SC coverage table: `SC-013 | T037 + T037a + T043 + T046`
     - Task summary: `PR2b | 14 (added T037a, T043a, T044a, T046a)`
   - T037 now lists cases `(a)` through `(g)`, but the task text still says `covering 6 cases total`.
   - Expected: remove `T037a` from summary references and update T037 to `covering 7 cases total`.

2. T091 move is closed.
   - T091 is now in `### Tests for PR5 (write first)`.
   - It is marked `[P]` and described as a gating PR5 integration test.

3. SC-015/T064 coverage is closed.
   - T064 now includes case `(c)` for a fixture invocation log showing a non-`.cs` Edit/Write event.
   - The assertion explicitly checks that `post-edit-format.sh` or its `dotnet format` subprocess was not spawned.

## Required Follow-up

Fix the remaining T037/T037a summary drift in `tasks.md`, then rerun close-out verification.
