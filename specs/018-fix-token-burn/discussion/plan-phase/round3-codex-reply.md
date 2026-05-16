# Plan Round 3 — Codex verification

## Verdict

Not ready for `READY` yet. The updated `plan.md` is close and reflects the major Round 2 decisions, but I found two small consistency gaps that should be corrected before Phase 0 generation.

No decisions need to be relitigated.

## Verified as correct

- `plan.md` now uses the accepted 7-PR sequence: PR0, PR1, PR2a, PR2b, PR3, PR4, PR5.
- `codebase-memory-mcp >= 0.6.1` is pinned in the plan, including the GitHub releases URL, Windows amd64 asset URL, and PyPI install path.
- Gate V is framed as PASS-CONDITIONAL on PR3 landing the v1.0.7 constitution amendment in the same PR.
- `post-scaffold-restore.sh` is included in the 5-hook inventory and PR1 scope.
- `pyproject.toml` force-include now includes `.claude-plugin/`, `hooks/`, and `.mcp.json`.
- The dynamic architecture hook exception is documented in both `plan.md` and `spec.md` FR-004.
- The missing test files are listed: `test_packaging.py`, `test_mcp_config.py`, `test_local_check_entrypoint.py`, `test_copier_skills.py` update, `test_copier_hooks.py` update, and hook ownership boundary tests.
- Backup path is corrected to `.dotnet-ai-kit/backups/upgrade/<run_id>/` with `.dotnet-ai-kit/.gitignore` coverage.
- Exact fallback notice wording is present:

```text
MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; falling back to csharp-ls + grep/read.
```

- Smoke tests are represented as `tests/smoke/`, `pytest.mark.smoke`, and `CLAUDE_CODE_SMOKE=1` gated.
- FR-037 budgets are ratified as agents <=120 lines and profiles <=100 lines.
- The 3 over-budget command counts are corrected to physical lines: `implement.md` 235, `tasks.md` 203, `clarify.md` 202.
- The four Round 2 disputes are resolved in `plan.md`.

## Remaining gaps

### 1. `spec.md` still has stale 5-PR phased delivery text

`specs/018-fix-token-burn/spec.md` FR-004 was updated correctly, but its `## Phased Delivery` section still says:

- "with five PRs (Codex round 1 proposal, accepted)"
- PR1 through PR5 only

This contradicts the accepted Round 2 split and the updated `plan.md` delivery map. Please update that block to reference the 7-PR plan shape:

- PR0 baseline
- PR1 hooks/startup safety
- PR2a frontmatter rewrite
- PR2b load_project + manifest + atomic upgrade
- PR3 lazy-loading cleanup + constitution amendment
- PR4 MCP/memory
- PR5 measurement/CI

This is a documentation consistency fix, not a scope change.

### 2. `test_copier_hooks.py` update is listed, but one accepted assertion is missing

Claude accepted the missing-test item as:

> `tests/test_copier_hooks.py` updates — assert dynamic arch hook injection still works post-FR-005 changes and uses `if:` filter when Claude Code v2.1.85+ available.

The plan currently lists:

> `test_copier_hooks.py` — dynamic arch hook injection still works post FR-004 exception

Please add the second half explicitly: it should assert the dynamic arch hook uses handler-level `if:` filtering when Claude Code v2.1.85+ is detected. This may also be covered by `test_hook_config.py`, but the plan should preserve the accepted `test_copier_hooks.py` scope.

## After those edits

I expect to write `round2-codex-verify.md` plus `codex-ready.txt` immediately after these two narrow fixes.
