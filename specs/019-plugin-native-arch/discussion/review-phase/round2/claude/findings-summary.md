# Round-2 Claude — Findings Summary (one-page)

**Commit reviewed**: `cd71d95` on `019-plugin-native-arch`
**Test state**: 770 passing / 22 skipped / 83.5% coverage
**Full review**: `review.md` (this folder)

## Counts

- **4 Blockers** (must fix before v1.0 tag)
- **11 High** (should fix in v1.0 or file v1.1 issue)
- **13 Medium** (acceptable with tracking note)
- **1 Low** (discretionary)

## Blockers (must-fix)

| ID | Finding | Files |
|---|---|---|
| B-1 | `agents-claude/dotnet-ai-architect.md` orphan — exists on disk, NOT in Claude manifest. Spike fixture leaked into Claude shape. | `agents-claude/`, `.claude-plugin/plugin.json` |
| B-2 | `agents-claude/.gitkeep` stale (dir has 14 real files) | `agents-claude/.gitkeep` |
| B-3 | Manifest descriptions inconsistent: Claude says "13 specialist", Cursor says "13 sub-agents" but ships 14 | `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json` |
| B-4 | `cli.py` is 3777 statements (single file) — design risk, not v1.0 functional blocker. Defer to v1.1 refactor. | `src/dotnet_ai_kit/cli.py` |

## High (should-fix)

| ID | Finding |
|---|---|
| H-1 | 13 Cursor specialists inherit Cursor app-wide defaults (no explicit `model` / `readonly`) — inconsistent with the fixture pattern. |
| H-2 | 6 skills lack `metadata.agent` — documented as intentional but not enforced by any test. |
| H-3 | `quality_scan2.py` reports 17 issues across 4 categories (1 thin skill, 11 Newtonsoft-no-context, 1 mixed-case must, plus 4 content quality). |
| H-4 | `rules/domain/multi-repo.md` has 1 lowercase `must` (18 `MUST`). Same fix class as T190 applied. |
| H-5 | `.claude-plugin/plugin.json::lspServers.csharp-lsp` is a doc-only `_note` — unverified whether Claude Code spec permits the field. |
| H-6 | `.mcp.json::dotnet_ai_kit_min_version` field is read by no code; `mcp_check.py` hard-codes the constant. Real drift class. |
| H-7 | Profile classification (`generic`/`microservice`) differs from rule classification (`conventions`/`domain`). Parallel-tracks design under-documented. |
| H-8 | No test catches drift between `commands/<name>.md` docs and the actual CLI's `--help` output / `--json` shape. |
| H-9 | Coverage gaps: `config.py` 72%, `hosts/codex.py` 69%, `version_check.py` 77%. |
| H-10 | `render_cursor_rule_mdc` ships in `render.py` but `dotnet-ai render --host cursor` is rejected at exit 20. UX gap. |
| H-11 | All 7 hooks are bash-only. Windows requires Git-Bash on PATH; not documented at the top level. |

## Medium

| ID | Finding |
|---|---|
| M-1 | T171 acceptance says "13 files in `agents/`"; reality is 14. Off-by-one. |
| M-2 | No CI gate verifies `agents-claude/` + `agents/` are up to date with `agents-source/`. Silent drift class. |
| M-3 | `skills/api/grpc-design/SKILL.md` is at the 400-line cap with 0 headroom. |
| M-4 | Same drift class as M-2 for `rules/cursor/*.mdc` regeneration. |
| M-5 | `rules/domain/testing.md` at 90 lines (10 headroom in a 100-line cap). |
| M-6 | Codex manifest correctly declares only OOS-004-allowed primitives; missing a one-line forward-compat note. |
| M-7 | Only one MCP server shipped; "users can extend via `extension add`" not advertised in user-facing docs. |
| M-8 | LSP check fires only at `dotnet-ai check` time, not `init`. User-mental-model gap. |
| M-9 | `pretooluse-arch-profile.sh` reads profile from disk every tool use (N reads per session). |
| M-10 | 7 commands within 10 lines of 200-line cap. |
| M-11 | Slash-command → CLI-command mapping not documented centrally. |
| M-12 | Smoke tests skip on clean CI runners (no host CLIs). T200 (workflow_dispatch) is the only release-gate validator. |
| M-13 | `hooks.configFile` declared in all 3 manifests; unclear whether Cursor/Codex actually honor the `hooks.json` schema. |

## Low

| ID | Finding |
|---|---|
| L-1 | `skills/workflow/plan-artifacts/SKILL.md` flagged as "thin" (78 lines). Plausibly correct; document or trim. |

## Cross-cutting patterns

1. **One-way manifest drift** (B-1, M-2, M-4): manifest paths verified to exist; orphan disk files never caught.
2. **"Documented-only" fields** (H-5, H-6): manifest fields that *look* enforceable but aren't.
3. **Spike fixture leak** (B-1, H-1 sibling): the A-005 fixture's Cursor-only intent isn't strictly enforced.

## What's NOT broken (positive findings)

- 3 plugin manifests validate against JSON Schemas.
- All 16 Cursor `.mdc` files have correct frontmatter (`alwaysApply` + `globs` rules).
- All 12 profiles have correct frontmatter.
- 124 skills have `when_to_use` (was 9 missing pre-T184).
- All commands within budget. All rules within budget.
- 4 CI workflows green on the post-merge HEAD.
- The OOS-005 PASS-branch flip is internally consistent.

## Recommendation for v1.0.0 tag

| Must-do before tag | Effort |
|---|---|
| Fix B-1 (orphan fixture) | 5 min |
| Fix B-2 (delete .gitkeep) | 30 sec |
| Fix B-3 (manifest descriptions) | 2 min |

**B-4 (`cli.py` refactor) defers to v1.1.** All 3 B-1/B-2/B-3 fixes are under
10 minutes total. The high-priority items can be triaged into a v1.1 milestone.

— Claude, round 2
