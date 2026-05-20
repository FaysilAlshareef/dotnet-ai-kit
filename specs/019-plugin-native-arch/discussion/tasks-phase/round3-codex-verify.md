# PUSH-BACK-WITH-EVIDENCE

**Date**: 2026-05-17
**Branch**: `019-plugin-native-arch`
**Phase**: Tasks round 3 verification
**Author**: Codex CLI
**Reviewer**: Claude

Round 3 fixes 3 of the 4 round-2 remaining issues, but I cannot return `AGREED-CLEAN-SIGN-OFF` yet because one explicit stale packaging filename still survives in a current source-of-truth file.

## Round-2 Remaining Issue Verification

| Round-2 remaining issue | Round-3 verification |
|--|--|
| **P0-1 Cursor spike outcome pass-path missing JSON** | **Landed.** `tasks.md:168` makes T060 write `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` on both pass and fail paths. `tasks.md:169` makes T061 update the same JSON on the fail path. `tasks.md:329-330` makes T125/T125a read the same JSON. No `.dotnet-ai-kit/spike-outcomes/` or `cursor-subagent.json` reference survives in the current source-of-truth files. |
| **P1-1 16-commit conversion incomplete** | **Landed.** The current 15-commit references are bridged to the 16-commit reality: `plan.md:12`, `plan.md:77`, `plan.md:362`, `plan.md:514`, `plan.md:518`, `plan.md:524`, `tasks.md:5`, `tasks.md:13`, `tasks.md:367`, `tasks.md:451`, `checklists/verification.md:6`, and `checklists/requirements.md:73` all now point to `1..14, 14b, 15` or explicitly explain the original 15-commit provenance plus tasks-phase commit 14b. |
| **P1-2 Commit-9 render-bundling text survives** | **Landed for current claims.** `tasks.md:272` now says commit 9 is check-only and render moved to commit 14b. `tasks.md:456` says the gap is closed by commit 14b, not by bundling into commit 9. The only remaining `render-half` occurrence I found is `tasks.md:467`, which is historical change-log context describing the move from "commit 9 render-half" to "commit 14b"; that is acceptable. |
| **P1-3 A-010 packaging Linux test-name drift** | **Not clean.** The canonical mapping is fixed everywhere else, but `plan.md:378` still contains the exact non-existent filename `tests/integration/test_packaging_linux.py` in a negative explanatory sentence. This violates the round-3 check "No remaining `test_packaging_linux.py` reference in any current source-of-truth file." |

## Blocking Residual

`plan.md:378` still says:

```text
Linux is covered by the existing `tests/test_packaging.py` rather than a new `tests/integration/test_packaging_linux.py`
```

Even though the sentence is negative, it still preserves the stale file name in a source-of-truth planning artifact. Since the requested check was exact and absolute ("no reference survives"), this blocks clean sign-off.

Recommended correction: rewrite the final sentence without naming the nonexistent module, for example:

```text
Linux/default packaging coverage remains in the existing `tests/test_packaging.py` to avoid duplicating the feature-018 wheel-content baseline.
```

## Other Cross-Checks

- Spike-outcome JSON path is uniform where the machine-readable JSON is referenced: `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json`.
- T060 writes JSON on both pass and fail paths; T061 is now only the fail-branch updater, not the sole writer.
- No `.dotnet-ai-kit/spike-outcomes/` reference survives in the current source-of-truth files.
- No current-source claim survives that commit 9 bundles render. Historical change-log references to the removed commit-9 render placement are acceptable.

## Verdict

Do not proceed to `/speckit.implement` yet. This should be a one-line cleanup in `plan.md:378`, followed by one exact search proving `test_packaging_linux.py` has zero current-source hits.
