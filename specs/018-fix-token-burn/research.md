# Phase 0 Research — Fix Token Burn

**Feature**: `018-fix-token-burn` | **Date**: 2026-05-16
**Source plan**: [plan.md](./plan.md)
**Status**: All NEEDS CLARIFICATION items resolved.

Web research consolidated from `discussion/plan-phase/round1-codex-reply.md` (Codex performed live fetches against PyPI, GitHub releases, and Claude Code docs on 2026-05-16). Each entry follows the speckit.plan format: Decision / Rationale / Alternatives.

---

## R1 — `codebase-memory-mcp` minimum-version pin (FR-018, FR-035)

**Decision**: Pin `codebase-memory-mcp >= 0.6.1`.

**Rationale**:
- GitHub `DeusData/codebase-memory-mcp` latest release tag is `v0.6.1`.
- PyPI `codebase-memory-mcp` current version is `0.6.1`.
- Windows amd64 binary is published as a release asset (`codebase-memory-mcp-windows-amd64.zip`).
- Verified live 2026-05-16. PR4 author MUST re-verify before opening PR4 and update the pin if a security release has shipped — re-verification date stored in `specs/018-fix-token-burn/measurements.md` under `## MCP Version Verification`.

**Alternatives considered**:
- Exact pin (`== 0.6.1`) — rejected. Blocks legitimate upgrades; forces plugin-side bumps on every MCP patch.
- Range pin (`>= 0.6.1, < 1.0`) — rejected for now. Without published semver guarantees from `DeusData/codebase-memory-mcp`, the safer floor is `>=` and let runtime check fail loudly on incompatibilities.
- No pin — rejected (clarify Q2 user choice).

**URLs**:
- `https://github.com/DeusData/codebase-memory-mcp/releases` — release tag `v0.6.1`
- `https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.6.1/codebase-memory-mcp-windows-amd64.zip` — Windows binary
- `https://pypi.org/project/codebase-memory-mcp/` — PyPI 0.6.1

---

## R2 — Claude Code minimum version for handler `if:` filter (FR-005)

**Decision**: Document min Claude Code version as **v2.1.85+** in README and detect at runtime in `src/dotnet_ai_kit/mcp_check.py` (or sibling). `.claude-plugin/plugin.json` does NOT carry a `minimumClaudeCodeVersion` field.

**Rationale**:
- Per `https://code.claude.com/docs/en/hooks-guide`: "The `if` field requires Claude Code v2.1.85 or later."
- Per `https://code.claude.com/docs/en/plugins-reference`: the complete plugin schema lists `name`, `version`, component paths, `dependencies` — no `minimumClaudeCodeVersion` field found.
- Runtime detection allows graceful degradation: when running on older Claude Code, the plugin can deploy hooks with command-pattern matchers and accept the over-firing as a documented downgrade rather than failing install.

**Alternatives considered**:
- Hard pin via plugin manifest — rejected: schema doesn't support it.
- Block install on older Claude Code — rejected: too aggressive when degraded behaviour is acceptable.

**URLs**:
- `https://code.claude.com/docs/en/hooks-guide` — `if:` field min version
- `https://code.claude.com/docs/en/plugins-reference` — plugin.json schema
- `https://code.claude.com/docs/en/hooks` — exit code 2 blocking semantics (reused in PR1)

---

## R3 — Over-budget command trim targets

**Decision**: Trimming deferred to PR3 author. Plan-phase notes:
- `commands/implement.md` (235 → ≤200, **−35 lines minimum**). Likely trim targets: routing/skill-load instructions (Step 2/2b/2c will be replaced by FR-008 + FR-021 changes anyway).
- `commands/tasks.md` (203 → ≤200, **−3 lines**). Almost there; trim Step examples.
- `commands/clarify.md` (202 → ≤200, **−2 lines**). Trim trailing examples or merge brief steps.

**Rationale**: After FR-008 (drop "Load all skills listed") and FR-021 (replace with MCP-first block), the implement.md skill-routing blocks naturally collapse. Estimating −15 to −30 lines from FR-008+FR-021 alone — likely brings implement.md under budget without aggressive content cuts.

**Alternatives considered**:
- Aggressive content cuts now — rejected: collapses likely happen mechanically.
- Raise the budget — rejected: would invalidate the FR-025 ≤200 constraint accepted by both reviewers.

---

## R4 — Agent and profile current sizes (FR-037 ratification)

**Decision**: FR-037 budgets **ratified** as **agents ≤ 120 physical lines, profiles ≤ 100 physical lines**.

**Rationale**: Codex measured current state:
- Largest agent: ~51 lines (well under 120)
- Largest profile: ~73 lines (under 100)
- Comfortable headroom for ratified budgets

**Alternatives considered**:
- Tighter (≤100 / ≤80) — rejected: too close to current largest; rejects natural growth.
- Looser (≤200 / ≤150) — rejected: wastes the discipline benefit.

---

## R5 — Baseline measurement (FR-030)

**Decision**: Captured in **PR0** (dedicated baseline-capture PR). Fixture under `tests/fixtures/measurement_project/`. Three reads per scenario, median wins. Scenarios:

1. **SC-001 baseline**: fresh `/cost` immediately after `claude` boot, no commands.
2. **SC-002 baseline**: `/dai.implement` on a 5-task fixture feature.
3. **SC-003 baseline**: `/dai.review` on the same feature.
4. **SC-007 baseline**: graph-shaped question ("who calls `AggregateBase.ApplyChange`").

Pinned attributes recorded with each measurement: Claude Code version, model id, plugin commit SHA, Python version.

**Rationale**: Separating baseline capture from any plugin behaviour change is the only way to guarantee no contamination. PR0 makes the baseline commit reviewable on its own.

**Alternatives considered**:
- Capture baseline inline at PR1 — rejected (Codex round 1): risk of accidental "post-first-fix" baseline.

---

## R6 — Manifest field set (FR-032)

**Decision**: Manifest entries carry exactly these fields:

```
DeployedFile:
  path:             string (relative to project root)
  sha256:           string (64 hex chars)
  plugin_version:   string (matches dotnet_ai_kit.__version__)
  deployed_at:      ISO-8601 datetime
  source_template:  string | null  (path within plugin repo, e.g. "skills/api/controllers/SKILL.md")
```

Plus manifest-level:

```
Manifest:
  plugin_version:    string  (version when manifest was last touched)
  created_at:        ISO-8601 datetime
  last_upgrade_at:   ISO-8601 datetime | null
  files:             list[DeployedFile]
```

**Rationale**:
- `path` + `sha256` are the rollback minimum.
- `plugin_version` per file allows future detection of "this file was deployed by an old plugin version" without scanning git history.
- `deployed_at` aids debugging.
- `source_template` traces a deployed file back to its plugin-repo template — critical when a future refactor renames source paths and we need to migrate manifests.
- No "managed-by-version range" — single plugin version per deployed file (rotation handled by retaining last 3 backup runs).

**Alternatives considered**:
- Add `content_hash_pre_substitution` — rejected: redundant with `source_template` for traceability.
- Drop `source_template` — rejected: makes migration scripts harder to write.

---

## Re-verification protocol

Before opening PR4, the author MUST:
1. Fetch `https://pypi.org/project/codebase-memory-mcp/` and confirm `>= 0.6.1` is still the minimum supported.
2. Fetch `https://github.com/DeusData/codebase-memory-mcp/releases` and confirm `v0.6.1` is still present (not yanked).
3. If a security release is current, bump the plugin-side `MIN_CODEBASE_MEMORY_MCP_VERSION` and update `research.md` + `plan.md`.
4. Record the re-verification date in `measurements.md`.

---

## Out-of-band findings (informational)

Captured during research, not part of any FR but worth noting:

- `.mcp.json` schema does not natively support minimum-version constraints. Plan-phase decision: sidecar metadata key `dotnet_ai_kit_min_version` in `.mcp.json` (documentation only; not enforced by Claude Code) + runtime check in `mcp_check.py`.
- `codebase-memory-mcp` upstream installer may inject its own Claude Code hooks/instructions. Plan-phase decision: dotnet-ai-kit's `/dai.init` MUST invoke `codebase-memory-mcp` install via a flag that suppresses any auto-config (research action: confirm `--skip-config` or equivalent exists; if not, document the override).
- Largest current skill: `skills/architecture/multi-tenancy/SKILL.md` at 330 lines. Well under 400-line budget.

---

## Sign-off

- Codex (gpt-5.5 xhigh) — research URLs gathered and validated in round 1 reply
- Claude (Opus 4.7, 1M context) — consolidated into this document

No outstanding NEEDS CLARIFICATION markers. Ready for Phase 1.
