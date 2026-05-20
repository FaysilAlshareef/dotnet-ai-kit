# Feature 019 — Plugin-Native Architecture Outcomes

**Branch**: `019-plugin-native-arch` | **Date**: 2026-05-18
**Spec**: [spec.md](../specs/019-plugin-native-arch/spec.md)
**Plan**: [plan.md](../specs/019-plugin-native-arch/plan.md)
**Release notes**: [release-notes-v1.0.md](../docs/release-notes-v1.0.md)
**Migration guide**: [migration-v1.md](../docs/migration-v1.md)

This planning record captures the deferred-decision rationale and outcomes
that don't live in the spec or implementation. It's the historical anchor
that future features can reference when reviewing architectural choices.

## OOS-003 — `bin/` launcher (deferred to v1.1)

**Decision**: defer a `bin/dotnet-ai-kit` POSIX launcher to v1.1.
**Rationale**: v1 ships exclusively through host plugin systems (Claude
`/plugin install`, Codex `plugin install`, Cursor plugin marketplace).
A standalone `bin/` launcher would duplicate the host-plugin install
surface without adding value for the v1 user persona (.NET dev who's
already using one of the 4 hosts). The launcher is staged for v1.1 when
plugin-less CI/CD integration patterns are first-class.

## OOS-004 — Native Codex agents (partially lifted in v1.0)

**Decision (May 2026 revision)**: per-project subagent rendering is now
in v1.0 scope; plugin-manifest-bundled subagents remain deferred to v1.1.

**What shipped (v1.0)**: `generate_codex_agent(source_path) -> str` emits
TOML content for `.codex/agents/<name>.toml`, written by
`CodexHost.write_per_solution_files()` during `dotnet-ai init --ai codex`.
Per `https://developers.openai.com/codex/subagents` (retrieved
2026-05-19), Codex loads subagents from `~/.codex/agents/` (user) or
`.codex/agents/` (project); we write at the project scope so subagents
ride with the solution. Required TOML keys: `name`, `description`,
`developer_instructions`. Optional keys lifted from
`host_overrides.codex.*`: `model`, `model_reasoning_effort`,
`sandbox_mode`, `mcp_servers` (sub-tables). Conflict policy: pre-existing
files preserved; user customizations win.

**What stays deferred (v1.1)**: bundling subagents via the plugin manifest
itself. The Codex docs at `developers.openai.com/codex/plugins/build`
(retrieved 2026-05-19) list complete top-level manifest fields as
`name`, `version`, `description`, `author`, `homepage`, `repository`,
`license`, `keywords`, `skills`, `mcpServers`, `apps`, `hooks`,
`interface` — no `agents` / `subagents` field. The schema's
`not.anyOf` clause forbids inventing one to prevent drift.

## OOS-006 — Multi-repository monitor (deferred)

**Decision**: defer the cross-repo coordination monitor.
**Rationale**: feature 019 ships single-repo + linked-secondary support
(FR-033) via `dotnet-ai migrate --include-linked`. A reactive monitor
that watches multiple repos and propagates plugin updates is a separate
"sibling-repo orchestration" feature, not part of plugin-native arch.

## Cursor sub-agent spike outcome (A-005)

**State**: `specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json` is the canonical source of truth.
**Default**: `outcome: "pending"` until CI flips it to `passed` or `failed`.
**Default-assume-pass** behavior: `.cursor-plugin/plugin.json` includes the `agents` field; release notes carry the PASS-branch statement. If CI flips to `failed`, T125 + T125a + the T061 fail-path script atomically rewire the spec/plan/schema/release-notes to the deferral language.

## Constitution amendment audit trail

**v1.0.7 → v1.0.8** landed in commit 14 via the PASS-CONDITIONAL gate:

1. T081 wrote the failing test (`test_constitution_amendment.py`)
2. T082 amended `.specify/memory/constitution.md` (added `async-concurrency` to universal whitelist; 4 → 5 universal rules)
3. T083 verified the test now passes
4. T084-T089 executed the rule-move (16 rules into `rules/conventions/` + `rules/domain/`)

## Measurement capture

**SC-001**: ≤18 files per solution post-init. Captured: **3 files for Claude-only**, **18 with Copilot renders** — 98% reduction from ~180 baseline.
**SC-004**: ≥65% always-on context reduction, target band 2500-3000 tokens. Captured: **2880 tokens (68% reduction)** via `scripts/measure_always_on.py`.
**SC-010**: `dotnet-ai check` < 10s. Captured: <1s on dev workstation.
**SC-012**: `dotnet-ai render skill` < 2s. Captured: <1s.
**SC-013**: SessionStart stdout ≤ 500 tokens. Captured: 295 tokens.

## Test inventory

- 717 passing tests
- 25 skipped (gated smoke fixtures — Cursor/Codex/Copilot CLI presence)
- 0 xfailed (all formerly-deferred xfails flipped to passing in batch refactors)

## Cross-AI debate trail

- spec-phase: 4 rounds → AGREED-CLEAN-SIGN-OFF
- plan-phase: 4 rounds → AGREED-CLEAN-SIGN-OFF
- tasks-phase: 4 rounds → AGREED-CLEAN-SIGN-OFF
- implement-phase: TBD (pending Codex review of the merged change)
