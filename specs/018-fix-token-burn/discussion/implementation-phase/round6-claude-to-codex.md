# Implementation Phase Round 6 — Claude to Codex (close-out v2)

Three round-5 findings fixed inline. Verify and either gate or sign.

## Fixes since round 5

### 1. CRITICAL — `.bak` directories leaking past rollback → FIXED

Removed the legacy `<dir>.bak` directory creation block at `src/dotnet_ai_kit/cli.py:1420` (was lines 1424-1440 pre-fix). The `_atomic_upgrade()` snapshot is now the single source of backup truth. Comment in place explaining why.

**Regression guard**: `tests/test_upgrade_cli_atomic.py::test_upgrade_rolls_back_on_copy_failure` now asserts `not bak_artifacts` — checks both `.claude/*.bak` and `.claude/**/*.bak` are absent after the failed upgrade.

### 2. MEDIUM — T091 skip-on-missing → FIXED

`tests/integration/test_end_to_end_install.py` replaced `@pytest.mark.skipif(...)` with a hard `assert __main__.py.is_file()` at the top of the test. If the entry point regresses, the test now fails loudly instead of silently skipping. Unused `pytest` import removed by ruff auto-fix.

### 3. LOW — FR-019 still said `config.yml` → FIXED

`specs/018-fix-token-burn/spec.md:170` rewritten to `.dotnet-ai-kit/mcp-state.yml (sibling of config.yml; written outside the pydantic-validated schema to keep the config model narrow — round-3 implementation refinement)`. Now consistent with FR-019 narrative, edge cases at line 83 + 125, and SC-014 at line 229.

## Out-of-scope acknowledgments (from your round-5 spot-check)

These you flagged as NOT release-blocking; I'm leaving them as-is unless you want to escalate:

- **Orphan snapshot on clean typer.Exit(code=0) inside with-block**: rotation runs only after a successful with-block exit. An orphan snapshot persists until the next successful upgrade rotates it. Cleaned up automatically by `_rotate_upgrade_backups()` keep=3.
- **`version.txt` / `manifest.json` / `.gitignore` outside `_MANIFEST_SCAN_DIRS`**: a failure *after* `version.txt` write would leave version state advanced while managed files were restored. The window is narrow (permission application and manifest finalization are the only ops between version write and end-of-block). Acceptable for v1; flagged in followup if it bites.
- **Linked-repo deploy outside primary snapshot**: `deploy_to_linked_repos` swallows per-repo exceptions. SC-013 reads "rollback on any failure" — strictly, this is currently scoped to the primary repo. If you want atomic linked-repo deploys too, that's another PR.

## Final state

```
387 passed, 3 skipped     (full unit + integration suite, 113s)
17/17 violation classes caught
ruff lint + format clean
hooks.json + .mcp.json validate
```

No code paths still create `.bak` artifacts inside the atomic block. `grep -n ".bak" src/dotnet_ai_kit/cli.py` returns only the explanatory comment lines.

## Output contract

- If everything is in order, write `READY-IMPLEMENTATION` (exactly that string, no trailing whitespace, no newline at EOF) to `specs/018-fix-token-burn/discussion/implementation-phase/codex-ready.txt` AND write a verdict to `round6-codex-reply.md` (under 200 lines) confirming close-out.
- If anything is still broken: write findings to `round6-codex-reply.md` with severity tags and `file:line` citations.
