# Review-Phase: Claude Content-Quality + OOS-Inclusion Review

**Date**: 2026-05-18
**Branch**: `019-plugin-native-arch`
**Phase**: Review (deep content audit + effort/value analysis on deferrals)
**Reviewer**: Claude (Opus 4.7, 1M context)
**Scope**:
  - Part A: Content quality of every shipped markdown asset (211 files
    across agents, rules, skills, commands, knowledge — no sampling)
  - Part B: Effort + value analysis for the 4 OOS-deferred items —
    OOS-003 (bin/ launcher), OOS-004 (Codex agents), OOS-005 (full
    Cursor sub-agents), OOS-006 (multi-repo monitor)
**Method**: Systematic Python scanners
  (`scripts/quality_scan*.py`, written for this review) that parsed
  frontmatter, scanned bodies, validated cross-references, and counted
  patterns across all 211 markdown files.
**Verdict**: Part A: **AGREED-WITH-FIXES** (12 real content issues).
            Part B: Recommend **defer 3 / include 1 conditionally**.

## How I scanned

Three scanner scripts read every asset markdown file in the repo:

| Scanner | Coverage | What it finds |
|---|---|---|
| `quality_scan.py` | All 211 .md files | Frontmatter integrity, line budgets, stale patterns, broken cross-refs, duplicate descriptions |
| `quality_scan2.py` | All 211 .md files | Empty sections, mixed voice, outdated .NET refs, metadata field distribution, agent symmetry |
| `quality_scan3.py` | Pinpoint contexts | Detail on each finding (5 lines around match) |
| `quality_scan4.py` | All 211 + cross-doc | Knowledge file orphans, paths consistency, placeholder usage, rules without Related-Skills |

Scripts are checked into `scripts/quality_scan{1..4}.py` and runnable
by any maintainer to reproduce the findings.

## Part A — Content quality audit

### A.1 What the scans confirmed clean

These properties hold for every file (no exceptions):

| Property | Files | Status |
|---|---|---|
| All skills have `name` frontmatter | 124/124 | ✓ |
| All skills have `description` frontmatter | 124/124 | ✓ |
| All skill descriptions start with "Use when..." | 124/124 | ✓ |
| All skills have `metadata` block | 124/124 | ✓ |
| All commands have `description` frontmatter | 27/27 | ✓ |
| All rules have `description` frontmatter | 16/16 | ✓ |
| All `skills/.../SKILL.md` cross-references resolve | all | ✓ no broken refs |
| All Claude agents have `name` + `description` | 13/13 | ✓ |
| No skill exceeds 400-line budget | max 397 | ✓ |
| No command exceeds 200-line budget | max 196 | ✓ |
| No rule exceeds 100-line budget | max 90 | ✓ |
| No `alwaysApply` legacy frontmatter field anywhere | 0 hits | ✓ (018 PR2a swept clean) |
| No outdated .NET version refs (.NET 5, Core 2/3) | 0 hits | ✓ |
| No duplicate skill descriptions across all 124 | 0 dupes | ✓ |
| Architecture profile count matches spec | 12/12 | ✓ (microservice + generic branches) |

### A.2 Real findings (12 issues)

#### F-A: 9 `skills/core/*` missing `when_to_use` frontmatter [MEDIUM]

**Evidence** (`quality_scan2.py` output):

```
Top-level frontmatter fields across 124 skills:
  name: 124          ← all
  description: 124   ← all
  metadata: 124      ← all
  when_to_use: 115   ← 9 missing
  paths: 9
```

The 9 files missing `when_to_use` are exactly the 9 `skills/core/*`
skills:

- `skills/core/async-patterns/SKILL.md`
- `skills/core/coding-conventions/SKILL.md`
- `skills/core/csharp-idioms/SKILL.md`
- `skills/core/dependency-injection/SKILL.md`
- `skills/core/design-patterns/SKILL.md`
- `skills/core/error-handling/SKILL.md`
- `skills/core/functional-csharp/SKILL.md`
- `skills/core/modern-csharp/SKILL.md`
- `skills/core/solid-principles/SKILL.md`

**Impact**: `when_to_use` is the explicit activation hint that the
018 PR2a refactor lifted from nested `metadata:` to top level. Its
absence on these 9 skills means:

- The skills can still activate via the `description` ("Use when…")
  fallback that all 124 skills carry.
- But the explicit field is the documented activation contract.
- These 9 are the **most foundational skills** (core C# patterns) —
  they're the ones most likely to be invoked, so consistency
  matters.

**Required fix** (1 commit, ~5 minutes):

For each of the 9 files, add a `when_to_use:` field below `metadata:`,
extracted from the existing description. Example:

```yaml
# skills/core/async-patterns/SKILL.md — BEFORE
name: async-patterns
description: Use when writing async code, propagating CancellationTokens, or fixing async/await pitfalls.
metadata:
  category: core
  agent: dotnet-architect
---

# skills/core/async-patterns/SKILL.md — AFTER
name: async-patterns
description: Use when writing async code, propagating CancellationTokens, or fixing async/await pitfalls.
metadata:
  category: core
  agent: dotnet-architect
when_to_use: When writing async code or fixing async/await pitfalls (CancellationToken propagation, ConfigureAwait, async void).
---
```

#### F-B: 6 skills missing `metadata.agent` [LOW]

**Evidence**: 6 skills have only `metadata.category` (no `metadata.agent`):

```
skills/detection/smart-detect/SKILL.md
skills/workflow/git-worktree-isolation/SKILL.md
skills/workflow/plan-artifacts/SKILL.md
skills/workflow/plan-templates/SKILL.md
skills/workflow/systematic-debugging/SKILL.md
skills/workflow/verification-gate/SKILL.md
```

The other 118 skills declare an owning specialist agent
(e.g. `agent: dotnet-architect`, `agent: api-designer`).

**Analysis**: These 6 are cross-cutting workflow skills not tied to a
single specialist. Workflow skills like `verification-gate` and
`git-worktree-isolation` are invoked by EVERY agent, not by one. So
this is likely **intentional** (no single owner). But it's an
unstated convention — a maintainer adding a new workflow skill
wouldn't know whether to omit `agent:` or pick one.

**Recommended action**: Either
- (A) Add `agent: <name>` to all 6 with a sensible fallback (e.g.
  `dotnet-architect` as the generalist), OR
- (B) Document in `data-model.md` that `metadata.agent` is optional
  and omitted for cross-cutting workflow skills.

I recommend (B) — option A adds noise; option B documents the
existing convention. Not blocking.

#### F-C: Universal rule `async-concurrency.md` carries `paths:` frontmatter [LOW]

**Evidence** (`quality_scan.py`):

```
[universal-rule-has-paths] 1 issue(s)
  - rules/conventions/async-concurrency.md: paths: ["**/*.cs"]
```

Universal (5 always-on) rules are loaded by folder classification
(`rules/conventions/`), not by frontmatter `paths:`. The other 4
universal rules omit `paths:`. The `paths:` on async-concurrency is
informational, not gating, but it's inconsistent.

**Recommended action**: Either remove `paths:` from this one rule, OR
add a `paths: ["**/*"]` to all 4 siblings for symmetry. I'd remove —
universal rules don't need it.

#### F-D: 5/16 rules missing "Related Skills" section [MEDIUM]

**Evidence** (`quality_scan4.py`):

```
With "Related Skills" section: 11/16
  + rules/conventions/async-concurrency.md
  + rules/conventions/coding-style.md
  + rules/conventions/security.md
  + rules/domain/api-design.md
  + rules/domain/architecture.md
  + rules/domain/configuration.md
  + rules/domain/data-access.md
  + rules/domain/error-handling.md
  + rules/domain/observability.md
  + rules/domain/performance.md
  + rules/domain/testing.md

Without "Related Skills" section: 5/16
  - rules/conventions/existing-projects.md
  - rules/conventions/tool-calls.md
  - rules/domain/localization.md
  - rules/domain/multi-repo.md
  - rules/domain/naming.md
```

**Impact**: The "Related Skills" section is how a rule points the AI
to skills that implement its guidance. 5 rules don't have it, so a
user hitting (e.g.) a localization rule won't see a pointer to the
`skills/.../localization` skill.

**Required fix** (5-10 minutes per rule):

For each of the 5 missing rules, add a `## Related Skills` section
listing the relevant skill paths. The pattern is:

```markdown
## Related Skills
- `skills/category/skill-name/SKILL.md` — short rationale
- `skills/category/other-skill/SKILL.md` — short rationale
```

Specific suggestions:

- **existing-projects.md**: link to `skills/detection/smart-detect/`
  (detects existing patterns)
- **tool-calls.md**: link to `skills/workflow/verification-gate/`
  (gates tool use), `skills/workflow/systematic-debugging/`
- **localization.md**: link to `skills/cqrs/notification-handlers/`
  if it exists, or relevant i18n skills
- **multi-repo.md**: link to `skills/workflow/multi-repo-workflow/`
  (which DOES exist — clean miss)
- **naming.md**: link to `skills/core/coding-conventions/`

#### F-E: 3 truly empty section headers [LOW-MEDIUM]

**Evidence** (`quality_scan2.py` + scan3 contexts):

```
skills/workflow/plan-templates/SKILL.md:70  "## Summary"        ← empty, followed by ## Constitution Check
skills/workflow/plan-templates/SKILL.md:73  "## Research Findings" ← empty, followed by ## Service Plan
commands/review.md:144                       "## Dry-Run / Errors" ← empty, followed by ## Error Handling
```

(The other 4 flagged "empty sections" in `session-management/SKILL.md`
and `specify.md` are template placeholders — `## Date: {date}` etc.
— which are field labels inside a code-template block, not real
empty sections. Scanner over-flagged; these are fine.)

**Required fix** (5 minutes):

Either delete the empty headers OR populate them. Looking at the
context:

- `plan-templates/SKILL.md:70 "## Summary"` — should describe the
  feature summary template (one paragraph)
- `plan-templates/SKILL.md:73 "## Research Findings"` — should
  describe how to capture research findings
- `commands/review.md:144 "## Dry-Run / Errors"` — should describe
  --dry-run behavior and error modes

#### F-F: `agents-source/` host_overrides pattern is inconsistently applied [MEDIUM]

**Evidence** (`quality_scan4.py`):

```
host_overrides: 1   ← only 1 of 14 source files has this field
```

The contract at `contracts/agent-source.contract.md` and the
generator at `src/dotnet_ai_kit/agent_generators.py:128-160`
(`_build_host_frontmatter`) expects the source to declare per-host
fields under `host_overrides.<host>`:

```yaml
# Expected pattern (only dotnet-ai-architect.md follows it):
name: foo
description: bar
host_overrides:
  claude: { role: ..., expertise: ... }
  cursor: { model: ..., readonly: ... }
  copilot: { tools: ..., model: ... }
```

But the 13 universal `agents-source/*.md` files have Claude-shaped
fields **at top level** instead:

```yaml
# Actual pattern in 13 of 14 source files:
name: dotnet-architect
description: Leads overall .NET solution architecture...
role: advisory               ← top level (NOT under host_overrides.claude)
expertise: [...]             ← top level
complexity: high             ← top level
max_iterations: 20           ← top level
```

**Functional impact**: `_build_host_frontmatter` only reads from
`host_overrides`, so when you generate a Claude agent from one of
the 13, the output gets ONLY `name` + `description`. The top-level
`role`/`expertise`/`complexity`/`max_iterations` are silently
ignored.

This means:
- The current 13 `agents-claude/*.md` files have minimal frontmatter
  (just name + description) — which is what gets generated.
- But the source files **look like** they're providing more.

This is **architectural confusion** between intended pattern and
actual data. Two ways to resolve:

**Option A — Migrate to the host_overrides pattern**:
Rewrite the 13 source files to nest their Claude fields under
`host_overrides.claude`. Then `generate_claude_agent()` would emit
the full Claude-shape frontmatter (with role/expertise/etc.).

**Option B — Document that the source IS the Claude shape**:
Update `contracts/agent-source.contract.md` to say the universal
agents use top-level Claude fields (because Claude is the dominant
host); only the Cursor-spike-fixture uses host_overrides for the
non-Claude shape. Strip the top-level fields from the source files
since they're not used.

**Recommended**: Option B. Pragmatically, agents-source/ files are
human-readable specs of the agent's purpose. The
role/expertise/complexity/max_iterations are documentation that
HUMANS read, even though the generator doesn't emit them. Document
this; don't refactor.

#### F-G: 8 Newtonsoft.Json references without explained rationale [MEDIUM]

**Evidence** (`quality_scan.py` + scan3 contexts):

```
skills/microservice/command/event-store/SKILL.md:17 (5 refs total)
skills/microservice/command/outbox/SKILL.md:139
skills/microservice/processor/event-routing/SKILL.md:200
knowledge/outbox-pattern.md:251
```

The pattern is **intentional** for the microservice event-sourcing
stack — Newtonsoft.Json handles polymorphic deserialization needed
for event payloads, while System.Text.Json (the .NET default)
struggles with type discriminators in event-sourced systems.

But **none of the 4 files explains this**. The closest is
`event-routing/SKILL.md:200`:

```
| Using System.Text.Json | Use Newtonsoft.Json (JsonConvert.DeserializeObject) |
```

A pitfall row that says "use Newtonsoft" but doesn't say why.

**Required fix**: Add a brief rationale to one of the skills (the
upstream `event-store/SKILL.md` is the natural place), and have the
other 3 cross-reference it:

```markdown
## Why Newtonsoft.Json instead of System.Text.Json

Events in this template use Newtonsoft.Json's polymorphic serializer
for the `Data` column because System.Text.Json (the .NET default)
does not handle the type discriminator pattern used by the event
catalogue without per-type converters. See `knowledge/event-sourcing-flow.md`
for the discriminator design.
```

A new contributor reading these skills today would reasonably assume
Newtonsoft.Json is a leftover from a pre-.NET-5 migration.

#### F-H: `knowledge/grpc-patterns.md` is orphaned [LOW]

**Evidence** (`quality_scan4.py`):

```
clean-architecture-patterns.md: referenced from 4 other file(s)
concurrency-patterns.md:        referenced from 3 other file(s)
cosmos-patterns.md:             referenced from 1 other file(s)
cqrs-patterns.md:               referenced from 7 other file(s)
ddd-patterns.md:                referenced from 5 other file(s)
dead-letter-reprocessing.md:    referenced from 5 other file(s)
deployment-patterns.md:         referenced from 3 other file(s)
documentation-standards.md:     referenced from 1 other file(s)
event-sourcing-flow.md:         referenced from 10 other file(s)
event-versioning.md:            referenced from 6 other file(s)
grpc-patterns.md:               referenced from 0 other file(s)  ← orphan
modular-monolith-patterns.md:   referenced from 2 other file(s)
outbox-pattern.md:              referenced from 4 other file(s)
service-bus-patterns.md:        referenced from 5 other file(s)
testing-patterns.md:            referenced from 5 other file(s)
vsa-patterns.md:                referenced from 1 other file(s)
```

15 of 16 knowledge files are linked from at least one skill, rule,
or other knowledge file. **Only `grpc-patterns.md` (497 lines!) has
0 incoming references.**

Yet there ARE gRPC-related skills:
- `skills/api/grpc-design/SKILL.md`
- `skills/microservice/grpc/interceptors/SKILL.md`
- `skills/microservice/grpc/service-definition/SKILL.md`
- `skills/microservice/grpc/validation/SKILL.md`

**Required fix**: Add `## Related Knowledge` (or weave into "Related
Skills") links from these gRPC skills to `knowledge/grpc-patterns.md`.
A 497-line knowledge doc that nobody links to is wasted shipping.

#### F-I: `rules/domain/configuration.md` mixed binding language [LOW]

**Evidence** (`quality_scan3.py` context):

```
rules/domain/configuration.md:
  14: ## MUST
  17: - All options classes MUST call `ValidateDataAnnotations()` and `ValidateOnStart()`
  18: - Options classes must declare `public const string SectionName` for the config section key
  21: - Default values must be set in the options class properties, not in appsettings.json
```

Lines 18 and 21 use lowercase `must` inside a `## MUST` section.
Per RFC 2119 conventions (which the codebase otherwise follows),
ALL-CAPS is the binding form. Mixing cases in a binding section is
ambiguous — does the reader treat line 18 as binding (matches section
header) or non-binding (lowercase)?

**Required fix**: Promote lowercase `must` to `MUST` on lines 18 + 21.

(Note: `multi-repo.md` was flagged for the same pattern but reads OK
on inspection — its 1 lowercase `must` is in a description sub-clause
not a binding bullet. Skip.)

#### F-J: 7 stale pre-019 references in commands (cross-ref to tool-surface-review) [HIGH]

Already documented in detail in `tool-surface-review.md` as F2/F3:

```
commands/init.md:34  - "copies commands/rules"
commands/init.md:60  - "Number of commands copied"
commands/init.md:76  - ".claude/commands/"
commands/init.md:77  - ".claude/rules/"
commands/init.md:106 - "Copied: {N} commands"
commands/init.md:107 - "Copied: {N} rules"
commands/init.md:127 - "Copied: {N} commands"
commands/init.md:128 - "Copied: {N} rules"
commands/configure.md:126 - "re-copies commands with the selected style"
```

Cross-referenced here for completeness. Severity: HIGH (slash-command
body contradicts FR-005/FR-006).

#### F-K: `host_overrides:` field used in only 1 of 14 source agents (architectural smell — same as F-F) [info]

Logged separately because the 1/14 ratio is suspicious in isolation;
the root cause is documented in F-F.

#### F-L: 1 thin skill: `skills/workflow/plan-artifacts/SKILL.md` (78 lines) [LOW]

The shortest skill in the corpus. Other workflow skills average
130-180 lines. Either:

- It's intentionally lean (a pointer skill).
- It's underdeveloped and should be expanded.

Read it before deciding; not blocking either way.

### A.3 Content-quality summary

| Severity | Count | Files |
|---|---|---|
| HIGH | 1 | commands/init.md + configure.md (F-J — covered by tool-surface-review) |
| MEDIUM | 5 | F-A (9 skills), F-D (5 rules), F-F (architectural), F-G (8 refs), F-I (1 rule) |
| LOW-MEDIUM | 1 | F-E (3 empty headers) |
| LOW | 3 | F-B, F-C, F-H, F-L |
| TOTAL | 11 | (12 if you count F-K as separate from F-F) |

**Distribution by surface**:

| Surface | Issues |
|---|---|
| skills/ | F-A (9), F-B (6), F-E (3), F-L (1) |
| rules/ | F-C (1), F-D (5), F-I (1) |
| commands/ | F-J (7 — already in tool-surface-review) |
| agents-source/ | F-F (architectural) |
| skills + knowledge/ | F-G (8), F-H (1 orphan) |

**Aggregate effort to fix all 12** (excluding F-J which is in
tool-surface-review): 1.5-2 hours for a focused documentation commit.

## Part B — OOS effort/value analysis

### How I evaluated effort

For each OOS item I checked:

1. **What exists today** — partial implementation, stub, or zero
2. **What's required for "shipped" status** — research, code, tests,
   docs, fixture
3. **Risk** — API stability, scope creep, regression surface

### B.1 OOS-003 — `bin/` launcher

**What exists**: Nothing. No `bin/` folder; no launcher script;
distribution is via `uv tool install` + host plugin install.

**What "shipped" would require**:
- POSIX launcher script (`bin/dotnet-ai-kit`) — find the installed
  package, dispatch to its CLI entry point
- Windows wrapper (`.cmd` or `.ps1`) for cross-platform parity
- Packaging glue to include `bin/` in the wheel
- 3-OS smoke test confirming launcher resolves correctly
- README section documenting the launcher use case

**Effort**: SMALL-MEDIUM. ~4-6 hours including 3-OS testing.

**Value**: LOW for v1 user persona.
- Per `planning/06-feature-019-outcomes.md:13-21`: "v1 ships
  exclusively through host plugin systems... A standalone `bin/`
  launcher would duplicate the host-plugin install surface without
  adding value for the v1 user persona."
- The persona is "a .NET dev already using one of the 4 hosts."
  They install via host plugin and use slash commands.
- The launcher is useful for **plugin-less CI/CD integration** —
  e.g. running `dotnet-ai check` in GitHub Actions without a host —
  but no v1.0 user has requested this.

**Risk**: LOW. Additive; doesn't affect existing surfaces.

**Recommendation**: **DEFER to v1.1**.
The effort is reasonable but the value is unproven. Wait for a real
CI/CD use case to surface in v1 user feedback, then design for that
specific case.

### B.2 OOS-004 — Native Codex CLI plugin agents

**What exists**:
- `src/dotnet_ai_kit/agent_generators.py:190-200` —
  `generate_codex_agent()` raises `NotImplementedError`.
- `.codex-plugin/plugin.json` — declares skills + MCP + hooks; NO
  `agents` field.
- 13 source-of-truth files in `agents-source/` ready to feed a
  generator.

**What "shipped" would require**:
1. **Verify Codex's current `agents/*` plugin API stability** —
   per `research.md:21`: "Codex CLI docs explicitly document only
   those primitives [skills, MCP, hooks]. Native agents for Codex
   remain OOS-004 until docs catch up." Has this status changed?
   No evidence in the spec docs that it has.
2. Implement `generate_codex_agent()` (replace the
   NotImplementedError raise with real generation logic, ~50 lines).
3. Add Codex agent allow-list constant in `agent_generators.py`
   (parallel to `_CLAUDE_ALLOW_LIST`).
4. Generate 13 Codex-format agent files into a build-output
   directory (e.g. `agents-codex/`).
5. Add `agents` field to `.codex-plugin/plugin.json`.
6. Update `codex-plugin.schema.json` to permit the new field.
7. Write `tests/integration/test_smoke_codex_agents.py` smoke fixture
   with a CI gate.
8. Update `spec.md` to mark OOS-004 as resolved + bump A-006.
9. Update `traceability.md` with new test rows.

**Effort**: MEDIUM-LARGE. ~12-16 hours plus the spike research time
to validate Codex's current agent API shape.

**Value**: MEDIUM-HIGH **if** Codex users want native specialist
agents in the host's agent listing.

**Risk**: HIGH. Per the deferral rationale: "at spec-phase round 2
the Codex plugin API for `agents/*` files was not stable enough to
ship against." If the API still isn't stable, shipping creates a
**breaking-change surface** the moment Codex changes its agent
contract. We'd then need to either chase Codex's API or revert.

**Recommendation**: **DEFER to v1.1**.
The maintainer cited API instability as the explicit blocker. Without
fresh evidence that Codex's agents/* API is now stable, shipping
this in v1.0 is a quality risk — exactly the failure mode FR-035's
host-admission gate exists to prevent ("a passing host-specific
smoke fixture" is required, and we'd have to maintain it against
moving target docs).

### B.3 OOS-005 — Full Cursor sub-agent generation (conditional on A-005)

**Current state** (spike outcome at
`specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json`):

```json
{
  "outcome": "pending",
  "timestamp": null,
  "failure_log_path": null,
  "ci_run_url": null
}
```

**What exists**:
- `src/dotnet_ai_kit/agent_generators.py:203-216` —
  `generate_cursor_agent()` is **already functional** (renders
  Cursor-shape frontmatter + body). NOT raising NotImplementedError.
- `.cursor-plugin/plugin.json` declares `"agents": "./agents/"`.
- `agents/dotnet-ai-architect.md` — the 1 mandatory spike fixture.
- `tests/integration/test_smoke_cursor.py` — the gate (skipped
  without `CURSOR_SMOKE=1` + Cursor CLI).
- `tests/unit/test_fr029_cursor_fail_path.py` — meta-test ensuring
  fixtures `cursor_fixture_pass/` and `cursor_fixture_fail/` stay
  consistent with spec language.

**What "shipped" would require**:
1. **Run `test_smoke_cursor.py` in CI with `CURSOR_SMOKE=1`** —
   confirm the fixture loads cleanly.
2. **Run `generate_cursor_agent()` on the 13 source files** to
   produce `agents/<name>.md` for each universal specialist (12 net
   new files — the 1 fixture already exists). ~5 minutes of
   automated generation.
3. **Update `cursor-subagent-outcome.json`** from `"pending"` to
   `"passed"` with timestamp + CI run URL.
4. **Verify** the meta-test `test_fr029_cursor_fail_path.py` still
   passes (no spec language change needed; the PASS branch IS the
   default-assume language).
5. **Update `traceability.md`** to mark OOS-005 resolved.

**Effort**: SMALL. ~2-3 hours of which 1.5 hours is the CI Cursor
fixture run (env setup + actual test).

**Value**: HIGH for Cursor users.
- Today: Cursor users see 0 sub-agents in the host listing (only the
  fixture is listed via the `./agents/` reference).
- Shipped: Cursor users see all 13 specialists in their agent
  listing — feature parity with Claude.

**Risk**: LOW-MEDIUM. The risk is **fixture-load failure**: if
Cursor's loader can't parse the file shape. But this is exactly what
the fixture is for — if it loads, the contract says full generation
ships. If it fails, the fail-path is well-documented at
`cursor-fixture-decision.contract.md:34-50`.

**Recommendation**: **INCLUDE IN v1.0.0 if the fixture passes today**.
This is the lowest-effort/highest-value OOS item by a wide margin.
The infrastructure is built; only the CI smoke run gates it. The
maintainer should:

1. Set `CURSOR_SMOKE=1` and run `pytest tests/integration/test_smoke_cursor.py`
   locally (requires Cursor CLI installed).
2. If PASS: run `generate_cursor_agent()` for the 12 missing agents
   → commit → update outcome.json → ship.
3. If FAIL: follow the well-documented fail-path in the contract;
   defer to v1.1 per OOS-005.

**This is the only "include now" candidate of the four.**

### B.4 OOS-006 — Multi-repo activity monitor

**What exists**: Nothing. No daemon; no monitor CLI; no state file
schema; FR-033's linked-secondary writer handles single-direction
deployment but doesn't watch for upstream changes.

**What "shipped" would require**:
1. Background daemon/service architecture (long-running process
   watching N repos).
2. Cross-platform service installation (launchd / systemd / Windows
   Service / Scheduled Task).
3. Plugin version comparison logic across repos.
4. Notification/reporting system (CLI? email? GitHub issue?
   webhook?).
5. State persistence (sqlite? jsonl? where?).
6. New CLI surface (`dotnet-ai monitor start|stop|status|...`).
7. Configuration schema for which repos to watch.
8. Tests for multi-repo scenarios (10+ fixture repos minimum).
9. Conflict resolution UX when repos diverge.
10. Documentation: install, configure, troubleshoot, uninstall.
11. Migration story: how do existing v1 users opt in?
12. Privacy/security review: what does the monitor see and log?

**Effort**: VERY LARGE. 3-5 weeks for a maintainer working
full-time. This is a separate substantial feature — comparable in
scope to plugin-native architecture itself.

**Value**: MEDIUM-HIGH for teams managing 10+ sibling repos.
- For solo developers or small teams: low value (host plugin update
  reaches all repos automatically).
- For large teams with sibling repos that need to stay aligned: high
  value.
- The v1.0 deferral rationale (`outcomes.md:33-39`) explicitly
  notes: "FR-033 + US1 already solve the core drift problem;
  multi-repo surveillance is a separate sibling-repo orchestration
  feature."

**Risk**: VERY HIGH. This is a new product surface with:
- Persistent state (data corruption risk)
- Cross-platform service management (OS integration risk)
- Privacy implications (what the monitor accesses)
- Scope creep almost guaranteed (notifications, dashboards, etc.)

**Recommendation**: **DEFER strongly to v1.2+** (not even v1.1).
Pulling this into v1.0 would balloon the release by weeks, introduce
a new product surface, and create a maintenance burden disproportionate
to the v1 user persona. The maintainer was correct to defer this.

### B.5 Summary table

| OOS | Effort | Value | Risk | Recommendation |
|---|---|---|---|---|
| OOS-003 (bin/ launcher) | SMALL-MEDIUM (4-6h) | LOW | LOW | **DEFER v1.1** |
| OOS-004 (Codex agents) | MEDIUM-LARGE (12-16h + research) | MEDIUM-HIGH | HIGH (API churn) | **DEFER v1.1** |
| OOS-005 (Full Cursor sub-agents) | SMALL (2-3h) | HIGH | LOW-MEDIUM | **INCLUDE NOW if fixture passes** |
| OOS-006 (Multi-repo monitor) | VERY LARGE (3-5 weeks) | MEDIUM-HIGH (large teams only) | VERY HIGH | **DEFER v1.2+** |

### B.6 Concrete action for OOS-005

Since OOS-005 is the recommendation, here's the exact playbook:

```bash
# 1. Set up Cursor smoke environment
export CURSOR_SMOKE=1
# (Install Cursor CLI from cursor.com if not already)

# 2. Run the smoke fixture
pytest tests/integration/test_smoke_cursor.py -v

# IF PASS:
# 3. Generate the 12 missing Cursor agents
python -c "
from pathlib import Path
from src.dotnet_ai_kit.agent_generators import generate_cursor_agent
sources = sorted(Path('agents-source').glob('*.md'))
for src in sources:
    if src.stem == 'dotnet-ai-architect':
        continue  # spike fixture already in agents/
    out = Path('agents') / src.name
    out.write_text(generate_cursor_agent(src), encoding='utf-8')
    print(f'Generated: {out}')
"

# 4. Update the spike outcome
cat > specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json << 'EOF'
{
  "outcome": "passed",
  "timestamp": "2026-05-18T<HH:MM:SS>Z",
  "failure_log_path": null,
  "ci_run_url": "<CI run URL>"
}
EOF

# 5. Verify the meta-test still passes
pytest tests/unit/test_fr029_cursor_fail_path.py -v

# 6. Commit
git add agents/ specs/019-plugin-native-arch/discussion/tasks-phase/cursor-subagent-outcome.json
git commit -m "feat(019): OOS-005 resolved — full Cursor sub-agent generation"
```

**If the smoke FAILS**: The fail-path is well-documented at
`contracts/cursor-fixture-decision.contract.md:34-50`. Defer to v1.1.

## Combined verdict

### Part A (content quality):
**AGREED-WITH-FIXES** — 12 real issues, all docs-only.
Aggregate fix time: ~2 hours for a focused commit.
None block the v1.0.0 implementation; they polish the user-visible
content layer.

### Part B (OOS inclusion):
**1 INCLUDE / 3 DEFER**:
- **OOS-005**: include in v1.0.0 IF the Cursor smoke fixture passes
  locally for the maintainer (small effort, high value, infrastructure
  ready).
- **OOS-003** (bin/), **OOS-004** (Codex agents), **OOS-006**
  (multi-repo monitor): defer as planned.

## Combined pre-tag punch list

Merging this review with `review.md` (CLI) and `tool-surface-review.md`:

| Item | Source | Severity | Time |
|---|---|---|---|
| F1: CHANGELOG.md v1.0.0 entry | tool-surface | HIGH | 30 min |
| F2: commands/init.md stale | tool-surface + F-J | HIGH | 30 min |
| F3: commands/configure.md:126 | tool-surface + F-J | MEDIUM | 5 min |
| F4: AGENTS.md stale counts | tool-surface | MEDIUM | 10 min |
| F5: CONTRIBUTING.md stale | tool-surface | MEDIUM | 10 min |
| F6: rules/cursor/ empty | tool-surface | LOW-MEDIUM | 15 min |
| F-A: 9 core skills + when_to_use | this review | MEDIUM | 30 min |
| F-D: 5 rules + Related Skills | this review | MEDIUM | 30 min |
| F-G: Newtonsoft.Json rationale | this review | MEDIUM | 20 min |
| F-H: grpc-patterns links | this review | LOW | 10 min |
| F-I: configuration.md MUST/must | this review | LOW | 5 min |
| F-E: 3 empty section headers | this review | LOW | 10 min |
| F-C: async-concurrency paths: | this review | LOW | 2 min |
| F-B: 6 workflow skills agent | this review | LOW | document, 5 min |
| OOS-005: Cursor smoke run | this review | OPPORTUNITY | 1-2h |
| **TOTAL** | | | **~4 hours** |

If the maintainer fixes all 14 items in one focused docs+content
commit (under 4 hours), v1.0.0 ships with:
- Code: AGREED-WITH-NOTES (review.md) — no changes needed
- Tool surface: clean (tool-surface-review F1-F6 resolved)
- Content quality: clean (this review's F-A through F-L resolved)
- OOS-005: shipped if fixture passes

## Reproducibility

All findings in Part A reproducible by:

```bash
python scripts/quality_scan.py    # round 1
python scripts/quality_scan2.py   # round 2
python scripts/quality_scan3.py   # round 3 (pinpoint contexts)
python scripts/quality_scan4.py   # round 4 (knowledge orphans)
```

These scanners should be promoted to a `scripts/asset_quality_check.py`
and wired into CI as part of O1 (extend doc_lint) from
`tool-surface-review.md`.

## What I did NOT audit

For completeness, this review **did not** cover:

- **Skill body technical accuracy**: I didn't verify that the C#
  code examples compile, the `Result<T>` patterns are correct, or
  the gRPC interceptor patterns match current .NET 8/9 idioms. This
  would require running actual .NET builds against each example.
- **Knowledge file factual accuracy**: I didn't verify that
  `cosmos-patterns.md` accurately reflects current Cosmos DB SDK
  behavior. This would require domain expertise + current SDK
  reference docs.
- **Cross-host loader behavior**: I didn't run the actual Cursor,
  Codex, or Copilot loaders to confirm each host accepts our
  generated files. The smoke fixtures gate this in CI (when CI runs).

These are reasonable maintenance follow-ups but not blocking for
v1.0.0 docs polish.
