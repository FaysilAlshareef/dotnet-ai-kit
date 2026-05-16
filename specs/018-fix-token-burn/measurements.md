# Measurements — Feature 018 Fix Token Burn

**Captured by**: `scripts/measure.py` (median of 3 runs per scenario)
**Format**: `- **<label>** | tokens=<n> | claude=<ver> | sha=<git> | python=<x.y> | at=<iso>`
**Status**: Baselines and post-fix rows below are placeholders. They are
populated by a maintainer with a live Claude Code v2.1.85+ session (the
`scripts/measure.py` script refuses to run without `CLAUDE_CODE_SMOKE=1`).

> ⚠️ **DEFERRED**: Real values cannot be captured from an automated PR run.
> Each `tokens=DEFERRED` row is replaced by the maintainer who executes the
> measurement protocol described in `quickstart.md` § 6.

## Baseline → Session startup (SC-001)

- **baseline** | tokens=DEFERRED | claude=DEFERRED | sha=DEFERRED | python=DEFERRED | at=DEFERRED

## Baseline → Implementation (SC-002)

- **baseline** | tokens=DEFERRED | claude=DEFERRED | sha=DEFERRED | python=DEFERRED | at=DEFERRED

## Baseline → Review (SC-003)

- **baseline** | tokens=DEFERRED | claude=DEFERRED | sha=DEFERRED | python=DEFERRED | at=DEFERRED

## Baseline → Graph question (SC-007)

- **baseline** | tokens=DEFERRED | claude=DEFERRED | sha=DEFERRED | python=DEFERRED | at=DEFERRED

## Post-fix → Session startup (SC-001)

- **post-fix** | tokens=DEFERRED | claude=DEFERRED | sha=DEFERRED | python=DEFERRED | at=DEFERRED

## Post-fix → Implementation (SC-002)

- **post-fix** | tokens=DEFERRED | claude=DEFERRED | sha=DEFERRED | python=DEFERRED | at=DEFERRED

## Post-fix → Review (SC-003)

- **post-fix** | tokens=DEFERRED | claude=DEFERRED | sha=DEFERRED | python=DEFERRED | at=DEFERRED

## Post-fix → Graph question (SC-007)

- **post-fix** | tokens=DEFERRED | claude=DEFERRED | sha=DEFERRED | python=DEFERRED | at=DEFERRED

Answer-quality parity note (SC-007): the post-fix graph-question scenario MUST produce the same correct answer as the baseline run. The measurement excludes one-time MCP indexing tokens since indexing is amortised across all future queries.

## Verdict (T084)

| SC | Baseline | Post-fix | Δ% | Target (soft) |
|---|---:|---:|---:|---|
| SC-001 session startup | DEFERRED | DEFERRED | DEFERRED | ≥ 40% reduction |
| SC-002 implementation | DEFERRED | DEFERRED | DEFERRED | ≥ 30% reduction |
| SC-003 review | DEFERRED | DEFERRED | DEFERRED | ≥ 30% reduction |
| SC-007 graph question | DEFERRED | DEFERRED | DEFERRED | ≥ 30% reduction (answer-quality parity required) |

Hard release gates (SC-004, SC-005, SC-006, SC-013, SC-014, SC-015, SC-016) are binary and verified by the static + unit test suite, not by this table. Token-reduction targets above are measured-target soft warnings — release does not block on them.

## MCP Version Verification

- **2026-05-16** — `codebase-memory-mcp >= 0.6.1` re-verified per research.md R1
  protocol against PyPI (`pip index versions codebase-memory-mcp`) and the
  upstream GitHub releases page. v0.6.1 confirmed as the current minimum that
  exposes the project-graph query surface used by FR-019/FR-021.
