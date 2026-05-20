# Final Merged Findings - Codex Version

Status: final merged findings, agreed by Claude and Codex
Date: 2026-05-17
Reviewers: Claude (Opus 4.7, 1M context) and Codex (gpt-5.5 xhigh)
Scope: plugin-native architecture refactor for v1.0 dotnet-ai-kit covering Claude Code, Codex CLI, Cursor, and GitHub Copilot
Release context: **pre-v1.0.0** - no public users, no backward-compat tax

This file is the Codex-side mirror of `issues/plugin-native-architecture/claude/final-merged-findings.md`. The decisions, commit order, quality estimates, and risks are byte-identical in substance; only the voice and ordering of supporting prose differ. Read whichever you opened first.

The executive-facing summary is at `issues/plugin-native-architecture/FINAL-REPORT.md`.

## Methodology

1. **Claude initial report** (`claude/REPORT.md`) - 703 lines covering the plugin host landscape, the current dotnet-ai-kit layout, and a proposed plugin-native refactor.
2. Claude's initial report covered Claude Code plugin primitives, Codex CLI plugin primitives, Cursor plugin packaging, GitHub Copilot's non-plugin customization model, and the before/after shape of dotnet-ai-kit commands, rules, skills, agents, hooks, MCP, and LSP.
3. The maintainer accepted two framing decisions before the cross-AI debate: Copilot stays in scope, and the v1.0 refactor ships as one big-bang PR with ordered commits.
4. **Codex initial report** (`codex/REPORT.md`) - 703 lines of independent analysis.
5. Codex's report was narrower in phrasing but heavier on specific `file:line` and URL+line citations.
6. **Round 1 from Claude** (`discussion/round1-claude-to-codex.md`) - 10 contestable claims, C1 through C10.
7. The point of Round 1 was not consensus language; it was to force the claims with the highest implementation risk into explicit, evidence-backed argument.
8. **Round 1 reply from Codex** (`discussion/round1-codex-reply.md`) - 436 lines.
9. Codex corrected the Copilot agent target: `.github/agents/*.agent.md`, not a root `AGENTS.md`.
10. Codex corrected Cursor support: Cursor marketplace material explicitly lists subagents as a packaged primitive.
11. Codex narrowed Codex CLI compatibility: documented plugin primitives are skills, MCP, hooks, apps, and assets, not native agents, LSP, monitors, settings, or `bin/`.
12. Codex corrected the hooks status: the May 2026 changelog makes hooks GA and shows `/hooks` browse/toggle support.
13. Codex corrected the current `AGENT_FRONTMATTER_MAP` state: it only contains Claude entries, with Cursor and Copilot left as TODO comments.
14. **Round 2 from Claude** (`discussion/round2-claude-reply.md`) accepted the evidence-backed corrections on C1, C2, C6, C7, and C10.
15. Claude also accepted 14 of 16 new Codex findings and reduced the open set to five residual disputes, R1 through R5.
16. **Round 2 sign-off from Codex** (`discussion/round2-codex-signoff.md`) agreed on all five residuals.
17. R1 settled the fate of `AGENT_FRONTMATTER_MAP`: delete it and replace it with explicit per-host generators.
18. R2 settled `bin/dotnet-ai`: record the spike result but defer the launcher to v1.1.
19. R3 settled `migrate` versus `upgrade --copilot`: cleanup and render-refresh are separate operations.
20. R4 settled Codex agents: no native Codex plugin agents in v1.0 without documentation or a passing smoke test.
21. R5 settled pre-v1.0 reasoning: the project can remove broken aspirational copy paths, but it cannot relax validation gates.
22. Convergence was achieved at the end of Round 2.
23. This mirror does not introduce a new position.
24. It restates the converged architecture in Codex's voice so either final-merged file can be used as the implementation source.

## Verified facts that drove the design

| Fact | Source |
|--|--|
| Claude Code plugin auto-discovers `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, `monitors/`, `bin/`, `settings.json`, `themes/` | `https://code.claude.com/docs/en/plugins-reference` lines 128-340 |
| Claude Code plugin manifest fields include `name`, `version`, `description`, `agents`, `skills`, `commands`, `hooks`, `mcpServers`, `lspServers`, `outputStyles`, `dependencies`, `userConfig`, `channels` | `https://code.claude.com/docs/en/plugins-reference` lines 365-485 |
| Claude Code plugin namespaces artifacts as `<plugin-name>:<artifact>` | `https://code.claude.com/docs/en/plugins-reference` lines 405-410 |
| Claude Code `${CLAUDE_PROJECT_DIR}` substitutes in skill/agent content, hook commands, MCP/LSP configs | `https://code.claude.com/docs/en/plugins-reference` lines 525-555 |
| Claude Code SessionStart hook stdout enters Claude's context | Live session evidence + `https://code.claude.com/docs/en/plugins-reference` lines 111-130 |
| Codex CLI plugin docs `.codex-plugin/plugin.json`, `skills/`, `.mcp.json`, `hooks/hooks.json`, `.app.json`, `assets/` | `https://developers.openai.com/codex/plugins/build` lines 811-836 |
| Codex CLI plugin docs do NOT cover `agents/`, LSP, `monitors/`, `settings.json`, `bin/` | Same source, by omission |
| Codex hooks general availability with `/hooks` browse | `https://developers.openai.com/codex/changelog` May 7-8 2026 entries |
| Cursor plugins package subagents | `https://cursor.com/blog/marketplace/` lines 268-273; `https://github.com/cursor/plugins` lines 288-297 |
| Cursor rules use `.mdc` format in plugin `rules/` directory or project `.cursor/rules/` | `https://cursor.com/docs/context/rules` |
| GitHub Copilot custom agents use `.github/agents/*.agent.md` | `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550 |
| GitHub Copilot custom instructions repo-wide is `.github/copilot-instructions.md` | `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 714-724 |
| GitHub Copilot path-scoped instructions are `.github/instructions/*.instructions.md` | Same source, lines 730-735 |
| Coderabbit plugin ships both `.claude-plugin/` and `.cursor-plugin/` manifests with shared `skills/`/`agents/`/`commands/` | Live disk inspection at `~/.claude/plugins/cache/claude-plugins-official/coderabbit/1.1.1/` |
| Official `csharp-lsp` plugin exists but still requires `csharp-ls` binary on PATH | `https://code.claude.com/docs/en/discover-plugins` lines 131-155 |

The design follows the documented host boundaries instead of assuming that all plugin hosts converge on Claude's superset.

Claude Code is the richest host.

Codex CLI has a documented plugin surface, but that surface is narrower than Claude's.

Cursor has plugin packaging and rule support, plus explicit marketplace language for subagents.

GitHub Copilot has no plugin host in this scope, so it remains a render target under `.github/`.

The evidence also fixes the LSP/MCP split.

`csharp-lsp` is the Claude plugin dependency.

`csharp-ls` remains the required executable.

That means the migration must add validation before removing the old MCP entry.

## Verified facts about today's dotnet-ai-kit codebase

| Fact | Source |
|--|--|
| `AGENT_FRONTMATTER_MAP` has only Claude entries; Cursor/Copilot are TODO comments | `src/dotnet_ai_kit/agents.py:63-83` |
| `SUPPORTED_AI_TOOLS` is frozen at `{"claude"}` | `src/dotnet_ai_kit/agents.py:57` |
| `AGENT_CONFIG["codex"]["agents_file"] = "AGENTS.md"` - collides with existing repo `AGENTS.md` | `src/dotnet_ai_kit/agents.py:51` + `AGENTS.md:1-15` |
| Root `AGENTS.md` already exists as repo-developer guidance | `AGENTS.md:1-66` |
| `init` writes commands, rules, skills, agents | `src/dotnet_ai_kit/cli.py:718-785` |
| `upgrade` re-copies commands, rules, skills, agents | `src/dotnet_ai_kit/cli.py:1430-1460` |
| `configure` re-copies commands, skills, rules, agents | `src/dotnet_ai_kit/cli.py:1953-2022` |
| Manifest collection tracks managed file paths and hashes | `src/dotnet_ai_kit/cli.py:399-438` |
| Upgrade backup rotation defaults to keep 3 | `src/dotnet_ai_kit/cli.py:505-537` |
| Upgrade detects user-modified files via hash | `src/dotnet_ai_kit/cli.py:1281-1316` |
| Linked secondary-repo deployment writes tooling | `src/dotnet_ai_kit/copier.py:882-1202` |
| Linked repos parse `project.yml` with nested-read bug pattern (same as fixed in 018) | `src/dotnet_ai_kit/copier.py:920-957` |
| Cursor implementation today concatenates everything into one `.cursor/rules/dotnet-ai-kit.mdc` | `src/dotnet_ai_kit/copier.py:231-272` |
| Codex implementation today emits root `AGENTS.md` | `src/dotnet_ai_kit/copier.py:276-317` |
| `pyproject.toml` packaging includes `.claude-plugin` but NOT `.codex-plugin` or `.cursor-plugin` | `pyproject.toml:48-60` |
| Interactive `configure` UI offers only Claude Code | `src/dotnet_ai_kit/cli.py:1879-1890` |
| `.mcp.json` ships csharp-ls and codebase-memory-mcp | `.mcp.json:1-15` |
| `.claude-plugin/plugin.json` has no `agents` field today | `.claude-plugin/plugin.json:1-24` |
| Tests assert Claude-only multi-tool support | `tests/test_agents.py:31-33` |

The current repository is not halfway through a working multi-host architecture.

It is Claude-first with several aspirational paths that either do not run because `SUPPORTED_AI_TOOLS` excludes them, or would produce incorrect output if enabled.

The Codex path is the highest collision risk because it targets the root `AGENTS.md`, and this repository already uses root `AGENTS.md` for developer guidance.

The Cursor path loses structure by flattening rules and commands into a single `.mdc` file.

The Claude path works, but it duplicates plugin-served artifacts into project-local directories.

The manifest and backup code are useful.

They should be reused for migration instead of introducing path heuristics.

## What's broken in dotnet-ai-kit today (drives the refactor)

1. **Triple-listing of every command** for Claude users.
2. The plugin `commands/do.md` exposes `dotnet-ai-kit:do`.
3. `init` also writes `.claude/commands/dotnet-ai.do.md`, exposing `dotnet-ai.do`.
4. `init` also writes `.claude/commands/dai.do.md`, exposing `dai.do`.
5. That is three entries for one logical command.
6. **Skills double-listed** for Claude users.
7. 124 plugin skills load as `dotnet-ai-kit:<skill>`.
8. `init` copies the same skills to `.claude/skills/`, where they reload unnamespaced.
9. The result is 248 listed entries for 124 logical skills.
10. **Agents are not plugin-served**.
11. `.claude-plugin/plugin.json` lacks an `agents` field.
12. Universal frontmatter is transformed only when project-local `.claude/agents/` files are copied.
13. That leaves `.claude/agents/` as the only loading path for agents today.
14. **Jinja2 substitution is stale by design**.
15. `${Company}`, `${Domain}`, `${Side}`, and `${ProjectType}` are frozen at init time.
16. If the project is renamed or reclassified later, generated content silently drifts.
17. **`detected_paths` is stale by design**.
18. Layer paths in `project.yml` are captured at init.
19. Refactors and folder renames break skill token resolution until manual refresh.
20. **Upgrade requires per-repo action**.
21. Plugin bug fixes do not reach initialized repos until each repo runs `dotnet-ai upgrade`.
22. That is exactly the drift a plugin architecture is supposed to avoid.
23. **`csharp-ls` is miscategorized as MCP**.
24. MCP requires explicit invocation.
25. LSP is the correct primitive for edit-time diagnostics and navigation.
26. **There is no working multi-tool plugin model**.
27. Only Claude is supported today.
28. Cursor, Codex, and Copilot paths exist in code but are either disabled, broken, colliding, or underspecified.
29. **Root `AGENTS.md` collision risk is concrete**.
30. `AGENT_CONFIG["codex"]` points at root `AGENTS.md`.
31. This repository already has a root `AGENTS.md` with repo guidance.
32. The new architecture must not write there.
33. **Packaging blocks non-Claude plugin hosts**.
34. The wheel includes `.claude-plugin/`.
35. The wheel does not include `.codex-plugin/` or `.cursor-plugin/`.
36. Any multi-host plugin plan is incomplete until package data includes all three manifest directories.

## Final v1.0 architecture (converged)

The final architecture is plugin-native for hosts that actually have a plugin model.

Claude, Codex, and Cursor get plugin manifests and shared root assets where their hosts can load them.

Copilot gets GitHub-native rendered files because there is no Copilot plugin host to install.

Project-local generated output is reduced to configuration, detection state, permissions merge, and Copilot renders.

Root `AGENTS.md` is user-owned and stays untouched.

### Plugin source repo layout

```
.claude-plugin/plugin.json         # Claude Code manifest, explicit agents listing
.codex-plugin/plugin.json          # Codex (skills+MCP+hooks only)
.cursor-plugin/plugin.json         # Cursor (skills+rules+subagent spike, UI metadata)

skills/                             # shared SKILL.md
commands/                           # shared bare-named markdown
agents/                             # source-of-truth markdown bodies
agents-claude/                      # generated at build by explicit generator
agents-cursor/                      # generated at build (if spike passes)
agents-copilot-templates/           # `.agent.md` rendering templates

rules/
  conventions/                      # 5 files: async-concurrency, coding-style,
                                    #          existing-projects, security, tool-calls
  domain/                           # 11 files: api-design, architecture, configuration,
                                    #           data-access, error-handling, localization,
                                    #           multi-repo, naming, observability,
                                    #           performance, testing
  profiles/                         # architecture profiles by project_type
  cursor/*.mdc                      # generated Cursor rule format

hooks/hooks.json                    # SessionStart compact bootstrap (<=500 tokens)
                                    # PreToolUse runtime arch-profile (reads project.yml at fire-time)
                                    # existing 4 hooks unchanged

.mcp.json                           # codebase-memory-mcp only (after csharp-lsp lands)
plugin.json dependencies:           # csharp-lsp (paired with check binary validation)
pyproject.toml                      # updated wheel includes for all three manifest dirs
```

The key boundary is explicit.

`agents/` remains the human-maintained source body.

Host-native generated folders are build outputs.

Shared `skills/` remain shared where hosts can consume them.

Rules split into always-on conventions and just-in-time domain material.

The MCP file retains only actual MCP servers after the LSP migration is validated.

### Per-solution files

For Claude / Codex / Cursor users:

- `.dotnet-ai-kit/config.yml`
- `.dotnet-ai-kit/project.yml`
- `.claude/settings.json` (permissions merge only)

Additional for Copilot users:

- `.github/copilot-instructions.md`
- `.github/instructions/<scope>.instructions.md`
- `.github/agents/<name>.agent.md`

Root `AGENTS.md` stays untouched as repo-developer guidance.

This is the main file-count reduction.

Plugin-host users no longer get copied commands, copied skills, copied agents, and copied rules in every solution.

Copilot remains rendered because Copilot is not a plugin host.

The rendered Copilot files are still managed and can be checked for freshness.

### CLI behavior changes

| Command | New behavior |
|--|--|
| `init` | Plugin tools: 3-file generator. Copilot adds `.github/*` renders. ~10 files vs ~180 today. |
| `upgrade` | Plugin tools: near no-op (validates config schemas; user runs `/plugin update`). `upgrade --copilot` re-renders GitHub-native files using current plugin source + project.yml. |
| `configure` | Multi-host UI. No copy step for plugin tools. |
| `check` | Validates: plugin install per configured host, `csharp-ls` binary, `project.yml` schema + detected paths, Copilot render freshness, manifest hash integrity. |
| `migrate` (NEW) | Manifest-driven cleanup using existing hash data. Classifies clean vs user-modified files. Moves clean managed files to `.dotnet-ai-kit/backups/migrate/<timestamp>/` with 3-keep rotation. Preserves user-modified files unless explicitly selected. **Does not re-render** Copilot files - that's `upgrade --copilot`. |
| `render <skill\|rule>` (NEW) | Resolves runtime tokens against current `project.yml` and prints what Claude would see. Restores inspectability lost when init stops pre-rendering. |
| `extension-*` | Unchanged (extensions subsystem out of scope). |
| `init --force` | Detects shadowed artifacts and prints `dotnet-ai migrate` invocation. Does NOT auto-migrate (preserves no-silent-cleanup rule). |

`init` becomes host-aware setup, not a bulk copy engine.

`upgrade` stops pretending to be a plugin update path for plugin hosts.

`check` absorbs the validation that used to be hidden in copy-time side effects.

`migrate` is cleanup only.

`upgrade --copilot` is render refresh only.

`render` gives maintainers and users a way to inspect runtime-expanded skill and rule content without putting stale expansions back on disk.

### Agent generation strategy

- One markdown body per logical agent in `agents/<name>.md` (source of truth)
- `src/dotnet_ai_kit/agent_generators.py` with explicit per-host generator functions: `generate_claude_agent()`, `generate_cursor_agent()`, `generate_copilot_agent()`
- `AGENT_FRONTMATTER_MAP` deleted; current Claude-only mapping at `src/dotnet_ai_kit/agents.py:63-83` was earning nothing for Cursor/Copilot anyway
- Tests assert no unsupported fields leak per host and no `skills:` preload regression

The generator model is deliberately explicit.

There is no generic runtime map that claims host neutrality while encoding only Claude.

Each host gets named output logic.

Each host gets tests for its allowed fields.

Claude's previous `skills:` preload regression remains specifically covered.

Cursor generation depends on the v1 spike.

Copilot generation targets `.github/agents/*.agent.md`.

Codex native plugin agents are not part of v1.0.

### Rule classification (converged 5/11 split)

**Conventions** (always-on; referenced from skill bodies via `${CLAUDE_PLUGIN_ROOT}/rules/conventions/`):

1. `async-concurrency.md` - broad `**/*.cs` correctness
2. `coding-style.md` - C# basics
3. `existing-projects.md` - detect-before-generate meta-principle
4. `security.md` - always-on
5. `tool-calls.md` - AI behavior governance

**Domain** (JIT-loaded; referenced from relevant skills):

1. `api-design.md` - Controllers/Endpoints/Program.cs
2. `architecture.md` - Microservice/Generic branches; profile-like
3. `configuration.md` - Options-pattern code
4. `data-access.md` - Infrastructure/Persistence/Repositories
5. `error-handling.md` - has architecture branches (Codex's correction; moved out of always-on)
6. `localization.md` - niche
7. `multi-repo.md` - microservice multi-repo only
8. `naming.md` - needs runtime `${Company}/${Domain}` substitution (Codex's correction)
9. `observability.md` - Logging/Telemetry
10. `performance.md` - broad but not startup-necessary (Codex's correction)
11. `testing.md` - tests/

Token math: convention bucket ~= 5 x ~80 lines = ~400 lines, ~3000 tokens after trimming for compact SessionStart bootstrap.

Domain bucket loads only when relevant.

Net always-on cost drops from ~9000 tokens to ~2500-3000 tokens.

This split is intentionally smaller than Claude's first proposal.

`error-handling.md` is not always-on because it contains architecture-specific branches.

`naming.md` is not always-on because it depends on runtime company/domain substitution.

`performance.md` is broad, but broad is not the same as startup-critical.

### SessionStart hook redesign

- Target: **<=500 tokens** stdout
- Content: compact bootstrap index (project.yml pointer, `dotnet-ai check` reminder, lazy-load instruction, current architecture profile *name*)
- NOT: concatenated 5000+ tokens of rule bodies (the token-burn precedent showed this defeats lazy loading)
- Convention rules reach context via skill body references using `${CLAUDE_PLUGIN_ROOT}` paths, not SessionStart injection

SessionStart should orient the model.

It should not preload the rule corpus.

The hook can name the active architecture profile and point at current project metadata.

It should keep the context budget available for the user task.

When a skill needs conventions, the skill body references the plugin-root rule files.

When a task needs a domain rule, that rule is loaded on relevance.

## Commit order - 15 commits in a single PR

Branch: `019-plugin-native-architecture` (or maintainer's choice).

| # | Commit | Files touched |
|--|--|--|
| 1 | Expand `SUPPORTED_AI_TOOLS` + multi-host config tests | `agents.py`, `tests/test_agents.py` |
| 2 | Update `pyproject.toml` packaging includes | `pyproject.toml` |
| 3 | Add three manifest twins | `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json` |
| 4 | Claude plugin-native init (drop `.claude/commands/`, `.claude/skills/`, `.claude/agents/` copies) | `cli.py`, `copier.py` |
| 5 | Codex documented primitives (skills/MCP/hooks via `.codex-plugin/`) | `copier.py`, drop `copy_commands_codex` |
| 6 | Cursor rules + subagent spike (one agent fixture) | `copier.py`, drop `copy_commands_cursor` blob path |
| 7 | Copilot GitHub-native render (`.github/*.instructions.md`, `.github/agents/*.agent.md`) | `copier.py`, new renderers |
| 8 | `project.yml` JSON schema + validation | `models.py`, plugin `schemas/` |
| 9 | `check` host-specific validations including `csharp-ls` binary | `cli.py` |
| 10 | Manifest-driven `migrate` command + backup rotation | `cli.py` (new command) |
| 11 | `csharp-lsp` plugin dependency added | `.claude-plugin/plugin.json` |
| 12 | Remove `csharp-ls` from `.mcp.json` (only after step 11 verified in CI) | `.mcp.json` |
| 13 | SessionStart compact bootstrap + PreToolUse runtime arch-profile | `hooks/hooks.json`, new hook scripts |
| 14 | Rules reclassification (5 conventions / 11 domain) + skill body references | `rules/`, all SKILL.md files |
| 15 | Docs, migration guide, README, planning/ | `README.md`, `CLAUDE.md`, `planning/`, new `docs/migration-v1.md` |

The order matters.

Packaging follows supported-tool expansion before host behavior depends on it.

Host manifests land before per-host init behavior is changed.

Copilot rendering lands before schema/check work, because check needs something concrete to validate.

`check` lands before the LSP switch.

The MCP removal is after both the plugin dependency and binary validation gate.

Rules and hooks land late because they rely on the new plugin-native loading model.

Docs land last so they describe the actual implementation rather than the intended one.

## Quality impact estimates

| Lever | Direction | Magnitude |
|--|--|--|
| Skill selection accuracy (Claude) | + | 248 -> 124 entries |
| Command selection accuracy (Claude) | + | 3 -> 1 entries per command |
| Always-on context cost | + | ~9000 -> ~2500-3000 tokens |
| Customization fidelity | + | Eliminates Jinja-staleness silent failure mode |
| Detected-paths accuracy | + | Read at invocation; survives layer renames |
| Plugin update propagation | + | Single `/plugin update` reaches all Claude/Codex/Cursor projects |
| Inspectability | - | Mitigated by `dotnet-ai render` |
| Drift across team repos | + | Eliminated for plugin tools |
| Copilot users | = | Same as today; render-time staleness via `check` + `upgrade --copilot` |
| `available skills` per-session size | + | Lean - only plugin entries; no duplicate `.claude/skills/` listing |

These are estimates, not benchmark claims.

The strongest expected gains come from removing duplicate artifacts and stale project-local expansions.

The main tradeoff is inspectability.

Pre-rendered files are easy to open, even when stale.

Runtime resolution is fresher, but less visible.

`dotnet-ai render <skill|rule>` is the mitigation.

Copilot users are neutral, not improved by plugin update propagation, because Copilot has no plugin host.

Their staleness risk is handled through `check` and `upgrade --copilot`.

## Items deferred to v1.1

- `bin/dotnet-ai` launcher (spike result documented in FINAL; pending cross-platform verification)
- Codex native plugin agent support (revisit when Codex docs catch up)
- Cursor full subagent generation (gated on v1 spike result)
- Multi-repo activity monitor (spike justified but not bundled in v1)

These are deferrals, not rejections.

`bin/dotnet-ai` needs a cross-platform plugin PATH story before it belongs in the v1.0 contract.

Codex native agents need either official documentation or a passing smoke test.

Cursor full agent generation depends on the one-fixture spike.

The monitor has value, but it is not required to remove the current duplicate-copy architecture.

## Items out of scope

- Extensions subsystem (maintainer direction)
- Per-project Copilot plugin support (no plugin host; render-time is the only path)

The extensions subsystem stays untouched in this PR.

Copilot remains in scope only as GitHub-native rendered files.

There is no per-project Copilot plugin system to implement.

## Risks and mitigations

| Risk | Mitigation |
|--|--|
| Big-bang 15-commit PR review burden | Commit-by-commit organization; each commit independently reviewable; pre-v1.0 means no rollback drag |
| `project.yml` missing/corrupt at runtime | JSON schema validation in `check`; safe defaults in skills; clear error messages |
| `csharp-ls` binary missing after MCP removal | `check` validates BEFORE step 12; CI gate prevents shipping |
| Cursor subagent spike fails | Documented as pending; full generation deferred to v1.1 |
| Codex hooks feature flag if any users still report it | Hooks now GA per May 2026 changelog; document if surfaces |
| Stale Copilot renders | `dotnet-ai check` reports freshness; `dotnet-ai upgrade --copilot` re-renders |
| Plugin update mid-session | Document `/reload-plugins` requirement |
| Untested cross-tool loader assumptions | Per-host smoke fixtures required as gate before step 12 |

The biggest process risk is review size.

The mitigation is not to split into independent PRs that can drift.

The mitigation is ordered commits with small, reviewable intent.

The biggest runtime risk is validation moving from copy time to load time.

That is why `check`, schema validation, smoke fixtures, and packaging tests are gates, not optional follow-ups.

The LSP switch is explicitly gated.

No implementation should remove `csharp-ls` from `.mcp.json` until the `csharp-lsp` dependency and binary validation have passed in CI.

## Verification gates before merge

Three smoke tests, one per plugin host:

1. **Claude**: drop a Claude-native agent in `agents-claude/` with `agents` field in `.claude-plugin/plugin.json`. Verify `/agents` lists it as `dotnet-ai-kit:<name>`.
2. **Codex**: drop a SKILL.md in plugin `skills/`. Verify Codex CLI sees it after install.
3. **Cursor**: drop a subagent fixture per Cursor format. Verify Cursor lists it.

Plus per-host packaging tests: `pip install` from wheel must produce working `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` in the installed plugin directory.

The smoke tests are intentionally host-specific.

They protect against treating documentation symmetry as loader symmetry.

The packaging tests protect against a common failure mode in this repository: adding source directories but forgetting wheel includes.

Step 12 in the commit order depends on these gates.

If a host smoke fixture fails, the corresponding host feature is either fixed before merge or deferred with the same explicitness as Codex agents and Cursor full subagent generation.

## Sign-off

This Codex-side report is signed off as the converged Codex position.

The Claude-side mirror at `claude/final-merged-findings.md` carries the same decisions with Claude's voice.

The cross-AI debate is closed.

Implementation can proceed using the 15-commit order above.

Codex's explicit sign-off statement is preserved at `discussion/round2-codex-signoff.md`.
