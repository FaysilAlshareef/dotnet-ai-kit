# dotnet-ai-kit v-next strategy: keep-vs-rebuild and the .NET 10 question

**Date:** 2026-05-30
**Author:** lead-architect analysis for Faysil Alshareef (kit maintainer)
**Status:** strategy proposal — **superseded** by the maintainer's decision to do a full rewrite. This doc weighs *keep-vs-rebuild* and argued against from-scratch; the maintainer has since chosen a full .NET 10 rewrite. The implementation blueprint is [21-v2-architecture-blueprint.md](21-v2-architecture-blueprint.md). Read this doc for the evidence and trade-offs; read 21 for the plan.
**Inputs:** 12 grounded codebase scanners + 6 dated feature researchers (Claude Code, Codex CLI, Cursor, GitHub Copilot, .NET 10 stack, prompt-engineering). Every claim below cites a `path`, `path:line`, a dated source URL, or a verified command output. Where a researcher marked a fact ungrounded, it is marked `[ungrounded]` here too.

> **Verification status (independent re-check, 2026-05-30).** After synthesis, the load-bearing claims were re-verified against primary sources — not just trusted from the subagents:
> - **Rule-delivery gap (the linchpin):** confirmed in source — `copy_rules` sits only in the dead `else` branch (`cli.py:1286-1334`), and the *other* write path `ClaudeHost.write_per_solution_files` (`hosts/claude.py:110-130`) writes `.claude/settings.json` only. So a plugin-native Claude install receives **no** domain rules. The field report (`issues/rule-enforcement-gap/`) corroborates independently.
> - **Command duplication:** confirmed — `grep "Bounded skill selection (FR-012)"` → exactly 17 of 27 files.
> - **Agent-count drift + fixture leak:** confirmed — `agents-source/` = 14 (incl. `dotnet-ai-architect` fixture), `agents-claude/` = 13, manifest = 13.
> - **Broken skill sample:** confirmed — `event-catalogue/SKILL.md:189` calls `Activator.CreateInstance` on a positional record.
> - **External (web) claims that drive recommendations:** System.CommandLine **2.0.8 stable (2026-05-12)** — confirmed via nuget.org (3.0.0-preview also exists). **Copilot auto-detects `.claude-plugin/plugin.json`** — confirmed via code.visualstudio.com/docs/copilot/customization/agent-plugins ("The plugin format is shared between VS Code, GitHub Copilot CLI, and Claude Code. A single plugin repository can work across all three tools"; keep `name` identical; the **cloud** agent still consumes render-to-files only). **"Commands merged into skills"** — confirmed via code.claude.com/docs/en/skills, with the nuance that `commands/` is **legacy-but-still-supported** (backward-compatible) — migrating commands→skills is the endorsed *direction*, not a forced break, so §7 can be sequenced without urgency.
> - Remaining feature-matrix rows not re-checked here (Codex/Cursor specifics, hooks event counts) stay at the researchers' stated confidence; treat anything marked `[ungrounded]` as design-blocking-until-confirmed.

> **Framing decision (read this first).** The user's request — "rewrite the tool from scratch using .NET 10 instead of Python" — is treated here as **two orthogonal questions**, not one:
> 1. **Re-architect the artifact/content layer** (124 skills, 27 commands, ~13 agents, 16 rules, profiles, hooks, manifests). This is ~90% of the product, it is CLI-language-independent, and it helps **all four** AI tools. **This is the high-value work.**
> 2. **Re-platform the CLI** (Python → .NET 10). This is ~10% of the product, it touches only init/check/upgrade/render/migrate, and its value is **distribution + dogfooding**, not capability.
>
> This report is a **keep-vs-rebuild** plan, not a greenfield design. The current product already has 717 passing tests (verified: 739 `def test_` across 130 files), a no-network invariant (A-011), a validated always-on token-reduction baseline, a working per-host adapter architecture (`hosts/base.py` → claude/codex/cursor/copilot), and a constitution. A from-scratch rewrite throws all of that away. We do not recommend it.

---

## 1. Executive summary

The mess the maintainer correctly senses is **not** that the tool is written in Python, and **not** that the artifacts are wrong. It is that **there is no single authored source-of-truth for any artifact type, and no enforced projection from that source to each host.** Agents are authored once (`agents-source/`) but the generators that project them are abandoned and hand-edited around (five consecutive manifest-fix commits: `f2ed807`, `57a2cce`, `3a7c30e`, `3f8f10f`). Commands duplicate the same boilerplate across 17 of 27 files. Rules overlap and — critically — **do not actually load for a plugin-native Claude install** (confirmed below at `cli.py:1334`). Manifests drift across three hand-maintained JSON files plus a fourth copy in `pyproject.toml`.

The CLI, by contrast, is mature: `manifest.py` and `upgrade.py` are exemplary, the `hosts/` adapter is the cleanest seam in the repo, and the test corpus is a genuine regression-safety asset. Re-implementing all of that in .NET 10 is **real cost with no capability gain** — its only payoffs are native distribution (`dotnet tool install -g`) to .NET developers and dogfooding credibility.

**Thesis: REBUILD the artifact/content layer first as a tool-agnostic track; treat the .NET 10 CLI port as a SECOND, parallel track gated on contract tests, and do neither from scratch.** The single discriminating criterion for the .NET-10 question — *does distribution-to-.NET-devs + dogfooding outweigh re-implementing a mature CLI and rewriting the ~46% of tests coupled to Python internals?* — resolves to **"yes, but only once the port is decoupled from the content work and gated on the language-neutral invariants (A-011, token budgets, the 40 portable artifact/contract tests)."** That decoupling is what makes "yes" defensible; without it, "yes" is reckless.

### Decision table (per area)

| Area | Verdict | Primary evidence | Priority |
|---|---|---|---|
| Per-host adapter design (`hosts/`) | **KEEP + generalize** | Clean ABC + registry; polymorphic verify path (`cli.py:3489/3498`) | P0 (becomes the backbone) |
| Single source-of-truth agent model (`agents-source/` + allow-lists) | **KEEP the pattern, REBUILD the pipeline** | `agent_generators.py:101-129` allow-lists are sound; drivers abandoned (`scripts/gen_*.py`) | P0 |
| Token-budget discipline | **KEEP, re-anchor on live measurement** | `measure_always_on.py` (≥65% vs ~9000 baseline); but measures the wrong layer for plugin-native | P0 |
| Test corpus + invariants (A-011, FR-031, SC-001/003/004) | **KEEP; partition for the port** | 739 `def test_`; A-011 AST scan; 8-exit-code contract | P0 (the gate) |
| SDD lifecycle + `do.md` reference-orchestration | **KEEP** | `do.md:43,63,68,94,108,109,122` delegate by reference, not copy-paste | P1 |
| Hooks (the 6 `.sh` files) | **KEEP, standardize + extend** | Small, fail-open, Windows-aware (`pre-bash-guard.sh:19-26`) | P1 |
| Agents pipeline (5 dirs, hand-edited manifests, fixture leak) | **REBUILD** | Manifest not reproducible from `gen_*.py`; fixture leaks to Codex/Copilot | P0 |
| Command boilerplate (FR-012 / dry-run / agent-mapping ×17) | **REBUILD (extract to shared)** | `grep "Bounded skill selection (FR-012)"` → 17 files | P1 |
| Rule delivery + enforcement | **REBUILD** | `copy_rules` not called for plugin-native Claude (`cli.py:1324-1334`); field report `issues/rule-enforcement-gap/` | P0 |
| Skill/command overlap + 124-skill always-on listing | **REBUILD (consolidate + reclassify)** | dup skill pairs; ~1% skill-listing budget vs 124 entries | P1 |
| Manifest generation (4 disjoint copies) | **REBUILD (generate from one descriptor)** | 5-commit churn; count drift 13 vs 14 | P0 |
| Stale planning (`01-vision`, content dumps) | **ARCHIVE/REWRITE** | `01-vision.md:91` pre-019 claim; 6,887 lines of dumps | P2 |
| CLI core in Python (`cli.py` 3,872 lines, dup models) | **REFACTOR now; PORT to .NET 10 second** | dup `load_project_metadata` (`config.py:284` vs `render.py:123`) | P1 (refactor) / P2 (port) |
| .NET 10 re-platform | **YES, gated + parallel, NOT from scratch, NOT first** | distribution + dogfooding win; ~46% tests are Python-internal-coupled | P2 |

---

## 2. Current-state map

Counts below are verified by command, not estimated.

### 2.1 Agents + the generation pipeline

| Dir | Role | Count | Carries `host_overrides`? |
|---|---|---|---|
| `agents-source/` | **source of truth** | 14 (13 specialists + `dotnet-ai-architect` fixture) | yes (only dir that does) |
| `agents-claude/` | generated Claude shape | 13 (fixture excluded) | no |
| `agents/` | generated **Cursor** shape | 14 (incl. fixture) | no |
| `agents-copilot-templates/` | 3 jinja2 templates | — | — |
| `.codex/agents/*.toml` | rendered per-solution at `init` | — | — |
| `.github/agents/*.agent.md` | rendered per-solution (Copilot) | — | — |

Pipeline core: `agent_generators.py` (381 lines) — per-host allow-lists at lines 101-129; verbatim-body invariant (T037). Three driver scripts (`scripts/gen_agents_claude.py`, `gen_cursor_agents.py`, `gen_claude_plugin_manifest.py`) are **abandoned**: they would each produce 14 entries, but the committed manifest and `agents-claude/` carry 13 — so every recent manifest change is a hand-edit. `agents.py` (118 lines) is vestigial: `detect_ai_tools` still says "v1.0: claude only" (`agents.py:103`), contradicting the 4-host model.

### 2.2 Commands (`commands/*.md`)

27 files, 4,109 lines, all ≤200 lines (largest `tasks.md` 196, smallest `learn.md` 64). Uniform single-key frontmatter (`description` only). Aliases (`/dai.*`) are **not** in these files — generated by the CLI (`cli.py:2729-2739`). `do.md` orchestrates the 6-phase lifecycle by reference (7 "same logic as /dotnet-ai.X" pointers) — the one example of duplication done right.

### 2.3 Rules (`rules/conventions/` + `rules/domain/`)

5 universal + 11 domain = 16 files (verified), 36-68 lines each. Universal 5 total 191 lines (tested budget 300). `paths:` frontmatter is consumed **only** by the Cursor `.mdc` renderer (`render.py:render_cursor_rule_mdc`); the Claude manifest has no `rules` field. Two domain rules (`error-handling.md`, `performance.md`) declare `paths: ["**/*.cs"]` — effectively always-on, defeating the JIT classification.

### 2.4 Skills (`skills/**`)

124 `SKILL.md` files (verified) in two trees: **generic** (api/architecture/core/cqrs/data/infra/resilience = 51 files, 12,760 lines) and **microservice** (8 subdirs incl. an undocumented `grpc/` = 33 files, 8,299 lines), plus quality/ops (devops/docs/observability/quality/security/testing/workflow = 39 files, 7,580 lines). All ≤400 lines (ceiling: `api/grpc-design` at exactly 400). Uniform 7-key frontmatter; consistent body template. All names are bare kebab-case (no namespace prefix).

### 2.5 CLI core (`src/dotnet_ai_kit/`)

~10,150 lines / 21 modules. `cli.py` is 3,872 lines (in the ruff E501 ignore list); `init()` alone spans ~690 lines. `copier.py` is 1,491 lines mixing 6 responsibilities. `models.py` (814) carries **duplicate** model pairs for each on-disk file (UserConfig+DotnetAiConfig for config.yml; ProjectMetadata+DetectedProject for project.yml). `manifest.py` (362) and `upgrade.py` (187) are exemplary.

### 2.6 Hosts (`src/dotnet_ai_kit/hosts/`)

ABC `Host` (`base.py`, 105) + registry (`__init__.py`, 72) + 4 adapters: claude (187), codex (176), cursor (114), copilot (629). Copilot holds ~80% of package logic. The **verify** path is polymorphic; the **write** path is hardcoded per-host (`cli.py:1372/1391/1409`) because the ABC `write_per_solution_files -> list[Path]` contract is too weak for Copilot's conflict-partition result type.

### 2.7 Tests (`tests/**`)

739 `def test_` (verified), 130 files (verified), six tiers. 102/125 substantive files carry a `T###` tag → an executable traceability matrix. Portability partition (the port plan): **40 pure-artifact/contract tests** (32%, port verbatim), **27 CLI black-box tests** (22%, re-target at the .NET binary), **58 internal-unit tests** (46%, reimplement against .NET internals).

### 2.8 Plugin / packaging / MCP / LSP / hooks

`.claude-plugin/plugin.json` — verified shape: keys `[name, version, description, author, homepage, repository, license, logo, keywords, skills, commands, agents]`; `agents` is a **13-entry array**; **no** `hooks`/`mcpServers` keys (removed in `3f8f10f` because Claude auto-discovers them). `.mcp.json` (codebase-memory-mcp, stdio), `.lsp.json` (csharp-ls). 6 hooks (`hooks/*.sh`, verified). `pyproject.toml` has a 17-entry hand-maintained `force-include` map; packaging of `agents/` is gated on a spike-fixture outcome (`pyproject.toml:54-61`).

### 2.9 Planning, docs, profiles, prompts, config, knowledge, templates

19 planning docs (13,801 lines); 3 are content dumps (14/15/18, 6,887 lines combined) superseded by shipped `skills/`+`templates/`. 10 docs (1,337 lines). 12 profiles (825 lines, all ≤100, read by the PreToolUse hook at every Write/Edit). 1 prompts file (a 403-line planning artifact mis-located). 4 config presets + 1 mcp overlay. 16 knowledge files (6,346 lines) — **not** in any manifest; only 5 skills cross-link them. 233 template files. Plus a **field-evidence folder** `issues/rule-enforcement-gap/` (REPORT.md, CHANGE-MAP.md, RESEARCH-2) dated 2026-05-29/30 — the maintainer's own dogfooding diagnosis (see §4.4, §7).

---

## 3. What works — KEEP

These are the assets a rewrite must preserve. Each is load-bearing.

1. **The per-host adapter + registry design (`hosts/`).** ABC `Host` with `install_paths` / `verify_install` / `write_per_solution_files`, a name-keyed registry (`hosts/__init__.py:30-52`), and a typed `InstallStatus` (`base.py:24-43`). The verify path is genuinely polymorphic end-to-end (`cli.py:3487-3498`) — proof the pattern works when the contract fits. **This is the seam everything else should route through**, in Python now and in .NET later.

2. **The single-source-of-truth agent pattern.** `agents-source/<name>.md` carries `name`/`description` + `host_overrides.{claude,cursor,codex,copilot}`; per-host generators copy only the host's allow-listed fields and emit the body verbatim (`agent_generators.py:138-175`, T037). `_build_host_frontmatter` rejects unknown override keys with a clear FR-027 error (lines 161-167). `generate_codex_agent` (242-330) is the most polished function in the area — a correct TOML emitter using literal multi-line strings so markdown survives. **The pattern is right; only the projection plumbing is broken.**

3. **The test corpus + invariants.** A-011 no-network via AST scan (`test_no_network_no_telemetry.py:69`, parametrized over every src file); FR-031 8-exit-code contract (`test_fr031_exit_classes.py`); SC-001 ≤18-file footprint; SC-003 three-point runtime resolution; SC-004 token band; A-009 host-symmetry meta-test; smoke gating behind env-var + CLI-on-PATH. 40 of these are pure-artifact/contract tests with zero Python coupling — **they are the cross-language spec.**

4. **The SDD lifecycle and `do.md` reference-orchestration.** The two-mode model (microservice vs generic), the 6-of-8 handoff schemas for generic mode (`planning/13-handoff-schemas.md:11-26`), and `do.md`'s delegation-by-reference (`do.md:172-181` error-recovery/`--resume`) are sound product design. Keep verbatim.

5. **The hooks.** 6 small (40-96 line) fail-open hooks, guarded by per-hook enable env-vars, Windows-aware (the two pre-* hooks smoke-test `python3/python/py` to dodge the Store stub, `pre-bash-guard.sh:19-26`). `manifest.py` (sha256 + traversal guard + v1→v2 upgrade-on-read) and `upgrade.py` (atomic backup→rollback→rotate) are exemplary and should be ported, not redesigned.

6. **Cross-platform + safety discipline (verified, not aspirational).** `from __future__ import annotations` in 21/21 modules; zero `os.path`/`shell=True`; list-arg subprocess; atomic temp-replace writes; explicit `encoding="utf-8"`. This is the behavior the .NET port must replicate via source-generated, reflection-free code.

---

## 4. What is messy — REBUILD

All four problems below are **symptoms of one root cause: no single authored source-of-truth per artifact type, and no CI-enforced projection from that source to each host.** They are presented separately for evidence, but §6a proposes one cure.

### 4.1 The agents pipeline (severity: high)

- **The committed Claude manifest and `agents-claude/` are not reproducible from their own generators.** `gen_claude_plugin_manifest.py:32` derives stems from the 14-file **Cursor** `agents/` dir (an accident); `gen_agents_claude.py:40` globs the 14-file source — both would emit 14, but the committed manifest array and `agents-claude/` have 13 (verified: `agents-claude/` = 13, `agents/` = 14, `agents-source/` = 14). Every recent manifest change is a hand-edit bypassing the generators. **This is the precise cause of the 5-commit churn.**
- **The Cursor spike fixture leaks into real Codex and Copilot output.** Both hosts glob `agents-source/*.md` with no filter (`hosts/codex.py:154`, `hosts/copilot.py:263`), so `dotnet-ai init --ai codex` writes `.codex/agents/dotnet-ai-architect.toml` — a file whose body reads "This is the spike fixture for the Cursor sub-agent capability." `.codex-plugin/plugin.json:4` even bakes "14 subagents" into its description.
- **Two Copilot renderers; one is dead.** `generate_copilot_agent()` (`agent_generators.py:355`) is never called — `CopilotHost._render_agent_file` uses `agent.md.j2` instead. The contract file describes code that never runs.
- **Five overlapping directories** for one concept, with `agents/` being the *generated Cursor output* (not the source) — a naming trap that caused the manifest generator to read the wrong dir.
- **The drift suite has a blind spot:** `test_no_orphan_artifacts.py` tests the generator *functions* but never the driver scripts or manifest generator, so the count mismatch is invisible to CI.

### 4.2 Command duplication (severity: high)

- The FR-012 "Bounded skill selection" paragraph appears **word-for-word in 17 of 27 files** (verified: `grep "Bounded skill selection (FR-012)"` → 17). A "Dry-Run Behavior" section appears in 17 files. The 6-line microservice agent-mapping stanza is copy-pasted across ~8 commands (`specify.md:30-35`, `clarify.md:30-35`, `plan.md:28-33`, …). Any policy change requires editing 17 files.
- **Agent-path drift:** command bodies say "Read `agents/<role>.md`" but the plugin registers `./agents-claude/*.md` — and the two trees already differ. It is ambiguous which the AI reads at runtime.
- **Deterministic logic encoded as AI prompts:** `status.md` (144 lines) is entirely "read feature dir, count completed tasks, render a dashboard" — work a CLI would do faster, cheaper, and more reliably.

### 4.3 Skill and rule overlap (severity: medium)

- **Near-duplicate skill pairs:** `api/controllers` ≈ `api/controller-patterns`; `api/scalar` ≈ `api/openapi-scalar` (near-identical `BearerSecuritySchemeTransformer`); `architecture/cqrs-basics` semantically overlaps the entire `cqrs/` directory.
- **Rule overlap:** `data-access.md` vs `performance.md` (AsNoTracking, ToList-before-Where, pagination); `Task.Run in ASP.NET Core` is byte-identical in `async-concurrency.md:23` and `performance.md:26`; parameterized-SQL and `async void` duplicated across two convention rules each.
- **Frontmatter redundancy:** in 8 of 12 `core/` skills (and ~all quality/ops skills) `when_to_use` is a verbatim copy of `description` — a no-op field.
- **A broken code sample:** `event-catalogue/SKILL.md:188-189` calls `Activator.CreateInstance(type, nonPublic:true)` on a positional record — throws `MissingMethodException` at runtime (records have no parameterless ctor). A correctness bug shipped in a skill.

### 4.4 Rule delivery + enforcement (severity: high — confirmed mechanically and in the field)

This is the most consequential finding, because it undercuts the kit's central value proposition (convention enforcement) and the token-reduction story.

- **For a plugin-native Claude install, `copy_rules` is not called.** Verified: the `copy_rules(...)` call at `cli.py:1334` sits inside the `else` fallback branch (`cli.py:1324-1326`: "keep legacy bulk copy for any future host registered outside both PLUGIN_NATIVE_HOSTS and RENDER_ONLY_HOSTS"). Claude **is** plugin-native, so this branch does not run for it. Rules therefore are **not** written into the project's `.claude/rules/` at `init`; they live only at plugin-root `rules/`, which the plugin manifest (verified: no `rules` key) cannot wire into Claude Code's path-scoped system.
- **The dated primary source explains why this matters:** Claude Code plugins have no always-on rules primitive; a plugin-root `CLAUDE.md` is not loaded; the only plugin-native way to force rule *bodies* into context is a hook emitting `hookSpecificOutput.additionalContext` (code.claude.com/docs/en/memory, retrieved 2026-05-30). The native JIT mechanism (`.claude/rules/*.md` + `paths:`) *does* exist — but only if rules are delivered there with frontmatter, which for plugin-native Claude they are not.
- **The maintainer's own field report confirms the consequence.** `issues/rule-enforcement-gap/REPORT.md` (dated 2026-05-29) documents that on the live `Ecom-LTD/Circle` project, the kit's rules were "never in the model's context" while it wrote the Query side: only the `Command` project had `.dotnet-ai-kit/project.yml`, so the arch-profile hook fired there but hit "Project metadata not initialized; exit 0" for `Query`/`Processor`. Result: public setters and weak tests in the un-initialized repos. **Two independent failure modes** — (a) the per-repo metadata gap means the one body-injecting hook silently no-ops in secondary repos, and (b) enforcement is advisory (`exit 0`, never blocks).
- **The deterministic gate exists but is never run:** the kit ships a NetArchTest (`Entities_ShouldHave_PrivateSetters()`) in `skills/quality/architectural-fitness/SKILL.md` but only as an on-demand skill, never generated or executed by default.

### 4.5 Manifest generation (severity: high)

Three hand-maintained plugin.json files plus a fourth keyword/agent-count copy in `pyproject.toml`, with no single source. Drift is already shipping: agent count is 13 in Claude/marketplace but 14 in Codex/Cursor; the `ddd` keyword is in 3 of 4. The JSON schemas were *loosened* during the churn (`schemas/claude-plugin.schema.json:34-76`, `oneOf[scalar, array, object]`) so they now accept exactly the shapes that broke — they can no longer catch a regression. The scalar-path existence check lives in `scripts/check.py` (dev-only), **not** the shipped `dotnet-ai check`.

### 4.6 Stale planning + CLI debt (severity: medium)

- `planning/01-vision.md:91` retains the pre-019 "agents become routing logic inside commands, not separate files" claim; multi-tool support is logged as v1.1 in `01-vision.md:74-76` and `12-version-roadmap.md:104-106` but shipped in v1.0 (`59050b2`); `12-version-roadmap.md:44-45` says "307 test functions / 8 CLI commands" vs the actual 717+/migrate+render. Content dumps (14/15/18) are 6,887 lines of superseded material.
- CLI debt: duplicate `load_project_metadata` (`config.py:284` returns a typed model; `render.py:123` returns a dict); `PLUGIN_NATIVE_HOSTS` copy-pasted 3× to dodge an import cycle (`copier.py:25-28` admits it); dead `copy_agents()` returning 0 for every host (`copier.py:486-546`); two template engines (jinja2 in copier vs hand-rolled `${...}` regex in render).

---

## 5. Per-tool feature matrix

Grounded in the dated researcher sources (retrieved 2026-05-30 unless noted). The single most important cross-tool finding is at the bottom: **Copilot's "render-only" classification is now false for IDE/CLI surfaces.**

| Capability | Claude Code | Codex CLI | Cursor | GitHub Copilot |
|---|---|---|---|---|
| **Plugin manifest** | `.claude-plugin/plugin.json`; `skills` ADDs, `commands`/`agents` REPLACE; paths must start `./` (GA) | `.codex-plugin/plugin.json`; **scalar** `./` pointers; **no `agents` field** (GA) | `.cursor-plugin/plugin.json`; field is **`agents`** not `subagents` (authoritative schema; A-005 resolved) (GA 2.5) | `plugin.json`; auto-detected at **4 paths incl. `.claude-plugin/plugin.json`** (Preview) |
| **Skills** | `SKILL.md`, 3-level progressive disclosure; commands **merged into** skills (GA) | `SKILL.md` (name+description only) — **replaces deprecated custom prompts** (GA) | `SKILL.md` + `paths`/`disable-model-invocation` (GA 2.4) | `.prompt.md` slash commands + plugin `skills` (GA / Preview) |
| **Agents** | `agents/`; subfolders scope; plugin agents **ignore** hooks/mcpServers/permissionMode (GA) | `.codex/agents/*.toml` written per-solution at `init` (GA) | `agents/` .md frontmatter; nesting + async (GA 2.5) | `.agent.md` (renamed from `.chatmode.md`); subagents + handoffs (Preview) |
| **Agent teams / orchestration** | Agent teams (**experimental**, env-gated; config is **runtime state**, not shippable); dynamic workflows (**research preview**, no manifest field) | threads/MultiAgentV2; `max_depth=1`, `max_threads=6`; **no "teams" primitive** (GA) | subagent trees + `/multitask` + TS SDK `orchestrate` (GA/SDK) | subagents + handoffs (Preview) |
| **Hooks** | `hooks/hooks.json`; ~40 events; `command`/`http`/`prompt`/`agent` types; `PreToolUse` can deny/ask (GA) | `hooks/hooks.json`; 10 events; **only `command` type runs**; `commandWindows` override; `PLUGIN_ROOT` + `CLAUDE_PLUGIN_ROOT` aliases (GA) | `hooks.json`; rich event set incl. `beforeShellExecution`/`afterFileEdit`; `CLAUDE_PROJECT_DIR` alias (GA) | `.github/hooks/*.json`; 8 events; Claude/CLI-compatible format (Preview) |
| **MCP** | `.mcp.json` inline/root; Tool Search defers schemas (default on) (GA) | `[mcp_servers.*]` in config.toml + plugin `./.mcp.json`; OAuth HTTP (GA) | `mcp.json`; `${env:}`/`${workspaceFolder}` interpolation (GA) | `.vscode/mcp.json` + plugin `mcpServers`; cloud agent supports MCP (GA) |
| **LSP** | `.lsp.json`; LSP tool (goToDefinition/findReferences/call-hierarchy); binary user-installed (GA) | **None native** `[ungrounded]` — community MCP-LSP bridges only; do not assume | **None agent-facing** `[ungrounded]` — editor uses LSP internally, no plugin field | `lspServers` in plugins (Preview); cloud-agent LSP unconfirmed `[ungrounded]` |
| **Always-on instructions** | `CLAUDE.md` + `.claude/rules/` + path-scoped `paths:` (GA); plugin **cannot** ship loaded rules | `AGENTS.md` (root→cwd merge); "rules" = **Starlark sandbox policy**, not docs (GA) | `.cursor/rules/*.mdc` (`alwaysApply`/`globs`) + `AGENTS.md` (GA) | `.github/copilot-instructions.md` + `*.instructions.md` (`applyTo`) + **native `AGENTS.md`/`CLAUDE.md`** (GA) |
| **Marketplace** | `marketplace.json`; source types path/github/url/git-subdir/npm (GA) | `.agents/plugins/marketplace.json`; Teams/Business sharing (GA) | `cursor.com/marketplace` (OSS + manual review) (GA 2.5) | shared `marketplace.json` format; default `github/copilot-plugins`, `awesome-copilot` (Preview) |

**Marked ungrounded** (per researchers, do not design hard dependencies on these):
- The **dynamic-workflows JS API** (`agent()`, `parallel()`, `pipeline()`, `budget`) — the *feature* is grounded (research preview, 16-concurrent/1000-total, save-as-command), the *API surface* is not (no Workflow tool schema; only secondary blogs). RESEARCH-2 in the issue folder independently verified the feature shipped in **v2.1.154 on 2026-05-28** — "~2 days old, far too new to take a hard dependency on."
- **Agent-teams config** is runtime state (session IDs, tmux panes); there is **no plugin/project field** to ship a team. The only shippable primitive is a subagent definition.
- **LSP for Codex and Cursor** (agent-facing) does not exist; only Claude Code (and Copilot plugins, Preview) expose it.

**The finding that overturns a stated invariant:** Both Copilot CLI docs (docs.github.com) **and** VS Code Copilot docs (code.visualstudio.com, dated 5/28/2026) confirm the plugin manifest is auto-detected at four paths **including `.claude-plugin/plugin.json`** "for compatibility with Claude Code plugin layouts." So `CLAUDE.md`'s "Copilot is render-only (no plugin system)" is **false for the IDE/CLI surfaces** as of 2026 — one plugin repo can serve Claude Code + Copilot CLI + VS Code Copilot. The **cloud coding agent** still consumes only render-to-files (`copilot-instructions.md`, `*.instructions.md`, `AGENTS.md`, `.agent.md`), so the render track stays necessary for that surface only. Caveat to verify: one VS Code doc said the Copilot format "has no defined token" for `${CLAUDE_PLUGIN_ROOT}` — audit hook/MCP path references before betting on single-manifest reuse.

---

## 6. Proposed clean architecture

### 6a. Artifact / content management — the high-value rebuild

**One model, authored once, projected per host, CI-enforced.** This single change dissolves §4.1–4.5.

```
artifacts/                      # SINGLE source of truth (rename agents-source/ → here)
  agents/<name>.md              # name + description + host_overrides.{claude,codex,cursor,copilot}
  commands/<name>.md            # body + shared-fragment references (no inlined boilerplate)
  rules/<name>.md               # body + paths: glob + scope: {universal|domain}
  skills/<name>/SKILL.md        # body + paths: + invocation policy
  fragments/                    # the FR-012, dry-run, agent-mapping stanzas — authored ONCE
tools/                          # per-host projectors (generalize hosts/)
  → build/<host>/...            # generated, gitignored OR clearly-named; never hand-edited
```

Design rules, each tied to a finding:

1. **Generalize the `hosts/` adapter into the projection engine.** Today `hosts/` is the cleanest seam but the **write** path bypasses it with hardcoded branches (`cli.py:1372/1391/1409`) because the contract is too weak. Fix the contract first: replace `write_per_solution_files -> list[Path]` with a rich `HostWriteResult { written, preserved, force_rendered, pending_consent }` that all hosts return, inject a context object (`plugin_root`, `project_root`, config) to kill the `cli↔hosts` circular import (the late `from dotnet_ai_kit.cli import _get_package_dir` at `claude.py:140` etc.), drop `permission_profile` from the shared signature (Claude-only), and collapse the triple-duplicated verify/install into a `PluginNativeHost` base parameterized by manifest dirname. Then projection routes through the registry, not branches.

2. **One generation entrypoint, CI-gated.** Replace the three abandoned `gen_*.py` scripts with a single `gen` step that regenerates every host's agent files **and** all manifests from `artifacts/` in one pass, then a CI test runs it and asserts `git diff --exit-code`. This structurally eliminates the manifest-churn class — the manifest can never again diverge from the source.

3. **Make the fixture a first-class, explicitly-routed concept** (or move `dotnet-ai-architect` to `tests/fixtures/` entirely). Production globs over `artifacts/agents/` then become fixture-free by construction, permanently fixing the Codex/Copilot leak.

4. **Generate manifests from one descriptor.** A single model holding name/version/description/keywords/agent-list/host-capabilities renders each host's manifest. Count drift, keyword drift, the `./` prefix, and shape coupling all collapse into one rendered output. Then **tighten** each host schema to pin the exact intended shape (and delete `hooks`/`mcpServers`/`lspServers` from the schemas — they are auto-discovered and forbidden in the manifest). Move path/shape validation from `scripts/check.py` into the shipped `check`.

5. **Extract command fragments.** The FR-012 / dry-run / agent-mapping stanzas (17× duplicated) become `fragments/` referenced by an `{{> fragment }}` include at projection time. Centralize the project_type→architect map in one data table.

6. **Consolidate skills + reclassify (see §7 for the token rationale).** Merge the duplicate pairs (`controllers`→`controller-patterns`, `scalar`→`openapi-scalar`), make `cqrs-basics` a decision-guide that links to `cqrs/`, fix the `when_to_use`=`description` no-op, fix the broken `event-catalogue` reflection, and route the undocumented `grpc/` subdir to a real agent.

7. **Fix rule delivery (the §4.4 cure).** Per host: Claude → `dotnet-ai init` writes domain rules into the project `.claude/rules/*.md` **with `paths:` frontmatter** (the native JIT path) and backs *enforcement-grade* rules (security, private-setters) with a **PreToolUse hook** that emits `additionalContext` — plus generate-and-run the NetArchTest by default so a violation fails the build. Cursor → `.mdc` with `alwaysApply`/`globs` (already correct). Codex → universal conventions into `AGENTS.md`; flag domain-rule path-scoping as a known fidelity gap (Codex has no glob-scoped instructions). Copilot → `copilot-instructions.md`/`AGENTS.md` + `*.instructions.md` (`applyTo`).

### 6b. The CLI — recommended .NET 10 stack (and the trade-off resolved)

The .NET 10 research gives a concrete, opinionated, AOT-capable stack (all packages target net8.0+, so net10.0 is supported):

| Concern | Python today | Recommended .NET 10 | Why |
|---|---|---|---|
| CLI parsing | typer | **System.CommandLine 2.0.x** (stable 2.0.8, 2026-05-12) | first-party, trim/AOT-friendly; `SetAction` (not `SetHandler`) |
| Terminal UI | rich | **Spectre.Console** (standalone, not Spectre.Console.Cli) | direct `rich` analog; tables/prompts/progress |
| Templating | jinja2 | **Scriban** (7.2.3, AOT-safe via `ScriptObject`) | **the single hardest port** — Scriban Liquid ≠ Jinja2; filters must be reimplemented |
| Config (JSON) | pyyaml/json | **System.Text.Json source-gen** | reflection-free → AOT |
| Config (YAML) | pyyaml | **YamlDotNet + Vecc static generator** | **AOT crux**: plain YamlDotNet breaks under AOT; or move config to JSON |
| Validation | pydantic v2 | **`[OptionsValidator]` source-gen + DataAnnotations** | reflection-free pydantic analog; avoid FluentValidation if AOT matters |
| Token counting | (none) | **Microsoft.ML.Tokenizers** (`TiktokenTokenizer`) | first-party; enforces budgets in `check` — see §7 |
| Testing | pytest | **xUnit v3** (or TUnit for AOT-built tests) | xUnit v3 has Native-AOT guidance (2026-03-25) |
| Distribution | pip | **`dotnet tool` framework-dependent baseline + per-RID Native AOT** | .NET 10 GA'd self-contained/AOT tools (~2.5 MB, fast cold start) |

**Honest portability verdict:** ~70% of the CLI is trivial file-copy/scaffold/host-routing that ports directly to `System.IO`; `manifest.py`→`System.Security.Cryptography.SHA256`; subprocess probes→`System.Diagnostics.Process`. **There is no LLM tokenizer in the Python source** (the "token budget" is a line-count check in a script), so that dimension is a non-issue to port and an *upgrade* to add via `Microsoft.ML.Tokenizers`. The two genuinely hard items: **Jinja2 parity** (every `*.j2` and `config-template.yml` is hand-ported to Scriban/Liquid, with golden-output tests comparing to current Python output) and **pydantic's validator semantics** (split into STJ-binding + `[OptionsValidator]`-validation; the alias-on-read/canonical-on-write rules and `derive_architecture_branch` need manual reimplementation).

**The case for keeping/refactoring Python instead** is also real and must be stated: the CLI is mature, the 717 tests encode hard-won behavior, and **46% of test files couple to Python internals** and would need reimplementation, not re-running. Refactoring Python (collapse the duplicate models, decompose `cli.py`, pick one template engine, route writes through `hosts/`) delivers most of the maintainability win **at a fraction of the cost** and is a prerequisite for a clean port regardless.

---

## 7. Token / context & prompt-engineering strategy

The current baseline — `measure_always_on.py` reports ≥65% reduction vs a ~9000-token baseline, landing in a 2500-3000 band — **is real, but it measures the artifact corpus' line-counts, not the live plugin-native always-on cost.** Re-anchor on live measurement and fix three layer-mismatches the dated prompt-engineering source surfaces:

1. **The 124-skill always-on listing is the dominant unmeasured cost.** Every model-invocable skill's `description` is injected at session start, and that listing is capped at **~1% of the context window** (~2,000 tokens on a 200K model); on overflow Claude Code **drops** the least-used descriptions, silently degrading triggering (code.claude.com/docs/en/skills). 124 entries cannot fit ~13 tokens each, so the `measure_always_on.py` figure almost certainly **omits this layer**. **Action:** set `disable-model-invocation: true` on every side-effecting/deterministic command (the 27 commands — this *removes* their description from context entirely, zero idle cost, and fixes semantics so the model can't auto-fire a PR/deploy/codegen); reserve model-invocation for genuinely intent-triggered reference skills; consolidate the duplicate skills (§4.3); use `skillOverrides` name-only for low-priority entries. Re-measure with `/context` and `/doctor`.

2. **JIT rule loading must actually fire (the §4.4 fix is also a token fix).** The 68%-reduction story *depends on* domain rules loading only when a matching file is touched — but for plugin-native Claude they are not delivered to `.claude/rules/` at all (`cli.py:1334` is in the dead `else` branch). Until §6a-7 ships, the reduction is partly notional for Claude. Deliver domain rules with `paths:` frontmatter; narrow the two `**/*.cs` globs (`error-handling.md`, `performance.md`) that defeat JIT.

3. **Commands merged into skills.** "Custom commands have been merged into skills" in Claude Code — retire the separate `commands/` tree + its ≤200-line budget; express commands as skills (keep the ≤400-line SKILL.md budget, which matches the docs' "under 500 lines" tip).

**Additional levers:** (a) **sub-agent isolation** — ship `/verify`, `/review`, `/analyze`, docs generators as skills with `context: fork` + `agent: Explore`, with tight return contracts ("report only failures"); have the 13 specialist agents use the `skills:` frontmatter field to *preload* their convention skill rather than hoping the model loads it. (b) **dynamic context injection** — `!`git status --short`` inlined into `status`/`checkpoint` prompts grounds them in real state with fewer turns and *subsumes* the kit's current `render` substitution. (c) **MCP Tool Search** (default on) keeps codebase-memory-mcp's tools out of context until needed. (d) **Measurement as governance:** make `/context` the canonical always-on metric and bake it into CI/a self-check skill, replacing static line-counts as the *primary* signal — line counts are a proxy; the real constraints are the ~1% listing budget, the ~200-line CLAUDE.md adherence threshold, and per-skill compaction caps (5K/25K).

---

## 8. The .NET 10 decision

**Recommendation: YES — port the CLI to .NET 10, but as a second parallel track behind a contract-test gate, after the content re-architecture, and never from scratch.**

**Rationale (the discriminating criterion, resolved).** The criterion is: *does distribution-to-.NET-devs + dogfooding outweigh re-implementing a mature CLI and rewriting the ~46% of tests coupled to Python internals?* On its own, **no** — re-implementation is pure cost. But the win becomes worth it **once the port is decoupled from the content work and gated on language-neutral invariants**, because then:
- **Distribution is a genuine, audience-aligned win.** `dotnet tool install -g` is the native channel for .NET developers; .NET 10 GA'd self-contained/Native-AOT tools (~2.5 MB, fast cold start, no runtime dependency). pip is friction for the target user.
- **Dogfooding is credible and load-bearing.** A .NET dev-lifecycle tool written in .NET is its own best test case and signals seriousness.
- **The content work (§6a) is CLI-language-independent**, so doing it first means the port inherits a clean source-of-truth model rather than porting the current mess.
- **The 40 portable artifact/contract tests are the cross-language spec**, so the port is gated on behavior, not on Python internals.

**Risks (and mitigations):**
- *Jinja2 has no .NET equivalent.* → Hand-port to Scriban/Liquid with golden-output tests; budget it as real work.
- *YAML breaks under AOT.* → Adopt the Vecc static generator (config as classes, not structs) **or** move config to JSON. Decide config-format and distribution-mode *together*.
- *46% of tests need reimplementation.* → Port their **assertions/intent**, not their plumbing; keep the `T###` tags so .NET test names map 1:1 to the same spec IDs.
- *Native AOT cross-compile is unsupported.* → CI runs `dotnet pack` once per RID on a matching host; ship framework-dependent as the broad-reach baseline.
- *Splitting effort across two tracks.* → The contract-test gate (below) is what lets them proceed independently without one breaking the other.

**What must be preserved (non-negotiable):**
1. **A-011 no-network invariant** — re-expressed as a CLI/process-level network-deny assertion (not an AST scan), still covering init/check/migrate/render.
2. **The token budgets** — now enforced via `Microsoft.ML.Tokenizers` (`TiktokenTokenizer.CountTokens`) in `check`, an *upgrade* over line-counts.
3. **The 8-exit-code check contract (FR-031), the ≤18-file footprint (SC-001), and three-point runtime resolution (SC-003)** — these are the behavioral spec the .NET binary must satisfy.
4. **`manifest.py` and `upgrade.py` semantics** — port their design (sha256 integrity, atomic backup/rollback/rotate), do not redesign.

---

## 9. Phased migration plan

Two tracks, deliberately decoupled. **Track A ships value to all four tools regardless of CLI language. Track B is gated and optional.**

### Track A — Artifact re-architecture (tool-agnostic, do this first)

- **Phase A0 — Stabilize the bug, fix the current regressions.** Before anything structural: (i) fix the rule-delivery gap for plugin-native Claude (write domain rules to `.claude/rules/` with `paths:`; back security/private-setter rules with a PreToolUse `additionalContext` hook; generate+run the NetArchTest by default) — this is the maintainer's live pain from `issues/rule-enforcement-gap/`. (ii) Fix `test_budgets.py` stale globs (`rules/*.md`→`rules/**/*.md`; reconcile `agents/` vs `agents-claude/`) — the rule token budget is **currently unenforced** (the test asserts over an empty set). (iii) Fix the broken `event-catalogue` reflection sample.
- **Phase A1 — Single source-of-truth + projection engine.** Rename `agents-source/`→`artifacts/`; generalize `hosts/` into the projector with the rich `HostWriteResult` contract; make the fixture first-class; collapse to one `gen` entrypoint with a `git diff --exit-code` CI gate. Extend the drift suite to exercise the entrypoint and manifests (close the blind spot).
- **Phase A2 — Generate all manifests from one descriptor; tighten schemas; move validation into `check`.** Kills the 5-commit churn class permanently.
- **Phase A3 — Extract command fragments; consolidate skills + reclassify invocation; fix `when_to_use` no-ops.** Apply the §7 token strategy (`disable-model-invocation` on the 27 commands, merge duplicate skills, re-measure with `/context`).
- **Phase A4 — Per-host delivery polish.** Codex `AGENTS.md` for conventions; Copilot single-manifest reuse via `.claude-plugin/` auto-detect (audit `${CLAUDE_PLUGIN_ROOT}` first) + render-track retained for the cloud agent; Cursor `.mdc` (already correct). Add the cross-manifest consistency test (agent count, keywords, version) so drift fails CI.
- **Phase A5 — Planning hygiene.** Archive content dumps (14/15/18); reconcile `01-vision.md`/`12-version-roadmap.md`; document the 14th agent and the Codex/Copilot render-once asymmetry.

### Track B — .NET 10 CLI port (parallel, gated)

- **Phase B0 — Refactor Python first (prerequisite, also valuable standalone).** Collapse the duplicate models to one-per-file; decompose `cli.py` into per-verb service modules; pick **one** template engine; route writes through `hosts/`; delete the dead `copy_agents()` and unreachable host-gate branches; hoist `PLUGIN_NATIVE_HOSTS` to one module. This makes the port a translation, not a redesign.
- **Phase B1 — Establish the contract gate.** Promote A-011, the token budgets, FR-031, SC-001/003 into a **language-neutral acceptance suite** (the 40 bucket-A tests + CLI black-box tests run against *either* binary). Add CLI tests for the under-covered commands (`render`: 2 files, `detect`: 1, `learn`: 0) so the .NET impl has acceptance criteria.
- **Phase B2 — Port the trivial 70%** (file-copy/scaffold/host-routing, `manifest`, `upgrade`, subprocess probes) behind the gate.
- **Phase B3 — Port the hard 30%** (Jinja2→Scriban with golden-output tests; pydantic→STJ-source-gen + `[OptionsValidator]`; decide YAML-vs-JSON + AOT together).
- **Phase B4 — Distribution.** Ship framework-dependent `dotnet tool` baseline + per-RID Native AOT; add `marketplace.json` for all four tools so onboarding is `/plugin install` rather than pip.

### Do-not-do / risk list

- **Do not rewrite from scratch.** It discards 717 tests, the invariant suite, and the working `hosts/` architecture for zero capability gain.
- **Do not ship agent teams or dynamic workflows as a hard dependency.** Both are experimental/research-preview (the workflows feature is ~2 days old per RESEARCH-2); teams config is runtime state with no shippable manifest field. Ship subagent *definitions*; let teams/workflows compose them at runtime, opt-in.
- **Do not assume LSP for Codex or Cursor.** It does not exist agent-facing `[ungrounded]`. Only build LSP features for Claude Code (and Copilot plugins, Preview).
- **Do not start the .NET port before Track A and Phase B0/B1.** Porting the current mess, or porting without the contract gate, reproduces the drift in a second language.
- **Do not let the rich .NET-stack research turn this into a greenfield CLI design.** The high-value rebuild is the content layer; the CLI is a translation.
- **Do not re-assert "68% always-on reduction" or "Copilot is render-only" without re-verification** — the former measures the wrong layer, the latter is now false for IDE/CLI.

---

## 10. Open questions for the maintainer

1. **Rule delivery for plugin-native hosts:** confirm the intended behavior — should `dotnet-ai init` write domain rules into the project `.claude/rules/` (with `paths:` frontmatter) for Claude? Today the `copy_rules` call is in a dead `else` branch (`cli.py:1324-1334`) and does not run for plugin-native Claude. Is that intentional (rely on hooks only) or the bug the field report describes?
2. **Enforcement philosophy:** should convention enforcement be advisory (current: hooks `exit 0`) or deterministic (generate + run NetArchTest + `severity=error` `.editorconfig` so violations fail the build)? The field report argues for deterministic; this is a product decision.
3. **The fixture:** keep `dotnet-ai-architect` as a routed-but-excluded fixture, or move it out of `artifacts/` to `tests/fixtures/` entirely? The latter fixes the Codex/Copilot leak by construction.
4. **Config format vs AOT:** keep YAML (requires the Vecc static generator + class-only models) or move to JSON (frictionless STJ source-gen) for the .NET port? Decide with distribution mode.
5. **Scope of the .NET port:** full parity, or only the genuinely per-solution no-network work (init/detect/migrate + writing `.dotnet-ai-kit/*` + project `.claude/settings.json`/`.claude/rules/`), leaving commands/skills/agents to the plugin install path?
6. **Copilot single-manifest reuse:** is the team willing to depend on a Preview feature (`.claude-plugin/` auto-detect) for IDE/CLI, keeping render-to-files only for the cloud agent — or stay render-only everywhere until it GAs?
7. **Marketplace strategy:** project-scope install (committed to a .NET team repo) vs user-scope, and pinned `version` (stable channel) vs unpinned (ship-every-commit)?
8. **Skill count:** is 124 the right surface, or should the duplicate/overlap consolidation (§4.3) reduce it to ease the always-on listing budget — and which skills should be model-invocable vs user-only?
