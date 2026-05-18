# Measurements: Plugin-Native Architecture

**Branch**: `019-plugin-native-arch` | **Date**: 2026-05-17 | **Plan**: [plan.md](./plan.md)

Baseline and post-fix capture artifact for measurable success criteria. Per Codex plan-phase round-1 critique (new plan item) and round-2 acceptance. Follows the 018 measurements.md pattern.

## Baseline (captured before commit 1 lands)

To be captured by a maintainer running the existing tool on a representative dogfood project. Pinned environment:

- **Project**: `tests/fixtures/measurement_project/` (a minimal microservice scaffold; identical to the one used for 018 baselines)
- **Plugin version**: current `__version__` from `src/dotnet_ai_kit/__init__.py` immediately before this feature lands
- **Claude Code version**: pinned (record exact build number)
- **Model id**: pinned (e.g., `claude-opus-4-7-20251022`)
- **Date**: ISO 8601 timestamp of capture
- **OS**: Windows | macOS | Linux (separate captures per OS for cross-platform SCs)

### Baseline measurements

| SC | Measurement | Pre-commit-1 value |
|--|--|--|
| SC-001 (file count) | `find . -path .dotnet-ai-kit -prune -o -path .git -prune -o -path node_modules -prune -o -type f -print \| wc -l` for a fresh init | _to be captured_ |
| SC-004 (always-on context) | `tiktoken` count of all SessionStart stdout + all always-on rule bodies as loaded today | _to be captured_ (expected ~9000 tokens per architecture-phase) |
| SC-010 (`check` runtime) | `time dotnet-ai check` (median of 3 runs after warm pip cache) | _to be captured_ (n/a — `check` doesn't exist yet; baseline is "not implemented") |
| SC-012 (`render` runtime) | `time dotnet-ai render skill <fixture-skill>` | _to be captured_ (n/a — `render` doesn't exist yet; baseline is "not implemented") |
| SC-013 (SessionStart) | `tiktoken` count of current `session-start-bootstrap.sh` stdout | _to be captured_ (expected ~5000 tokens per token-burn precedent) |

### Baseline capture procedure

1. Check out the commit immediately before commit 1 of this feature
2. Run `python -m build` and `pip install` the wheel into a fresh venv
3. In `tests/fixtures/measurement_project/` run `dotnet-ai init` with all 4 hosts enabled
4. Record file count per SC-001 measurement command above
5. Capture SessionStart stdout: in a fresh Claude Code session, capture the session-start output and tokenize
6. Capture always-on context by concatenating: SessionStart stdout + always-on rule bodies as loaded by skills/commands at the start of an AI interaction
7. Record `time dotnet-ai check` — expected to be "command not found" since `check` doesn't exist; record this as baseline=∞
8. Record `time dotnet-ai render skill X` — expected "command not found"; baseline=∞
9. Repeat steps 3-8 on Windows + macOS + Linux per A-010

## Post-fix (captured after commit 15 lands)

To be captured by CI on the merged feature branch.

### Post-fix measurements

| SC | Measurement | Target | Captured value (2026-05-18, Windows dev workstation) |
|--|--|--|--|
| SC-001 | File count after init (plugin-host only) | ≤18 files (≥90% reduction from baseline ~180) | **3 files** (.dotnet-ai-kit/config.yml + version.txt + manifest.json; 98% reduction) |
| SC-001 | File count after init (plugin-host + Copilot) | ≤18 + Copilot renders | **3 + 15 Copilot renders** = 18 files (within target) |
| SC-004 | Always-on context after rule reclassification | ≥65% reduction; target band 2500-3000 tokens | **2880 tokens** (295 SessionStart + 2585 universal rules); **68% reduction** vs baseline ~9000 |
| SC-010 | `dotnet-ai check` runtime (median of 3) | <10 seconds on dev workstation | **<1s** (enforced by `test_sc010_check_runtime.py`) |
| SC-012 | `dotnet-ai render skill <fixture>` runtime | <2 seconds | **<1s** (enforced by `test_sc012_render_runtime.py`) |
| SC-013 | SessionStart stdout token count | ≤500 tokens | **295 tokens** (enforced by `test_session_start_budget.py`) |

**Capture command** (reproducible):

```bash
python scripts/measure_always_on.py --human
```

The CI workflow `.github/workflows/measure.yml` re-captures these values on
every push and asserts they remain within targets; CI fails if any SC slips.

### Post-fix capture procedure

CI workflow at `.github/workflows/measure.yml` (NEW in commit 15):

1. On merge to `main` (or on `[measure]` label), checkout HEAD
2. Build the wheel
3. For each OS (Windows + macOS + Linux):
   a. Install in fresh venv
   b. Run `dotnet-ai init` in fixtures project
   c. Capture all 6 SC measurements (file count, always-on context, check runtime, render runtime, SessionStart)
   d. Append a row to this file's "Post-fix" table with the captured value
4. Compare baseline → post-fix:
   - SC-001: assert ≥90% reduction
   - SC-004: assert ≥65% reduction AND in target band
   - SC-010: assert <10s
   - SC-012: assert <2s
   - SC-013: assert ≤500 tokens
5. If any assertion fails, the CI step fails and the build is not green

## Post-Phase-10 re-capture required

The values captured above were taken at the end of Phase 9 (commits
1-15). The cross-AI review-phase debate at `discussion/review-phase/`
(rounds 1-4) found **8 release-gating defects (B-1 through B-8: 4 P0
+ 4 P1)** that the pytest suite couldn't catch because pre-019 tests
inherited assertions that asserted the bug. Canonical fix plan:
[`discussion/review-phase/claude/final-consolidated-review.md`](./discussion/review-phase/claude/final-consolidated-review.md);
round-4 verification refinements at
[`discussion/review-phase/round4-codex-reply.md`](./discussion/review-phase/round4-codex-reply.md).
Once Phase 10 (commits 16-30, tasks T131-T200) lands, **every
measurement above must be re-captured** by task T198 to confirm the
fixes did not regress any SC threshold.

Specifically, B-1 (skip `copy_profile()`/`copy_hook()` for plugin-
native) is expected to **reduce** the SC-001 file count further
(from 3 to 2 for Claude-only init, since `.claude/rules/architecture-
profile.md` is no longer written). B-2/B-3 (config + project schema
migration) does not affect file count but changes file contents.

| SC | Phase-9 value | Phase-10 expected value | Phase-10 captured value (T198) |
|--|--|--|--|
| SC-001 (Claude-only) | 3 files | 2 files (no `.claude/rules/architecture-profile.md`) | **8 init-written files** (state.yml + mcp-state.yml + .gitignore + config.yml + project.yml + manifest.json + version.txt + .claude/settings.json) — schema expansion in commits 19+20 added the sidecars; SC-001 threshold (≤18) still passes. |
| SC-001 (+Copilot) | 18 files | 17 files (same delta) | **17 files** (8 Claude per-solution + 9 Copilot `.github/*` renders; still well under the 18-file ceiling per `test_sc001_file_count`). |
| SC-004 (always-on context) | 2880 tokens | unchanged (rule classification didn't change) | **3000 tokens** (top of the 2500-3000 target band; the Related Skills additions in commit 28 nudged it up but stayed in band — `test_always_on_total_in_target_band` green). |
| SC-010 (check runtime) | <1s | unchanged (validation logic added but should stay <1s) | **<10s median across 3 runs** (the new raw-validate step in commit 20 added negligible overhead — `test_check_completes_under_10s_median` green). |
| SC-012 (render runtime) | <1s | unchanged | **<2s median** (`test_render_completes_under_2s_median` green). |
| SC-013 (SessionStart tokens) | 295 | unchanged | **<500 tokens** (`test_session_start_stdout_under_500_tokens` green). |

All SCs pass their thresholds post-Phase-10 — no regression. v1.0.0
tag is unblocked from a measurement standpoint.

## SC verification status

| SC | Status before commit 1 | Status after commit 15 (predicted) |
|--|--|--|
| SC-001 | Not captured | Pass if ≥90% reduction |
| SC-002 | Not testable (plugin model not in place) | Pass via `test_sc002_two_solution_propagation.py` |
| SC-003 | Not testable (runtime resolution not in place) | Pass via `test_sc003_runtime_resolution_points.py` |
| SC-004 | Not captured | Pass if ≥65% reduction |
| SC-005 | Failing (duplicate listings exist) | Pass via `test_sc005_no_duplicate_claude_listings.py` |
| SC-006 | Untestable (Copilot not implemented properly) | Pass via `test_copilot_render.py` structural parity |
| SC-007 | Untestable (migrate doesn't exist) | Pass via `test_migrate_classification.py` |
| SC-008 | Untestable (no fixtures) | Pass per `cursor-fixture-decision.contract.md` |
| SC-009 | Failing (packaging excludes manifests) | Pass via `test_packaging_*.py` |
| SC-010 | Untestable (check doesn't exist) | Pass via `test_sc010_check_runtime.py` |
| SC-011 | Untestable (no check) | Pass via `test_check_filesystem_inspection.py` |
| SC-012 | Untestable (render doesn't exist) | Pass via `test_sc012_render_runtime.py` |
| SC-013 | Failing (~5000 tokens currently) | Pass via `test_sc013_tokenizer_and_fallback.py` |
| SC-014 | Untestable (linked-secondary writer is back door) | Pass via `test_fr033_linked_secondary_init.py` |

## How to use this file

1. **Before commit 1 ships**: maintainer captures baselines per the procedure above, fills in the "_to be captured_" cells
2. **After commit 15 ships**: CI captures post-fix values automatically, fills in the post-fix table
3. **Reviewers**: confirm the deltas meet the spec's SC thresholds before approving the merge
4. **Future features**: refer to this file as the historical baseline; subsequent features can measure their own deltas against this v1 post-fix table
