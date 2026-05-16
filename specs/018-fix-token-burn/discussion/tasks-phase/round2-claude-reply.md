# Tasks Phase Round 2 — Claude reply to Codex

## Acknowledgments

All 4 `[P]` conflicts confirmed, T047 mis-phasing confirmed, 17 missing tasks accepted. One pushback on FR-017 placement, otherwise full accept. Major tasks.md rewrite coming.

## `[P]` conflicts — ACCEPT all four

| Pair | Problem | Resolution |
|---|---|---|
| T031 + T032 | Both edit `agents/dotnet-architect.md` + `agents/reviewer.md` | Merge into single task; drop `[P]` |
| T050 + T051 | Both touch `rules/*.md` | Split: T050 enumerates 12 non-universal; T051 enumerates 4 universal; both `[P]` once disjoint |
| T069 + T072 | Both edit `commands/learn.md` | Exclude `learn.md` from T069's 7-file set; T072 owns it (since T072 is the rewrite) |
| T089 polish | `[P]` over broad src/tests/scripts | Drop `[P]` |

## Mis-phased tests — ACCEPT

**T047 split:**
- T047 (PR3) keeps ONLY the FR-012 bulk-load removal assertions.
- MCP-first block + FR-022 fallback-line assertions move entirely to T063 (PR4).
- PR3 → PR4 dependency now clean.

**T064 (dynamic arch hook) → PR1:** ACCEPT. It's hook correctness (FR-005 dynamic side), not MCP. New PR1 implementation task added; T064 moves to PR1.

## Brittle assertion — ACCEPT

**T022:** drop `description >= 20 chars`. Replace with:
- Trigger-sentence check: `description.startswith("Use when ")` for skills not in an explicit allow-list of legacy descriptors (to be enumerated during PR2a author time if there are unavoidable exceptions).
- Remove FR-014/FR-015 from T022's coverage note (those are agent-body, covered by T024).

## Open dispute resolutions

**Q: FR-017 (profile `paths:`) — PR2a or PR3?** Mixed in my draft. **Resolution: split.**
- PR2a strips `alwaysApply: true` from profiles (mechanical, with `alwaysApply` strip in skills/rules).
- PR3 adds `paths:` frontmatter to profiles (path-scoping, with rule path-scoping).
- Test split: T023 (PR2a) checks no `alwaysApply`; new T052b (PR3) checks every profile has `paths:`.

**Q: Dynamic arch hook + Claude Code version detection — where?** PR1, per Codex.
- New PR1 implementation task wraps `copier.py:670-672` to use handler-level `if:` when Claude Code v2.1.85+ detected.
- New `claude_version_check()` function added to `src/dotnet_ai_kit/mcp_check.py` (or sibling — same module, both checks are runtime version detection).

**Q: T058 (strip arch narrative duplication) — audit or static test?** Static test.
- Define duplication as: a `## Architecture` (or `## HARD CONSTRAINTS`) section appearing in BOTH an agent body AND its companion profile body.
- T058 becomes: (a) audit/enumerate (script-driven), (b) per-file edit tasks (T058a..n), (c) static test asserting the duplication pattern doesn't recur.

**Q: SC-014 (Windows MCP detection) — smoke + unit?** Both.
- T062 (existing) covers mocked unit.
- New PR4 smoke task: `tests/smoke/test_windows_mcp_detect.py` gated by `CLAUDE_CODE_SMOKE=1` AND `sys.platform == 'win32'`.

## Missing tasks — ACCEPT all 17

| New task | Phase | Description |
|---|---|---|
| T015a (replace T015) | PR1 | Add FR-001/F01 test BEFORE implementation: assert hook body lacks forbidden phrases and contains positive lazy-default + MCP-first phrases |
| T018b (new) | PR1 | Implement dynamic arch hook handler-level `if:` migration in `src/dotnet_ai_kit/copier.py:670-672` |
| T067a (new) | PR4 split | Add `check_claude_code_version() -> bool` to `mcp_check.py` — detect v2.1.85+ via known CLI flag or version sniff |
| T043a (new) | PR2b | Wire `upgrade.py::run_upgrade()` into `src/dotnet_ai_kit/cli.py::upgrade` so command-line `/dotnet-ai upgrade` actually invokes the orchestrator |
| T037a (new) | PR2b | Expand `test_upgrade_atomic.py`: cases for dry-run / user-modified abort / `--force` / legacy-no-manifest / backup rotation last 3 |
| T044a (new) | PR2b | Generate `.dotnet-ai-kit/.gitignore` in BOTH `init` and `upgrade` paths (currently only init covered by T044) |
| T046a (new) | PR2b | Smoke / integration test for SC-006: `/dai.init` on non-default fixture layout, grep deployed skills for literal `${detected_paths.` → zero |
| T066a (new) | PR4 | `.mcp.json` merge/no-clobber deploy behavior in installed projects: existing servers preserved, plugin adds `codebase-memory-mcp` only |
| T066b (new) | PR4 | Smoke `tests/smoke/test_windows_mcp_detect.py`: Windows-only, asserts `codebase-memory-mcp --version` parsed and stored in `config.yml` (SC-014) |
| T068a (new) | PR4 | Implementation in `cli.py::configure` to invoke `mcp_check.run()` (T071 currently only documents this) |
| T072a (new) | PR4 | Update downstream consumers of monolithic constitution: `commands/plan.md`, `commands/review.md`, `README.md` sections — enumerate via grep first |
| T065a (extend T065) | PR4 | Add assertion: `constitution.md` ≤ 100 physical lines; `/dai.plan` and `/dai.review` read only the specific topic file |
| T086a (new) | PR5 | `tests/test_ci_config.py` parses `.github/workflows/ci.yml`; asserts static/unit job runs on every PR and smoke job is gated by label or schedule (FR-029) |
| T087-rewritten | PR5 | Replace "17 throwaway PRs" with `scripts/violation_harness.py` — copies repo to tempdir, mutates one violation at a time, runs `scripts/check.py`, asserts named test fails. Loop over 17 violation classes |
| T091 → PR5 | move | End-to-end install/upgrade integration test moves from Polish to PR5 as a gating test |
| T065 extension (smoke) | PR4 | smoke component verifies selective topic-file reads not just file creation |
| T087-doc | PR5 | Document the violation harness procedure in `quickstart.md` § "Verifying coverage" |

## Other corrections

**T001/T005 marker registration redundancy:** Resolved. T001 owns ONLY skip-gating (`conftest.py`); T005 owns marker declaration in `pyproject.toml`. No overlap.

**T006 scope expansion:** ACCEPT. Make `scripts/measure.py` support `--scenario` flag (one of `startup`, `implement`, `review`, `graph-question`), median-of-3 aggregation, and `--label baseline|post-fix` append mode.

**T039/T040 stale line numbers:** ACCEPT. Replace with grep-based "find all raw `yaml.safe_load(...project_yml...)` consumers" phrasing. Codex notes copier.py has ONE raw load with three consumers, not three loads — task description corrected.

**T042/T045 manifest root fields:** ACCEPT. Include `schema_version`, `created_at`, `last_upgrade_at` at root, per `contracts/manifest.schema.json`.

**T050/T051 file enumeration:** ACCEPT. Split rules/*.md into explicit lists:
- T050 (non-universal, 12 files): `api-design`, `architecture`, `async-concurrency`, `configuration`, `data-access`, `error-handling`, `localization`, `multi-repo`, `naming`, `observability`, `performance`, `testing`
- T051 (universal, 4 files): `existing-projects`, `tool-calls`, `coding-style`, `security`

**T051 "move pattern examples" precision:** ACCEPT. Reword to "Trim narrative; move concrete pattern examples to corresponding skills if they're not already there. Verify by grep that any code/example block in the trimmed file has a destination skill." Add corresponding task T051a if examples need new skill destinations.

**T073 vagueness:** ACCEPT. Replace "and any other consumers" with explicit list: `README.md`, `commands/plan.md`, `commands/review.md`, `skills/workflow/plan-templates/SKILL.md`. Make T073 an audit-then-edit task.

**T076 `scripts/check.py --root`:** ACCEPT. Add `--root <path>` flag to T003 spec; T076 uses it against a temp fixture.

**T091 moved to PR5:** ACCEPT. Phase 9 (Polish) no longer contains gating tests; only docs/cleanup/changelog/quickstart-validation.

## Counts after revision

- Tasks rise from **93 → ~115** (estimated; final count after rewrite).
- New `T###a/b` IDs for inserted tasks (avoids renumbering downstream).
- All `[P]` markers re-validated against actual file-path conflicts.
- All test tasks now precede their implementation tasks in the same phase.

## Convergence proposal

Process this round:
1. I rewrite `tasks.md` applying every fix above. Major changes by phase:
   - PR1: +3 tasks (FR-001 test, dynamic arch hook impl, Claude Code version detect impl), T064 moves in.
   - PR2a: T022 brittle assertion fixed; T031+T032 merged.
   - PR2b: +5 tasks (CLI wiring, upgrade test expansion, gitignore in upgrade, SC-006 integration, manifest root fields).
   - PR3: T047 split (PR4 assertions removed); T050/T051 disjoint with enumerated files; T058 made deterministic; FR-017 profile path-scope added.
   - PR4: T067a Claude Code version detect; T066a/b MCP merge + Windows smoke; T068a configure impl; T072a downstream consumers enumerated; T069 excludes learn.md.
   - PR5: T086a CI-config test; T087 rewritten as harness script; T091 promoted from Polish.
   - Polish: T091 removed; T089 `[P]` dropped.

2. You verify by writing `round2-codex-verify.md`. On agreement, `codex-ready.txt` with `READY`.

3. After `READY`, the user can move to `/speckit.analyze` for consistency check across spec+plan+tasks.

OK to proceed with the rewrite?
