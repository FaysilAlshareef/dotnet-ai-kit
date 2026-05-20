# Round-2 Review (Claude) — feature 019 plugin-native architecture

**Branch under review**: `019-plugin-native-arch` @ commit `cd71d95`
**Date**: 2026-05-19
**Scope per user direction**: Agents, skills, rules, MCPs, LSPs, profiles, plugin
setup, commands, and the main features in `src/dotnet_ai_kit/`.
**Reference state**:

- 770 unit + contract tests passing (22 platform-gated skips). Coverage 83.51%.
- Doc-lint clean (70 files scanned).
- `quality_scan.py`: 1 issue (1 thin skill, justified).
- `quality_scan2.py`: 17 issues across 4 categories.
- 3 plugin manifests validate against their JSON Schemas.
- 54 commits on feature branch since master.

---

## Severity rubric

| Level | Meaning | Action |
|---|---|---|
| **B** (Blocker) | Ship-blocker for v1.0.0. Contract violation, broken contract, or evidence of dead/stale artifact in the manifest. | MUST fix before `git tag v1.0.0`. |
| **H** (High) | Quality regression that doesn't break the build but is visible/audit-trail polluting. | Should fix in v1.0; otherwise file v1.1 issue. |
| **M** (Medium) | Polish, drift, or under-documented behavior. | Acceptable in v1.0 with a tracking note. |
| **L** (Low) | Stylistic, low-cost cleanup. | Discretionary. |

---

# Section 1 — Agents

## 1.1 Layout (verified)

| Directory | Count | Role |
|---|---|---|
| `agents-source/` | 14 | Source-of-truth markdown with `host_overrides:` blocks. |
| `agents-claude/` | 14 files (1 is orphan, see B-1) | Claude allow-list shape. |
| `agents/` | 14 | Cursor allow-list shape (1 fixture + 13 specialists). Drives `.cursor-plugin/plugin.json::agents`. |
| `agents-copilot-templates/` | 3 Jinja templates | Copilot render-time templates. |

The 14 sources are: api-designer, command-architect, controlpanel-architect,
cosmos-architect, devops-engineer, docs-engineer, **dotnet-ai-architect**
(spike fixture), dotnet-architect, ef-specialist, gateway-architect,
processor-architect, query-architect, reviewer, test-engineer.

## 1.2 Findings

### B-1 (Blocker, audit drift) — `agents-claude/dotnet-ai-architect.md` is orphan

**Evidence**: filesystem inventory + manifest cross-check.

`.claude-plugin/plugin.json::agents[]` lists **13** files (lines 6-19), but
`agents-claude/` contains **14** files. The extra is `dotnet-ai-architect.md`,
which is the **A-005 Cursor spike fixture** generated through the Claude shape
generator. Its body explicitly says "Cursor sub-agent fixture for the A-005
spike (CHK003)" — i.e., it's Cursor-purpose content shipped in Claude shape
and not loaded by the Claude manifest.

This is a real drift:

- The Claude path NEVER loads it (manifest absent).
- The Cursor path loads `agents/dotnet-ai-architect.md` (Cursor-shape).
- The Claude-shape copy is dead code in the wheel.

Why the existing tests miss it: `tests/contract/test_plugin_manifest_paths.py`
only asserts paths IN the manifest exist on disk — not the inverse (orphan
disk files). It's the same one-way gap that let commit-22 packaging tests
pass while skipping the agents directory.

**Recommendation**: either

  (a) delete `agents-claude/dotnet-ai-architect.md` (the fixture's purpose
      is to prove Cursor sub-agent loading; there is no reason for it to
      exist in the Claude shape), OR
  (b) add it to `.claude-plugin/plugin.json::agents[]`.

Option (a) matches OOS-005 / A-005 intent. Option (b) widens the fixture's
purpose to also exercise Claude's agent loader, which is already tested by
the 13 specialists.

### B-2 (Blocker, hygiene) — `agents-claude/.gitkeep` is stale

`agents-claude/.gitkeep` ships in the directory which has 14 real files.
`scripts/quality_scan.py` reports it as a (non-counted) entry. It also
appears in the frontmatter audit table with `!role !exp !cplx !iter` since
it has no YAML. Cosmetic, but ship-shape matters at v1.0 tag time.

**Recommendation**: `git rm agents-claude/.gitkeep`.

### H-1 (High) — 13 Cursor specialists have minimal frontmatter (name+description only)

**Evidence**: I generated them in commit 31 via the documented allow-list
path. Since the source files only declare `host_overrides.claude:` (no
`host_overrides.cursor:`), the Cursor generator falls back to
`{name, description}` only — no `model`, no `readonly`.

This is technically allow-list-compliant (Cursor frontmatter fields are
optional per `cursor-fixture-decision.contract.md:14-15`), but it means:

- Every specialist defaults to Cursor's app-wide model selection.
- Every specialist defaults to writeable mode.

In contrast, the spike fixture (`agents/dotnet-ai-architect.md`) explicitly
declares `model: claude-sonnet-4` + `readonly: false`. The specialists are
inconsistent with that pattern.

**Recommendation**: add `host_overrides.cursor:` blocks to the 13 specialist
sources with at least `model:` and `readonly:` matching the team's intent.
This is purely additive content; no code or contract change.

### M-1 (Medium) — Off-by-one in T171 acceptance language

`tasks.md` T171 line states "Acceptance: 13 files in `agents/`". Reality
is 14 files (1 fixture + 13 specialists). I corrected this in the commit-31
audit note but the original task line is still imprecise. Same imprecision
appears in `.cursor-plugin/plugin.json::description` which says "13
sub-agents" while shipping 14.

**Recommendation**: bump the count to 14 in both the manifest description
and T171 acceptance. Or be precise: "13 specialists + 1 spike fixture".

### M-2 (Medium) — Agent generator round-trip is not exercised end-to-end in CI

`generate_claude_agent()` is exercised by 6 unit tests; `generate_cursor_agent()`
by 3 tests. None of them re-run the actual `agents-source/*.md` → `agents-claude/`
+ `agents/` build at test time. So if a maintainer edits `agents-source/`
without re-running the generator, the build outputs drift silently until the
next manual regeneration. The wheel still ships, the manifest still loads, but
the bodies are stale.

**Recommendation**: add a contract test that asserts every `agents-source/*.md`
re-rendered via `generate_claude_agent()` matches the on-disk
`agents-claude/*.md` byte-for-byte (and the same for Cursor against `agents/`).
Catches the drift class automatically.

---

# Section 2 — Skills

## 2.1 Inventory (verified)

124 SKILL.md files across 16 categories:

```
api: 11, architecture: 7, core: 12, cqrs: 6, data: 8, detection: 1,
devops: 5, docs: 8, infra: 4, microservice: 33, observability: 3,
quality: 3, resilience: 3, security: 5, testing: 4, workflow: 11
```

Manifest matches disk exactly: 124 / 124.

## 2.2 Findings

### H-2 (High) — 6 skills lack `metadata.agent` frontmatter

**Files**:

```
skills/detection/smart-detect/SKILL.md
skills/workflow/git-worktree-isolation/SKILL.md
skills/workflow/plan-artifacts/SKILL.md
skills/workflow/plan-templates/SKILL.md
skills/workflow/systematic-debugging/SKILL.md
skills/workflow/verification-gate/SKILL.md
```

T185 (commit 28, F-B) added a note to `data-model.md` § 6 documenting that
`metadata.agent` is intentionally absent for **cross-cutting workflow /
detection skills**. The 6 above all match that description — but the
exemption is documented, not enforced.

This is a partial fix: the documentation exists, but there's no automated
gate. A new skill in `core/` without `metadata.agent` would also pass.

**Recommendation**: add a contract test that scans `skills/**/SKILL.md`,
allow-lists the 6 documented exemptions (or by category — workflow + detection),
and fails any other skill lacking `metadata.agent`.

### H-3 (High) — 4 categories of issues in `quality_scan2.py`

The full report:

```
[skill-thin]            1 (workflow/plan-artifacts/SKILL.md, 78 lines)
[outdated-newtonsoft]  11 (event-store / outbox / event-routing + knowledge)
[rule-must-mixed]       1 (rules/domain/multi-repo.md: 18 MUST vs 1 must)
(plus content-quality items — total 17)
```

The `outdated-newtonsoft-no-context` 11 hits exist DESPITE the fix in T177
(commit 26) which added "Why Newtonsoft.Json (not System.Text.Json)" upstream.
The scan still flags references that don't carry the context inline. This is
arguably a false positive (the rationale is documented at the top of
`event-store/SKILL.md`), but the scan doesn't know that.

**Recommendation**: either:
- Suppress the hits in the scan whitelist (when the rationale appears in the
  same file), OR
- Repeat the one-line rationale comment near each reference for clarity.

### M-3 (Medium) — 10 skills near the 400-line budget cap

```
400  skills/api/grpc-design/SKILL.md          ← AT cap (constitution: max 400)
397  skills/architecture/multi-tenancy/SKILL.md
395  skills/microservice/gateway/scalar-docs/SKILL.md
395  skills/infra/feature-flags/SKILL.md
392  skills/microservice/event-catalogue/SKILL.md
391  skills/core/fluent-validation/SKILL.md
387  skills/api/signalr-realtime/SKILL.md
372  skills/security/input-sanitization/SKILL.md
361  skills/microservice/processor/batch-processing/SKILL.md
360  skills/core/solid-principles/SKILL.md
```

None over budget, but `grpc-design` is **at** the cap. Any future addition
to that file will violate the constitution.

**Recommendation**: trim `grpc-design/SKILL.md` by 5–10 lines (or split into
two files) to provide headroom.

### L-1 (Low) — Skill thin: `plan-artifacts` (78 lines)

Quality_scan calls a skill "thin" below some threshold. 78 lines may or may
not be enough — depends on whether the skill is complete. Spot-checked:
`plan-artifacts/SKILL.md` is a workflow checklist that's intentionally short.
Probably acceptable; consider documenting why.

---

# Section 3 — Rules

## 3.1 Inventory (verified)

- **`rules/conventions/`** — 5 universal rules (always-loaded): async-concurrency,
  coding-style, existing-projects, security, tool-calls.
- **`rules/domain/`** — 11 path-scoped rules: api-design, architecture,
  configuration, data-access, error-handling, localization, multi-repo,
  naming, observability, performance, testing.
- **`rules/cursor/`** — 16 generated `.mdc` files (5 + 11). All have correct
  Cursor frontmatter (`alwaysApply: true` for conventions; `alwaysApply: false`
  + `globs:` for domain). Audit script in §A.3 below shows 0 issues.

All rule files within the 100-line constitution budget:

```
90  rules/domain/testing.md           ← Highest. 10 lines headroom.
76  rules/domain/configuration.md
68  rules/domain/naming.md / architecture.md
61  rules/conventions/tool-calls.md
```

## 3.2 Findings

### H-4 (High) — `rules/domain/multi-repo.md` MUST/must mixed-case (already flagged)

`quality_scan2.py` reports 18 `MUST` + 1 lowercase `must`. T190 fixed
configuration.md but missed multi-repo.md.

**Recommendation**: promote the one `must` → `MUST` in multi-repo.md.

### M-4 (Medium) — `rules/cursor/*.mdc` regeneration is one-shot, no CI gate

The `.mdc` files were generated in commit 31 via a one-shot `python -c "..."`
invocation. Nothing in CI verifies they're up to date with their sources.
If a maintainer edits `rules/conventions/async-concurrency.md`, the
`rules/cursor/async-concurrency.mdc` stays at the old content silently.

This is the same drift class as M-2 (Agent generator round-trip).

**Recommendation**: add a contract test that re-runs
`write_cursor_rules_for_plugin()` against an in-tempdir copy of rules/ and
asserts the output is byte-identical to `rules/cursor/`. Or, more pragmatic:
have the wheel build step regenerate `rules/cursor/` from sources and bail
out if anything differs from git.

### M-5 (Medium) — `domain/testing.md` 90 lines, getting close to 100

10 lines of headroom. Same pattern as M-3 for skills.

**Recommendation**: minor trim or document the budget tightness.

---

# Section 4 — Plugin manifests

All three pass schema validation:

```
codex OK    .codex-plugin/plugin.json
cursor OK   .cursor-plugin/plugin.json
claude OK   .claude-plugin/plugin.json
```

## 4.1 Findings

### B-3 (Blocker, audit) — `.claude-plugin/plugin.json::description` claims "13 specialist agents"

Description string (line 4) says "13 specialist agents". Reality: 13 in the
manifest (the 13 specialists), and the spike fixture is separately tracked
under Cursor. Phrasing is **technically** correct for the Claude path, but
internally inconsistent with `.cursor-plugin/plugin.json::description`
which says "13 sub-agents" (and ships 14 files including the fixture).

**Recommendation**: align both descriptions to "13 specialist sub-agents
(+ 1 spike fixture in the Cursor manifest)" or just "14 sub-agents (13
specialists + 1 spike fixture)" for Cursor.

### H-5 (High) — `lspServers.csharp-lsp._note` is a documentation-only field

`.claude-plugin/plugin.json::lspServers` (lines 181-185) is structured as if
Claude Code consumes it, but the entry is purely `_note` text. The actual
LSP enforcement is in `dotnet-ai check`, not Claude Code. So this field is:

- Doc-only (lines 182-184 say "References csharp-lsp plugin dependency").
- Schema-unverified — `schemas/claude-plugin.schema.json` was not inspected
  to confirm `lspServers` is part of the documented Claude Code plugin
  manifest contract.

If Claude Code doesn't actually load `lspServers`, this is **noise** in the
manifest that may confuse future maintainers.

**Recommendation**: either verify Claude Code's documented plugin spec
permits `lspServers` (cite the documentation URL) or move the note to a
separate file (e.g., `docs/lsp-dependencies.md`) and remove the field.

### M-6 (Medium) — Codex manifest deferred everything (right per OOS-004)

`.codex-plugin/plugin.json` declares only skills + MCP + hooks (no agents,
no rules). Per OOS-004 this is correct, but a future-maintainer reading the
manifest in isolation might wonder why Codex has no rules when Cursor does.

**Recommendation**: add a one-line `"_oos004_note"` field (or comment in
the description) referencing OOS-004 and the v1.1 plan.

---

# Section 5 — MCP

`.mcp.json` is single-server:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "codebase-memory-mcp",
      "args": ["--project", "."],
      "transport": "stdio",
      "dotnet_ai_kit_min_version": "0.6.1"
    }
  }
}
```

## 5.1 Findings

### H-6 (High) — `dotnet_ai_kit_min_version` field is documentation-only

`mcp_check.py` defines `MIN_CODEBASE_MEMORY_MCP_VERSION = "0.6.1"` (line 18)
**hard-coded in Python**, not read from the JSON. The JSON field is purely
informational. So if someone changes the JSON to `0.7.0` without touching
Python, the runtime check silently keeps using `0.6.1`.

This is a real drift class. Today both are aligned (`0.6.1`); tomorrow they
might not be.

**Recommendation**: read `MIN_CODEBASE_MEMORY_MCP_VERSION` from
`.mcp.json::mcpServers.codebase-memory-mcp.dotnet_ai_kit_min_version` at
import time, falling back to the hard-coded constant only if missing.
**Or** delete the field from the JSON and document the constraint in code +
docs only.

### M-7 (Medium) — Only one MCP server is shipped

The shipped `.mcp.json` declares one server (`codebase-memory-mcp`). The
ecosystem story is single-vendor. Worth noting that:

- The `extensions/` subsystem (per OOS-002) is the path for users to add
  more servers.
- `merge_mcp_config()` in `copier.py:316-340` honors third-party servers
  pre-existing in user projects.

This is correct design but **not advertised in the user-facing docs**.
First-time users reading `.mcp.json` see one entry and may not realize
they can extend.

**Recommendation**: one-line note in `README.md` or `quickstart.md`:
"Additional MCP servers can be added via `dotnet-ai extension add ...`."

---

# Section 6 — LSP

Single LSP dependency: `csharp-ls` (per `.claude-plugin/plugin.json::dependencies`).

## 6.1 Findings

### M-8 (Medium) — LSP check is gated on `dotnet-ai check` invocation

`csharp-ls` is verified at `dotnet-ai check` time (CHK009 / FR-028). It is
**not** verified at `dotnet-ai init` time. So a user can:

1. `dotnet-ai init` — succeeds even if csharp-ls is missing.
2. Open Claude Code — diagnostics don't surface; user doesn't know why.
3. Eventually run `dotnet-ai check` — discovers csharp-ls is missing.

The user's mental model breaks at step 2. The check is correct but the
*notification* timing is off.

**Recommendation**: add a one-line "csharp-ls not on PATH" warning to
`dotnet-ai init` if csharp-ls is missing. Non-blocking; just informative.
(Smoke test design already considers this — see `tests/integration/test_smoke_claude_lsp.py`.)

---

# Section 7 — Profiles

## 7.1 Inventory (verified)

12 profile files under `profiles/`:

```
profiles/generic/        — clean-arch, ddd, generic, modular-monolith, vsa (5)
profiles/microservice/   — command, controlpanel, gateway, hybrid, processor,
                           query-cosmos, query-sql (7)
```

All 12 profiles have correct frontmatter: `description: <str>`, `paths:`
list, `alwaysApply: false`.

## 7.2 Findings

### H-7 (High) — Profile classification doesn't match feature-019 rule classification

Rules are split into `conventions/` (always-loaded) and `domain/` (path-scoped).
Profiles use a different scheme: `generic/` vs `microservice/`. The
**activation** mechanism is also different — profiles are loaded via the
`pretooluse-arch-profile.sh` hook, not the SessionStart bootstrap.

This isn't wrong, but it's a parallel-tracks design where two adjacent
concepts (profiles and rules) use different vocabularies. New maintainers
must learn both.

**Recommendation**: document the relationship between profiles and rules
in `data-model.md` § "Profile vs Rule" (or wherever the split is described).
The current docs cover each side but not the cross-reference.

### M-9 (Medium) — Profile selection at session-start vs at pretool-use

`session-start-bootstrap.sh` reads `architecture_profile_name` from
`project.yml`. `pretooluse-arch-profile.sh` does the same, **at every tool
use**. The pretool hook reads from disk on every fire (no caching per the
comment). For a typical session with N tool uses, the profile body is read
~N times. Each read is small (<100 lines), but at scale (N>50 tool uses
per session) this is wasteful.

**Recommendation**: either cache in env-var across the session, or accept
the cost and add a one-line comment that the cost is acknowledged.

---

# Section 8 — Commands

## 8.1 Inventory (verified)

27 commands under `commands/`. Manifest matches disk exactly. None over
the 200-line budget. Top by size:

```
196  tasks.md
194  verify.md / analyze.md
193  detect.md
191  specify.md
189  docs.md / do.md
```

## 8.2 Findings

### M-10 (Medium) — Command line counts close to budget

7 commands within 10 lines of the 200-line cap. Same headroom concern
as the rules.

**Recommendation**: trim or document why.

### H-8 (High) — `commands/init.md` mentions "json output JSON shape" not actually emitted

Spot-checked the init command body: it documents JSON output fields that
the CLI emits, but the field-by-field list in `commands/init.md` may have
drifted from what `cli.py` actually prints. Need a doc-vs-cli linter or a
test that captures cli.py's JSON output and compares against the command's
documented shape.

This isn't a confirmed drift — it's a class of drift the codebase doesn't
defend against. T191 (commit 28) extended doc-lint to commands but only
for stale phrases, not for JSON-shape verification.

**Recommendation**: add a contract test that invokes `dotnet-ai <cmd>
--help` for each command, parses the help text, and asserts that
`commands/<cmd>.md` documents the same options. Or asserts that
`dotnet-ai <cmd> --json` (where supported) emits a shape matching the
command's documented JSON fields.

### M-11 (Medium) — 11 typer commands in cli.py vs 27 slash commands in manifest

This is expected (slash commands are wrappers that invoke the CLI, often
with arguments), but the mapping isn't documented anywhere central. From
the user's perspective, `dai.spec` calls something — what? A reader of
`commands/specify.md` shouldn't have to grep cli.py to find out.

**Recommendation**: add a 2-column table to `README.md` or
`docs/cli-and-commands.md`: slash-command → CLI command.

---

# Section 9 — Python source

`src/dotnet_ai_kit/` layout:

```
__init__.py, __main__.py, agent_generators.py, agents.py, cli.py (3777 stmts!),
config.py, copier.py, detection.py, extensions.py, manifest.py, mcp_check.py,
models.py, render.py, upgrade.py, utils.py, version_check.py
hosts/ — base.py, claude.py, codex.py, copilot.py, cursor.py
```

## 9.1 Coverage state

```
__init__              60%      __main__              0%
agent_generators     90%      agents               95%
cli                  77%      config               72%
copier               82%      detection           100%
extensions           92%      manifest             98%
mcp_check            95%      models               96%
render               94%      upgrade              96%
utils               100%      version_check        77%
hosts/base           96%      hosts/claude         80%
hosts/codex          69%      hosts/copilot        80%
hosts/cursor         75%
```

## 9.2 Findings

### B-4 (Blocker, design risk) — `cli.py` is 3777 statements in a single file

The single-file CLI module has grown to 3777 statements (per the coverage
report). Per `pyproject.toml::tool.ruff.lint.per-file-ignores`, it carries
an explicit `E501` ignore — meaning long lines are routine. This file
contains the entire CLI surface: 11 Typer commands plus shared helpers
(init step 1-7, configure step 1-N, upgrade, render, migrate, check,
extension subcommands, ...).

The constitution sets per-file budgets for rules (100), commands (200),
skills (400). There's no budget for source code, but 3777 statements is
operationally heavy:

- Coverage at 77% leaves ~870 uncovered statements.
- The `per-file-ignores` E501 is a sign of "we gave up trying to keep
  this readable".
- Test isolation suffers — a bug in one command's flow could mask issues
  in another via shared imports.

This is a v1.0 ship-blocker only insofar as it's an **architectural risk**.
Not a functional one. v1.0 ships as-is, but the next refactor should split
cli.py into per-command modules.

**Recommendation** (post-tag, not blocking v1.0):
```
src/dotnet_ai_kit/cli/
  __init__.py        # registers app
  init.py            # def init()
  upgrade.py         # def upgrade()
  configure.py       # ...
  render.py
  migrate.py
  check.py
  extension.py
  changelog.py
  status.py
```

### H-9 (High) — `config.py` 72%, `hosts/codex.py` 69%, `version_check.py` 77%

Lowest coverage outside `__main__.py` (which is just `python -m`).

`config.py` 72% — the `save_user_config` + `save_project_metadata` paths
are exercised by commit-19/20 tests, but the migration path (legacy
`ai_tools` → `enabled_hosts`) and the sidecar `.state.yml` writer have
gaps.

`hosts/codex.py` 69% — Codex is plugin-native-deferred (OOS-004), so
many code paths are stubs that raise NotImplementedError. The tests for
those raise-paths exist but don't fire on every CI matrix entry.

`version_check.py` 77% — the `check_claude_code_version()` fail-path
isn't exercised because tests run on machines where the env varies.

**Recommendation**: dedicated coverage-improvement PR to push to ≥ 85%
honestly. Identify the 5–10 missing test cases and add them.

### H-10 (High) — `render.py` ships the new `render_cursor_rule_mdc` but `dotnet-ai render` CLI does NOT expose `--host cursor`

In `render.py`:

```python
SUPPORTED_HOSTS_V1: frozenset[str] = frozenset({"claude"})
DEFERRED_HOSTS_V1_1: frozenset[str] = frozenset({"codex", "cursor", "copilot"})
```

The `render` CLI command rejects `--host cursor` with exit 20. Meanwhile
`render_cursor_rule_mdc()` (added in commit 31, T195b) IS callable from
Python but NOT from the CLI.

This is the contract intent (per the comment in render.py:48) but it
creates a **subtle UX gap**: the rule generator that ships in `render.py`
is invisible to users unless they invoke the Python module directly.

**Recommendation**: either expose a separate CLI subcommand (e.g.,
`dotnet-ai render-cursor-rules` or `dotnet-ai cursor-build`), or document
that `rules/cursor/*.mdc` is a build-time artifact regenerated only via a
maintainer script and never invoked by end users. Both are valid; the
current state (Python-only, not in CLI) is intermediate.

### M-12 (Medium) — Many integration tests assume host-binary presence

8 tests in `tests/integration/` rely on host CLIs being on PATH (claude,
codex, cursor, csharp-ls). Per my CI investigation in commits 33-41, these
tests are gated by env vars + `shutil.which()` checks and self-skip when
their dependency is absent. That design is correct, but it means on a
clean CI runner the smoke matrix runs **degraded** (8 tests skip, 0
fixtures actually validate the loader pathway).

T200 (workflow_dispatch for the release gate) is the only path to actually
exercise these. The risk: a regression that breaks `claude /agents list
--json` (or its analog for cursor) won't be caught until the maintainer
manually dispatches smoke.

**Recommendation**: invest in a self-hosted runner OR a mock host CLI
that responds to the expected commands (replay-style test). The latter
catches regressions in our manifest shape; the former catches both that
AND host loader compatibility.

---

# Section 10 — Hooks

7 hooks in `hooks/`:

```
post-edit-format.sh       PostToolUse, Edit|Write on *.cs, warn
post-scaffold-restore.sh  PostToolUse, Bash containing dotnet new, warn
pre-bash-guard.sh         PreToolUse, Bash, blocking
pre-commit-lint.sh        PreToolUse, Bash containing git commit, blocking
pretooluse-arch-profile.sh PreToolUse, Edit|Write, advisory
session-start-bootstrap.sh SessionStart, ~500 tokens
hooks.json                Wiring
```

## 10.1 Findings

### H-11 (High) — Bash-only hooks won't run on Windows without WSL/Git-Bash

All 7 hook scripts are bash. On Windows, Claude Code requires Git-Bash on
PATH or WSL. The `tests/unit/test_pretooluse_arch_profile.py` skips 4 tests
on Windows for this reason ("hook is a bash script — Windows requires Git
Bash/WSL on PATH").

This is the same A-010 cross-platform concern that the rest of the codebase
addresses. The hooks are an exception.

**Recommendation**: dual-script each hook (`*.sh` + `*.cmd` or `*.ps1`).
OR commit to "Windows users MUST have Git-Bash" and document it in the
top-level README. The latter is cheaper; the former is friendlier.

### M-13 (Medium) — Hooks are not registered/manifested in Codex/Cursor manifests beyond `configFile`

`.claude-plugin/plugin.json::hooks.configFile` points to `hooks/hooks.json`.
The Cursor + Codex manifests also point at the same file. But `hooks.json`
itself is Claude-Code-specific in syntax (`SessionStart`, `PreToolUse`,
`PostToolUse` matchers). It's unclear whether Cursor/Codex honor the same
schema — and if not, what `hooks.configFile` does for them.

**Recommendation**: document per-host hook compatibility in
`data-model.md`. If Cursor/Codex don't honor hooks.json, drop the
declaration from those manifests.

---

# Section 11 — Cross-cutting findings

## 11.1 The "manifest one-way drift" pattern

Three of the blockers (B-1) and two of the high findings (M-2, M-4) are
the same pattern: **the manifest is verified to point at on-disk files, but
nobody checks the reverse — orphan files on disk**.

Suggested unified fix:

```python
# tests/contract/test_no_orphan_artifacts.py
def test_no_orphan_agent_files():
    manifest_agents = {os.path.basename(p) for p in claude_manifest['agents']}
    disk_agents = {f for f in os.listdir('agents-claude') if f.endswith('.md')}
    assert disk_agents == manifest_agents, ...

def test_no_orphan_skills():
    ...

def test_cursor_mdc_is_regenerated_from_sources():
    # run write_cursor_rules_for_plugin in tempdir; diff against rules/cursor/
    ...
```

These three tests alone catch every drift class I found.

## 11.2 The "documented-only" anti-pattern

H-5 (lspServers `_note`), H-6 (mcp `dotnet_ai_kit_min_version`), the
Codex `_oos004_note` recommendation in M-6 — these are all instances of
fields that *look* enforceable but are actually documentation. They are
read by humans, not by code.

This is fine when documented (a doc-only field has a place), but the
practice should be consistent: either move them to clearly-documented
sidecar files, OR commit to enforcing them in code.

## 11.3 The "spike fixture is special" inconsistency

The A-005 / OOS-005 fixture is intentionally Cursor-specific. But it leaks
into:

- `agents-source/dotnet-ai-architect.md` (with both `host_overrides.cursor`
  AND `host_overrides.claude` blocks — why both if it's Cursor-only?).
- `agents-claude/dotnet-ai-architect.md` (dead generated artifact, B-1).
- `agents/dotnet-ai-architect.md` (the actual fixture, correct).

**Recommendation**: pick one of:

  (a) The fixture is **Cursor-only**. Remove `host_overrides.claude` from
      its source; don't generate a Claude shape.
  (b) The fixture is **dual-purpose** (proves both Cursor AND Claude loaders).
      Add `agents-claude/dotnet-ai-architect.md` to the Claude manifest.

Currently the codebase has the worst-of-both: a Claude shape exists but
isn't loaded.

---

# Section 12 — What's NOT broken

Worth saying explicitly:

- 770 unit + contract tests pass on the post-merge branch.
- Coverage at 83.5% (recalibrated honestly from the previous 85% aspirational
  target).
- All 3 plugin manifests validate against their JSON Schemas.
- Doc-lint scans 70 files clean.
- 16 Cursor MDC files audit cleanly (0 frontmatter issues).
- 124 skills audit cleanly for `when_to_use` (was 9 missing in F-A — fixed
  in commit 28).
- All command files within 200-line budget.
- All rule files within 100-line budget.
- All skill files within 400-line budget (with `grpc-design` at exactly 400).
- The CI pipeline now has 4 workflows (CI, CI Branch Validation, Smoke, SC
  measurements) all green on `ci/019-plugin-native-arch` HEAD.
- The OOS-005 PASS-branch flip is internally consistent (manifest declares
  `agents`, generator emits Cursor shape, release notes say "shipped").

The architecture is fundamentally sound. The findings above are quality /
hygiene / drift-defense issues, not contract violations.

---

# Appendix A — Audit script outputs

## A.1 Skill frontmatter

```
Total: 124
Bad fm: 0
Missing when_to_use: 0
Missing metadata.agent: 6  (all documented workflow/detection exemptions)
```

## A.2 Cursor MDC frontmatter

```
Total cursor mdc files: 16
Issues: 0
```

## A.3 Profile frontmatter

```
12 profiles. All have description + paths + alwaysApply=False.
```

## A.4 Manifest cross-check

```
Claude agents: 13 in manifest, 14 on disk. 1 orphan: dotnet-ai-architect.md (B-1)
Claude skills: 124 / 124, no drift.
Claude commands: 27 / 27, no drift.
Codex / Cursor: scalar dir paths, all resolve on disk.
```

---

# Appendix B — Prioritized punch list for v1.0.0 tag

| Priority | ID | Action | Files |
|---|---|---|---|
| Must-fix | B-1 | Reconcile orphan `agents-claude/dotnet-ai-architect.md` (delete or add to manifest) | `agents-claude/`, `.claude-plugin/plugin.json` |
| Must-fix | B-2 | Remove `agents-claude/.gitkeep` (dead file) | `agents-claude/` |
| Must-fix | B-3 | Align manifest descriptions for sub-agent counts | `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json` |
| Should-fix | H-1 | Add `host_overrides.cursor:` to 13 specialist sources | `agents-source/*.md` |
| Should-fix | H-2 | Contract test for `metadata.agent` exemption allow-list | new `tests/contract/test_skill_metadata.py` |
| Should-fix | H-4 | Fix the one lowercase `must` in `multi-repo.md` | `rules/domain/multi-repo.md` |
| Should-fix | H-6 | Move `dotnet_ai_kit_min_version` to single source of truth | `.mcp.json` or `mcp_check.py` |
| Should-fix | H-11 | Dual-script hooks OR document Git-Bash-on-Windows requirement | `hooks/`, README |
| Defer to v1.1 | B-4 | Split `cli.py` (3777 stmts) into per-command modules | `src/dotnet_ai_kit/cli/` |
| Defer to v1.1 | H-3 | Suppress quality_scan2 Newtonsoft false-positives or repeat rationale inline | `skills/microservice/command/*` |
| Defer to v1.1 | H-9 | Push coverage to ≥85% by adding 5–10 targeted tests | `tests/unit/` |

---

# Appendix C — Open questions for codex round 2

(These will appear in the codex-discussion prompt as the basis for
cross-review hard discussion.)

1. **B-1** — should the spike fixture live ONLY under Cursor (delete the
   Claude shape) or be dual-purpose? Spec A-005 implies Cursor-only;
   the generated Claude shape suggests dual-purpose. Codex: which is the
   binding intent?

2. **B-4** — is `cli.py` at 3777 statements a v1.1 refactor or a v1.0
   ship-blocker? Counterargument: it works, tests cover 77%, no functional
   defect. My read: ship as-is, plan refactor.

3. **H-1** — pre-flipping the 13 specialist Cursor sources to add
   `host_overrides.cursor:` blocks: is the right default `model:
   claude-sonnet-4` (matching the spike fixture) or should each specialist
   pick its own model based on complexity?

4. **H-5/H-6** — what's the policy for "documentation-only fields" in
   manifests? Allow with a `_note` convention, or strictly forbid them?

5. **H-7** — should profiles be reclassified using the same
   conventions/domain split as rules? Or is the generic/microservice
   axis fundamentally different?

6. **H-10** — should `render_cursor_rule_mdc` be exposed via the
   `dotnet-ai render` CLI, or is it strictly a build-time helper that
   end users never invoke?

7. **M-2 / M-4 / 11.1** — three drift classes (agent generator round-trip,
   cursor mdc regeneration, no-orphan-files) all fixable with one
   contract test file. Codex: agree with the unified-test recommendation
   or split per-class?
