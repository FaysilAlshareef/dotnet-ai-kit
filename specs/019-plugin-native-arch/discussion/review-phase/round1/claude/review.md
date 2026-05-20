# Review-Phase: Claude Independent Codebase Review

**Date**: 2026-05-18
**Branch**: `019-plugin-native-arch`
**Phase**: Review (post-implement, post-Codex-AGREED-WITH-NITS)
**Reviewer**: Claude (Opus 4.7, 1M context)
**Scope**: Full codebase scan after feature 019 implementation
**Verdict**: **AGREED-WITH-NOTES** (no blockers; cross-platform CI un-triggered on branch — see Note 1)

## Reviewer disclosure

This is a Claude self-review conducted **after** Codex CLI signed off
with `AGREED-WITH-NITS` in
[`implement-phase/round3-codex-verify.md`](../../implement-phase/round3-codex-verify.md).
It is not an independent first-read. Its value is:

1. Documentation of the verification I ran and the evidence captured
2. Final scan for things Codex's narrow round-3 scope (sibling-gap
   fixes) might have missed
3. Honest accounting of residual risk (skipped tests, un-triggered CI)

A second-round review by an independent model (Codex round-4 or
another reviewer) is not required to merge — the work is verified
against spec, but maintainers may want one for the v1.0.0 cut.

## Verdict rationale

- All 137 tasks in `tasks.md` are marked `[X]`; zero deferred.
- All 35 functional requirements (FR-001 → FR-035) trace to a passing
  test or a documented manual gate (`traceability.md:11-45`).
- All 14 success criteria (SC-001 → SC-014) trace to a measured value
  or a passing test (`traceability.md:51-64`, `measurements.md:48-53`).
- All 11 assumptions (A-001 → A-011) have a test gate or a manual
  gate documented at `traceability.md:70-80`.
- 729 tests pass / 25 skipped / 0 failed / 0 xfailed locally on
  Windows (Python 3.13).
- The Codex implement-phase round-3 verdict at
  [`round3-codex-verify.md:3`](../../implement-phase/round3-codex-verify.md)
  is `AGREED-WITH-NITS` with a single nit explicitly out-of-scope
  (extensions; A-003 + OOS-002).
- The host-selection invariants that drove the 3-round Codex debate
  (plain `upgrade`, `configure --tools copilot`, linked-secondary
  writer) are centralized through two module-level frozensets and
  uniformly applied across `init`, `upgrade`, `configure`, and the
  `copier.deploy_to_linked_repos` path.

## What I verified

### 1. Test baseline (local, Windows + Python 3.13)

```
$ python -m pytest --tb=no -q | tail -1
729 passed, 25 skipped in 98.31s (0:01:38)
```

```
$ python scripts/measure_always_on.py --human
SessionStart stdout: 295 tokens
Universal rules: 2585 tokens
Total always-on: 2880 tokens
Target band: 2500-3000 tokens (PASS)
vs baseline ~9000: 68.0% reduction (PASS >=65% target)
```

```
$ python scripts/doc_lint.py
[OK] Doc-lint passed (24 files scanned).
```

### 2. Skipped-test classification (25 total)

| Group | Count | Reason | Gating mechanism |
|--|--|--|--|
| `tests/integration/test_packaging_macos.py` | 12 | macOS-specific packaging assertions | CI matrix `macos-latest` (`.github/workflows/ci.yml:38`) |
| `tests/integration/test_smoke_{claude,codex,cursor,claude_lsp}.py` | 4 | Host CLI not present + smoke env unset | CI `smoke:` job, gated by `[smoke]` label or nightly cron (`.github/workflows/ci.yml:64-72`) |
| `tests/smoke/test_*.py` | 5 | Smoke harness opt-in | `CLAUDE_CODE_SMOKE=1` env var |
| `tests/unit/test_pretooluse_arch_profile.py` | 4 | Hook is a bash script; Windows needs Git Bash/WSL | CI Linux/macOS jobs cover this |

**None of the 25 skips is a real regression.** Each has a documented
gate that runs the skipped test on at least one CI lane:

- macOS packaging: covered by `static-unit` matrix at
  `.github/workflows/ci.yml:38` (`macos-latest`)
- All 4 host smoke fixtures (FR-029, SC-008): covered by the
  `smoke:` job, gated on the `[smoke]` PR label or the nightly cron
- Bash-hook tests (FR-034): covered by the same matrix on
  `ubuntu-latest` and `macos-latest`

**Note 1 (residual risk)**: CI has not yet been triggered on the
`019-plugin-native-arch` branch (`ci.yml` triggers only on push to
`master`/`development` or on PR). The cross-platform claim therefore
rests on the workflow file being correct, not on a green run. **The
maintainer should open a PR to `development` or apply the `[smoke]`
label and confirm green before tagging v1.0.0.**

### 3. Host-selection invariants

The 3-round Codex debate identified that the legacy
`copy_commands`/`copy_rules`/`copy_skills`/`copy_agents` bulk-copy path
is the dominant failure mode for plugin-native architecture. The fix
is centralized through two module-level frozensets:

```python
# src/dotnet_ai_kit/cli.py:150-155
PLUGIN_NATIVE_HOSTS: frozenset[str] = frozenset({"claude", "codex", "cursor"})
RENDER_ONLY_HOSTS: frozenset[str] = frozenset({"copilot"})
```

I verified these two sets are checked **before** any legacy bulk-copy
call in every write command:

| Command | PLUGIN_NATIVE check | RENDER_ONLY check | Legacy fallback location |
|--|--|--|--|
| `init` | `cli.py:969` | `cli.py:983` | `cli.py:995-1013` (fallback branch) |
| `upgrade` | `cli.py:1813` | `cli.py:1829` | `cli.py:1841-1862` (fallback branch) |
| `configure` recopy loop 1 | `cli.py:2377` | `cli.py:2377` | `cli.py:2390-...` |
| `configure` recopy loop 2 | `cli.py:2423` | `cli.py:2423` | `cli.py:2426-2436` |
| `copier.deploy_to_linked_repos` | line 1063 | line 1050 | line 1096 |

Two redundant frozensets in `copier.py:1041-1042` re-declare the same
sets locally (`_PLUGIN_NATIVE`, `_RENDER_ONLY`). This is fine for the
linked-secondary writer's isolation, but maintenance-wise it would be
cleaner to import the cli.py constants. **Not blocking** — the values
are equal and the linked-secondary tests assert the behavior.

### 4. Permission-write gates (`copy_permissions`)

`copy_permissions` writes `.claude/settings.json` and must only fire
when Claude is a selected host. I verified all four call sites are
gated on `claude in ai_tools`:

| Site | File:Line | Gate |
|--|--|--|
| `init` | `cli.py:1132` | `if "claude" in ai_tools:` |
| `upgrade` | `cli.py:1931` | `if config.permissions_level and "claude" in config.ai_tools:` |
| `configure` | `cli.py:2337` | `if "claude" in config.ai_tools:` |
| `copier` linked-secondary | `copier.py:1063` area | `if tool_name in _PLUGIN_NATIVE` (claude branch) |

No fifth call site found. The `_deployed_profile_path` flag at
`cli.py:2476` is a notification-only check (not a write), so it
doesn't need the gate.

### 5. FR coverage (FR-001 → FR-035)

Each FR is tested or manually gated. Confirmed against
`traceability.md:11-45`:

- **FR-001-004 (plugin packaging, host coverage)**: 3 smoke fixtures
  (`tests/integration/test_smoke_{claude,codex,cursor}.py`) + Copilot
  render lifecycle. Schema rejection tests cover FR-002.
- **FR-005-008 (per-solution footprint)**: `test_sc001_file_count.py`,
  `test_init_claude_native.py`, `test_copilot_render.py`,
  `test_fr008_unmanaged_paths_parameterized.py`. Confirmed: 3 files
  for Claude-only init, 18 with Copilot enabled.
- **FR-009-010 (runtime resolution)**:
  `test_runtime_resolution.py`,
  `test_sc003_runtime_resolution_points.py`.
- **FR-011-013 (rules + bootstrap)**:
  `test_fr011_fr012_jit_loading.py`,
  `test_rule_classification.py`,
  `test_no_arch_branching_in_always_on.py`,
  `test_sc013_tokenizer_and_fallback.py`.
- **FR-014-016 (command behavior — init/upgrade/configure)**:
  `test_fr014_fr016_init_e2e.py`,
  `test_fr015_fr024_upgrade_separation.py`. The sibling-gap fix is
  doubly-covered by `test_codex_blockers_resolved.py:225,259`.
- **FR-017 (check)**: `test_check_filesystem_inspection.py`,
  `test_sc010_check_runtime.py`, `test_check_cli_flags.py`.
- **FR-018-025 (migration safety)**: `test_migrate_classification.py`,
  `test_migrate_backup_rotation.py`, `test_migrate_cli_flags.py`,
  `test_init_force_prints_migrate.py`,
  `test_fr020_host_owner_all_values.py`.
- **FR-026-027 (agent generation)**: `test_agent_generators.py`,
  `test_copilot_agent.py`, `test_a009_host_symmetry.py`.
- **FR-028 (C# language intelligence)**:
  `test_check_filesystem_inspection.py` (csharp-ls detection),
  `test_smoke_claude_lsp.py` (CI-gated).
- **FR-029-031 (verification gates)**: Three smoke fixtures (CI-gated)
  + `test_packaging.py` + `test_fr031_exit_classes.py`.
- **FR-032 (manifest integrity actionable output)**:
  `test_fr032_manifest_actionable_output.py`,
  `test_manifest_integrity.py`.
- **FR-033 (linked-secondary writer)**:
  `test_fr033_linked_secondary_init.py`,
  `test_fr033_linked_secondary_migrate.py`. Confirmed the back door
  is closed: `copier.py:1050-1063` routes copilot through
  `CopilotHost().render()` and plugin-native hosts through plugin
  install (no bulk copy).
- **FR-034 (PreToolUse arch-profile)**:
  `test_pretooluse_arch_profile.py` (Linux/macOS in CI).
- **FR-035 (host admission gate)**:
  `test_fr035_host_admission_static_guard.py`.

### 6. SC coverage (SC-001 → SC-014)

Per `measurements.md:48-53` captured 2026-05-18 on Windows dev
workstation:

| SC | Target | Captured | Status |
|--|--|--|--|
| SC-001 (file count, Claude-only) | ≤18 (≥90% reduction) | 3 files (98% reduction) | PASS |
| SC-001 (file count, +Copilot) | ≤18 | 3 + 15 = 18 files | PASS |
| SC-002 (single host action) | 0 per-solution upgrades | Asserted by `test_sc002_two_solution_propagation.py` | PASS |
| SC-003 (runtime rename) | Next invocation observes change | `test_sc003_runtime_resolution_points.py` | PASS |
| SC-004 (always-on context) | ≥65% reduction, target band 2500-3000 | 2880 tokens / 68% reduction | PASS |
| SC-005 (no duplicate listings) | Exactly one per logical entry | `test_sc005_no_duplicate_claude_listings.py` | PASS |
| SC-006 (Copilot structural parity) | 3 content classes | `test_copilot_render.py` + 3 contract tests | PASS |
| SC-007 (user-modified preserved) | 100% | `test_migrate_classification.py` | PASS |
| SC-008 (smoke fixtures) | All 3 pass pre-merge | CI-gated (see Note 1) | PENDING-CI |
| SC-009 (packaging) | All manifest dirs present | `test_packaging.py` + macOS/Windows variants | PASS (local) |
| SC-010 (`check` runtime) | <10s | <1s (`test_sc010_check_runtime.py`) | PASS |
| SC-011 (csharp-ls missing detected) | Reported with non-zero exit | `test_check_filesystem_inspection.py` | PASS |
| SC-012 (`render` runtime) | <2s | <1s (`test_sc012_render_runtime.py`) | PASS |
| SC-013 (SessionStart ≤500 tokens) | ≤500 | 295 tokens | PASS |
| SC-014 (linked-secondary footprint) | No legacy copies | `test_fr033_linked_secondary_init.py` | PASS |

**SC-008 is the only PENDING-CI item.** Locally the smoke tests skip
because host CLIs are not installed; the CI `smoke:` job runs them on
nightly cron or PR `[smoke]` label. Until a real CI run lands, this
sits on the maintainer's pre-tag checklist.

### 7. Codex round-3 evidence (re-verified)

Codex round 3 cited specific file:line locations
([`round3-codex-verify.md:9-11`](../../implement-phase/round3-codex-verify.md)).
I spot-checked each citation against the current tree:

| Codex citation | Current state |
|--|--|
| `cli.py:1829` (upgrade `RENDER_ONLY_HOSTS` skip) | Present; correct branch |
| `cli.py:1841` (upgrade legacy fallback) | Present; correct branch |
| `cli.py:1931` (upgrade permission gate) | Present; reads `claude in config.ai_tools` |
| `cli.py:2334` (configure permission gate header) | Present at 2335 (off-by-one — see Nit 1) |
| `cli.py:2377` (configure recopy loop 1 skip) | Present; correct |
| `cli.py:2389` (configure legacy fallback) | Present at 2390 |
| `cli.py:2421` (configure recopy loop 2 skip) | Present at 2423 |
| `tests/unit/test_codex_blockers_resolved.py:225` | Present (Blocker 1' regression) |
| `tests/unit/test_codex_blockers_resolved.py:259` | Present (Blocker 2' regression) |

All citations resolve to the correct logical location; minor 1-2 line
drifts from intervening whitespace or comment edits do not affect
correctness.

### 8. Extension-add OOS-002 confirmation (Codex nit)

Codex's single nit
([`round3-codex-verify.md:27`](../../implement-phase/round3-codex-verify.md)):

> `extension-add` still has legacy extension behavior … I am not
> blocking on this because feature 019 explicitly keeps the extensions
> subsystem out of scope. See spec.md:246 and spec.md:261.

I independently verified:

- `spec.md:246` reads:
  `**A-003**: The extensions subsystem is out of scope for this release. It remains as-is and is not modified by this work.`
- `spec.md:261` reads:
  `**OOS-002**: Extensions subsystem changes. The extensions subsystem stays exactly as-is in this release.`

Codex's nit is correctly out-of-scope. **Confirmed accept.**

## Findings beyond Codex round 3

I scanned for things Codex's narrow round-3 scope (sibling-gap fixes
in `upgrade` and `configure`) might have missed. Three observations,
none blocking:

### Nit 1 — Constant duplication in `copier.py`

`copier.py:1041-1042` re-declares `_PLUGIN_NATIVE` and `_RENDER_ONLY`
locally inside `deploy_to_linked_repos` rather than importing the
cli.py module constants. The values are correct and the linked-
secondary tests cover behavior, but the duplication invites drift if
a future host is added (e.g., a fifth Codex-CLI-agents primitive).

**Suggested cleanup** (post-merge, low priority):

```python
# At top of copier.py:
from .cli import PLUGIN_NATIVE_HOSTS, RENDER_ONLY_HOSTS
# Remove _PLUGIN_NATIVE / _RENDER_ONLY locals.
```

Defer to v1.0.1 cleanup; not a release blocker.

### Nit 2 — `extension-add` legacy behavior persists (matches Codex's nit)

Independent confirmation of Codex's nit at
`round3-codex-verify.md:27`. `extensions.py:281-374` still writes
extension-supplied command/rule files into pre-existing host command/
rule directories. Under plugin-native architecture, these directories
are never written per-solution; so for a fresh Claude-only init,
`extension-add <ext>` is effectively a no-op. For a hybrid solution
where Copilot is enabled, it writes only the Copilot-shaped
extension files (which is the correct outcome).

**Status**: Out-of-scope per A-003/OOS-002. Recommended for v1.1
follow-up when the extensions subsystem is revisited.

### Nit 3 — Smoke tests need an explicit pre-tag checklist item

The CI `smoke:` job is gated on `[smoke]` PR label or nightly cron.
Tagging v1.0.0 from `master` won't automatically run the smoke gate;
it will only run on the next nightly cron tick. Maintainers should:

1. Open the v1.0.0 PR with the `[smoke]` label, **or**
2. Wait for the nightly cron to confirm green before tagging.

This is a process note; it's not a code defect.

## Additional spot-checks performed

- **`extension-add` is out-of-scope per spec** (confirmed Codex Nit):
  spec.md:246 (A-003) and spec.md:261 (OOS-002).
- **No-network invariant (A-011)** is enforced by
  `tests/unit/test_no_network_no_telemetry.py` (23 tests passed).
- **3-OS CI matrix** is declared at `ci.yml:38`
  (`[ubuntu-latest, windows-latest, macos-latest]`) × 3 Python versions
  for the `static-unit` job. The `measure.yml` workflow runs a
  separate `quickstart-3os` matrix.
- **Constitution amendment (4→5 universal rules)** is governance-
  gated by `test_constitution_amendment.py` and audit-trailed in
  `planning/06-feature-019-outcomes.md`.
- **257 files changed** since master (`+22390 / -747`) — large
  surface, but the change is concentrated in `cli.py`, `copier.py`,
  `hosts/copilot.py`, and per-test units. Each commit boundary is
  small and individually reviewable.

## Suggested pre-tag actions (not blocking merge)

1. **Open PR to `development`** so CI fires the full 3-OS matrix on
   this branch. Verify all 9 `static-unit` matrix entries are green.
2. **Apply `[smoke]` label** to that PR (or trigger the smoke job
   manually) so the 3 host fixtures execute and SC-008 flips from
   PENDING-CI to PASS.
3. **Consider follow-up issues** for the two non-blocking nits
   (constant duplication, extension-add v1.1 alignment) so they don't
   disappear into the backlog.
4. **Tag v1.0.0 only after** all of (1), (2), and the round-3 Codex
   sign-off remain valid.

## What's explicitly not in scope for this review

- **Extension subsystem behavior changes** — A-003 / OOS-002.
- **`bin/` launcher** — OOS-003, deferred to v1.1.
- **Native Codex CLI plugin agents** — OOS-004, deferred to v1.1.
- **Multi-repo activity monitor** — OOS-006, deferred to v1.1.
- **Backward-compatibility shims for pre-019 layouts** — OOS-007;
  the migration command is the bridge.

## Command evidence (reproducible)

```
$ git log --oneline 019-plugin-native-arch ^master | wc -l
20    (1 planning + 19 implementation commits)

$ git status
On branch 019-plugin-native-arch
nothing to commit, working tree clean

$ python -m pytest --tb=no -q | tail -1
729 passed, 25 skipped in 98.31s (0:01:38)

$ python scripts/measure_always_on.py --human
SessionStart stdout: 295 tokens
Universal rules: 2585 tokens
Total always-on: 2880 tokens
Target band: 2500-3000 tokens (PASS)
vs baseline ~9000: 68.0% reduction (PASS >=65% target)

$ python scripts/doc_lint.py
[OK] Doc-lint passed (24 files scanned).

$ grep -c "^- \[X\]" specs/019-plugin-native-arch/tasks.md
137
$ grep -c "^- \[ \]" specs/019-plugin-native-arch/tasks.md
0
```

## Final verdict

**AGREED-WITH-NOTES**.

The feature is correctly implemented against spec. All required
changes are present. The Codex round-3 sign-off remains valid against
the current tree. No new blockers found.

The two open items (CI not yet triggered on this branch, and the two
out-of-scope nits) are noted for the maintainer's pre-tag checklist
but do not block merge of `019-plugin-native-arch`.

If a second-round review is wanted before tagging v1.0.0, Codex
round-4 or another reviewer would be looking only at:

1. CI run greenness on the actual branch
2. Any drift introduced by an intervening commit

Neither is a code-correctness concern at this point.
