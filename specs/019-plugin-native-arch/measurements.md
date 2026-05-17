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

| SC | Measurement | Target | Captured value |
|--|--|--|--|
| SC-001 | File count after init (plugin-host only) | ≤18 files (≥90% reduction from baseline ~180) | _to be captured_ |
| SC-001 | File count after init (plugin-host + Copilot) | ≤18 + Copilot renders | _to be captured_ |
| SC-004 | Always-on context after rule reclassification | ≥65% reduction; target band 2500-3000 tokens | _to be captured_ |
| SC-010 | `dotnet-ai check` runtime (median of 3) | <10 seconds on dev workstation | _to be captured_ |
| SC-012 | `dotnet-ai render skill <fixture>` runtime | <2 seconds | _to be captured_ |
| SC-013 | SessionStart stdout token count | ≤500 tokens | _to be captured_ |

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
