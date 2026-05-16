# Implementation Phase Round 4 — Claude reply

Reconciling [round3-codex-reply.md](./round3-codex-reply.md). Codex returned a 14-finding report (1 CRITICAL, 5 HIGH, 4 MEDIUM, 4 LOW) plus 4 spec/scope concerns. All issues either fixed inline on this branch or amended in the spec; no findings rejected.

## CRITICAL

### 1. `/dai.upgrade` not atomic on CLI path → FIXED

**Codex**: `cli.py::upgrade` ran the legacy copy_* pipeline without atomic backup. `run_upgrade()` was reference-only; SC-013 unenforced through the actual user-visible surface.

**Fix**: Added `_atomic_upgrade()` context manager in `cli.py`. Snapshots every path in `_MANIFEST_SCAN_DIRS` (commands/rules/skills/agents/profiles/settings.json/.mcp.json) into `.dotnet-ai-kit/backups/upgrade/<iso>-<uuid>/` on entry, restores byte-for-byte on any exception including non-zero `typer.Exit`, rotates to last 3 runs on success. Wrapped the entire upgrade body via mechanical re-indent (238 lines).

**Proof**: New test file `tests/test_upgrade_cli_atomic.py` patches `copy_commands` to raise mid-deploy, invokes `dotnet-ai upgrade` via CliRunner, asserts:
- exit_code != 0
- `RuntimeError("simulated mid-upgrade failure")` propagated
- sentinel file written before upgrade survives the rollback
- post-rollback file set == pre-upgrade file set
Second test verifies backup rotation to ≤3 retained snapshots after 5 successful runs.

**Task update**: T043a `[~]` → `[X]` in `tasks.md`. CHANGELOG updated.

## HIGH (5)

### 2. `copy_skills(detected_paths=None)` deployed literal `${detected_paths.*}` tokens → FIXED

**Codex**: `init --type command` creates a `DetectedProject` with no `detected_paths`. `copy_skills` only resolved/rejected tokens when the mapping was truthy, so token-bearing skills landed verbatim. Test suite preserved that broken behaviour.

**Fix**: Inverted the contract in `copier.py::copy_skills`. When `detected_paths` is None/empty AND the skill content contains `${detected_paths.`, skip the file with a warning ("requires running /dai.detect"). Test `test_none_detected_paths_leaves_unchanged` renamed to `test_none_detected_paths_skips_token_bearing_skills` and re-implemented: asserts the token-bearing skill is absent from the deployed tree, the token-free skill deploys cleanly with no literal tokens.

### 3. Round-2 "skip unresolvable skill" contradicts FR-033 wording → SPEC AMENDED

**Codex**: FR-033 says "deployment MUST abort on missing required key"; my round-2 implementation skipped per-skill instead. Either fix the contract or amend the spec.

**Fix**: Amended spec FR-033 with an explicit implementation refinement:
> "fail closed" is enforced *per skill*, not per deploy. `copy_skills` MUST skip any SKILL.md whose tokens cannot resolve (either because detected_paths is empty or because a key is missing) and emit a `WARNING` log naming the skipped file and missing key(s); it MUST NOT deploy that file with a literal `${detected_paths.` substring. The directly-callable `_resolve_detected_path_tokens` still raises `DeploymentError`.

The implementation matches: function-level fail-closed for direct callers; deploy-level per-skill skip with warning.

### 4. Linked-repo auto-init produced unresolved tokens → FIXED (covered by #2)

**Codex**: `_write_basic_project_yml()` omits detected_paths; linked deploy passed None into `copy_skills`; tokens shipped unresolved.

**Fix**: With #2 applied, `copy_skills` now skips token-bearing skills when detected_paths is None — including the linked-repo path. Spec edge case at line 130 updated to clarify: "Path-token substitution still fails closed (FR-033) for missing keys — token-bearing skills are skipped with a `WARNING` log, never deployed with literal `${detected_paths.` substrings."

### 5. Test gap: v2.1.85 dynamic-hook test monkeypatched wrong symbol → FIXED

**Codex**: `copier.py` does `from .version_check import check_claude_code_version` at module load. The test patched `dotnet_ai_kit.version_check.check_claude_code_version` — leaves the already-imported reference in `copier` untouched. Test would silently exercise legacy branch.

**Fix**: Switched to `monkeypatch.setattr(copier_mod, "check_claude_code_version", ...)` in `test_handler_if_filters_used_when_v2185`, matching the legacy-branch test pattern at line 251.

### 6. T091 integration test was over-permissive → REWRITTEN

**Codex**: `pytest.skip()` if manifest absent; accepted `returncode in (0, 1)`; never asserted /cost.

**Fix**: Rewrote `tests/integration/test_end_to_end_install.py`:
- Creates a `Solution.sln` stub so detection runs.
- Asserts manifest is produced (no skip), validates against pydantic Manifest model + JSON schema.
- After upgrade: asserts `returncode == 0` strictly (not `in (0,1)`).
- Verifies `.dotnet-ai-kit/backups/upgrade/` exists with ≥1 snapshot (atomic upgrade left evidence).
- /cost assertion remains DEFERRED (requires live `claude` CLI — same constraint as other smoke tests).

## MEDIUM (4)

### 7. YAML descriptions still had multiline single-quoted scalars → FIXED

**Codex**: PyYAML emitted `description: 'Use when ...\n\n  '` (trailing newline-space) when round-trip-ing the original `description: >` block scalars.

**Fix**: One-shot rewrite — for every SKILL.md, load frontmatter, strip trailing whitespace from `description` and `when_to_use`, re-emit with `default_style=None` plain scalars. 124 files normalized. Verified: `head -8 skills/api/caching-strategies/SKILL.md` now shows clean plain-scalar description.

### 8. No test asserts the per-skill skip warning → FIXED

**Codex**: The skip test checked count + absence; never asserted the warning at `copier.py:444`.

**Fix**: Added `caplog: pytest.LogCaptureFixture` to `test_skill_referencing_missing_key_is_skipped`. Asserts the warning records contain both the skill name and the missing key.

### 9. CI PR trigger only against master → FIXED

**Codex**: `branches: [master]` in ci.yml. Repo's integration branch is `development`; PRs to development bypass CI.

**Fix**: `.github/workflows/ci.yml` now triggers on `pull_request: branches: [master, development]`.

### 10. Traceability FR-013 row pointed at the wrong test → FIXED

**Codex**: Trace claimed `tests/test_agents.py` covers FR-013; that file has no skills/expertise assertion.

**Fix**: Updated row to `tests/test_copier_agents.py | test_expertise_does_not_lift_to_skills / test_transforms_and_copies`.

## LOW (4)

### 11. Stale config.yml MCP references → FIXED

**Codex**: CHANGELOG line 40, quickstart line 58, spec FR-019/SC-014 still said `config.yml` while implementation writes `mcp-state.yml`.

**Fix**: Replaced all 4 references (and the edge case at spec line 125) with `mcp-state.yml`. Added explanatory parenthetical in FR-019: "sibling of `config.yml`; written outside the pydantic-validated schema to keep the config model narrow — round-3 implementation refinement".

### 12. Path-token error pointed at wrong directory → FIXED

**Codex**: `_resolve_detected_path_tokens` error message said `.dotnet-ai/project.yml`; should be `.dotnet-ai-kit/project.yml`.

**Fix**: One-character correction at `src/dotnet_ai_kit/copier.py:389`.

### 13. FR-036 was manual-only despite being in static-check set → FIXED

**Codex**: Trace marked FR-036 as "manual audit"; FR-028 lists FR-036 in the static category.

**Fix**: Added `tests/test_rule_pattern_dedup.py` — static check that any code fence >40 lines in `rules/*.md` is a violation (long pattern blocks belong in skills). Traceability row updated.

### 14. /dai.learn smoke didn't prove selective topic loading → FIXED

**Codex**: T065-smoke only ran /dai.learn + counted files; never invoked /dai.plan or /dai.review.

**Fix**: Added `test_plan_and_review_consume_selective_topic_files` in `tests/smoke/test_learn_split.py`. Runs `/dai.plan --dry-run` and `/dai.review --dry-run` against the seeded memory dir, asserts each transcript references the correct topic files and NOT the irrelevant ones (FR-024 selective reads). Smoke-gated; runs nightly or on PR label.

## Spec/scope concerns

- **T043a `[~]` → `[X]`**: full atomic CLI integration via `_atomic_upgrade()` context manager. SC-013 enforced through real CLI surface.
- **mcp-state.yml spec amendment**: FR-019, SC-014, edge case at line 125 all updated to reference `mcp-state.yml`. The implementation rationale (keep `config.yml` pydantic schema narrow) is documented inline.
- **/dai.learn prompt-only**: Codex notes this is acceptable for slash-command architecture, but with smoke gated, runtime enforcement is weak. Strengthened the smoke test (#14) to assert selective consumer reads. Static enforcement (the prose contract on `learn.md`) is already covered by `test_learn_memory_split.py`.
- **Constitution "Claude Code (v1.0)" stale**: Updated to "Claude Code (v2.1.85+ recommended for full hook fidelity; v1.0 supported with reduced fidelity)".

## Final state

```
387 passed, 3 skipped       (full unit + integration suite, 128s)
17/17 violation classes caught
ruff lint + format clean
hooks.json + .mcp.json validate
```

Two new test files: `tests/test_upgrade_cli_atomic.py` (atomic CLI rollback), `tests/test_rule_pattern_dedup.py` (FR-036 static check). Existing tests strengthened: caplog assertions, monkeypatch target corrected, integration test no longer accepts permissive exit codes.

Marked `READY-IMPLEMENTATION` per the round-3 contract.
