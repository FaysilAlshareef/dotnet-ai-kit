# Final Merged Findings — Claude Version

Status: final merged findings, agreed by Claude and Codex
Date: 2026-05-17
Reviewers: Claude (Opus 4.7, 1M context) and Codex (gpt-5.5 xhigh)
Scope: plugin-native architecture refactor for v1.0 dotnet-ai-kit covering Claude Code, Codex CLI, Cursor, and GitHub Copilot
Release context: **pre-v1.0.0** — no public users, no backward-compat tax

This file is the Claude-side mirror of `issues/plugin-native-architecture/codex/final-merged-findings.md`. The decisions, commit order, quality estimates, and risks below are byte-identical in substance; only the voice and ordering of supporting prose differ. Read whichever you opened first. The executive-facing summary is at `issues/plugin-native-architecture/FINAL-REPORT.md`.

## Methodology

1. **Claude initial report** (`claude/REPORT.md`) — 703 lines covering Claude Code plugin spec, Codex CLI plugin spec, Cursor plugin spec, Copilot non-plugin model, plus full per-command before/after for the dotnet-ai-kit refactor. Maintainer accepted Copilot stays in scope and chose a single big-bang PR; those decisions were baked in before the cross-AI debate began.
2. **Codex initial report** (`codex/REPORT.md`) — 703 lines of independent analysis, narrower in scope per Codex's typical compactness, with concrete file:line + URL+line citations.
3. **Round 1 from Claude** (`discussion/round1-claude-to-codex.md`) — 10 contestable claims (C1–C10) framed to provoke evidence-based pushback.
4. **Round 1 reply from Codex** (`discussion/round1-codex-reply.md`) — 436 lines. Codex returned with corrections on Copilot agent format (`.github/agents/*.agent.md`, not root `AGENTS.md`), Cursor subagent support (Cursor marketplace confirms subagent packaging), Codex plugin compatibility (narrower than Claude's), Codex hooks GA (no feature flag), and the `AGENT_FRONTMATTER_MAP` state today (Claude-only entries; Cursor/Copilot are TODO comments).
5. **Round 2 from Claude** (`discussion/round2-claude-reply.md`) — accepted Codex's evidence-backed corrections on C1, C2, C6, C7, C10 and 14 of 16 new findings; flagged 5 residual disputes R1–R5.
6. **Round 2 sign-off from Codex** (`discussion/round2-codex-signoff.md`) — AGREED on all 5 residuals. Convergence achieved.

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

## Verified facts about today's dotnet-ai-kit codebase

| Fact | Source |
|--|--|
| `AGENT_FRONTMATTER_MAP` has only Claude entries; Cursor/Copilot are TODO comments | `src/dotnet_ai_kit/agents.py:63-83` |
| `SUPPORTED_AI_TOOLS` is frozen at `{"claude"}` | `src/dotnet_ai_kit/agents.py:57` |
| `AGENT_CONFIG["codex"]["agents_file"] = "AGENTS.md"` — collides with existing repo `AGENTS.md` | `src/dotnet_ai_kit/agents.py:51` + `AGENTS.md:1-15` |
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

## What's broken in dotnet-ai-kit today (drives the refactor)

1. **Triple-listing of every command** for Claude users: plugin `commands/do.md` exposes `dotnet-ai-kit:do`; init also writes `.claude/commands/dotnet-ai.do.md` (`dotnet-ai.do`) and `.claude/commands/dai.do.md` (`dai.do`). Three entries for one logical command.
2. **Skills double-listed**: 124 plugin skills load as `dotnet-ai-kit:<skill>`; init copies them to `.claude/skills/` where they reload unnamespaced. 248 entries per Claude project for 124 logical skills.
3. **Agents not plugin-served**: `.claude-plugin/plugin.json` lacks an `agents` field; universal frontmatter requires `AGENT_FRONTMATTER_MAP` transformation at init, which means `.claude/agents/` is the only loading path.
4. **Stale Jinja2 substitution**: `${Company}`, `${Domain}`, `${Side}`, `${ProjectType}` frozen at init time. Renames silently break.
5. **Stale `detected_paths`**: layer paths in `project.yml` captured at init; refactoring breaks all skill token resolution.
6. **Upgrade requires per-repo action**: plugin bug fixes don't reach a repo until its user runs `dotnet-ai upgrade`.
7. **csharp-ls miscategorized as MCP**: wrong primitive — LSP would push diagnostics in real-time during edits; MCP requires explicit invocation.
8. **No multi-tool plugin model**: only Claude is supported despite codebase intending all four tools; aspirational Cursor/Codex/Copilot paths produce broken or colliding output.
9. **Root `AGENTS.md` collision risk**: `AGENT_CONFIG["codex"]` was set to write to root `AGENTS.md`, which is the repo's own existing developer-guidance file.
10. **Packaging blocker**: wheel doesn't include `.codex-plugin/` or `.cursor-plugin/` directories.

## Final v1.0 architecture (converged)

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

hooks/hooks.json                    # SessionStart compact bootstrap (≤500 tokens)
                                    # PreToolUse runtime arch-profile (reads project.yml at fire-time)
                                    # existing 4 hooks unchanged

.mcp.json                           # codebase-memory-mcp only (after csharp-lsp lands)
plugin.json dependencies:           # csharp-lsp (paired with check binary validation)
pyproject.toml                      # updated wheel includes for all three manifest dirs
```

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

### CLI behavior changes

| Command | New behavior |
|--|--|
| `init` | Plugin tools: 3-file generator. Copilot adds `.github/*` renders. ~10 files vs ~180 today. |
| `upgrade` | Plugin tools: near no-op (validates config schemas; user runs `/plugin update`). `upgrade --copilot` re-renders GitHub-native files using current plugin source + project.yml. |
| `configure` | Multi-host UI. No copy step for plugin tools. |
| `check` | Validates: plugin install per configured host, `csharp-ls` binary, `project.yml` schema + detected paths, Copilot render freshness, manifest hash integrity. |
| `migrate` (NEW) | Manifest-driven cleanup using existing hash data. Classifies clean vs user-modified files. Moves clean managed files to `.dotnet-ai-kit/backups/migrate/<timestamp>/` with 3-keep rotation. Preserves user-modified files unless explicitly selected. **Does not re-render** Copilot files — that's `upgrade --copilot`. |
| `render <skill\|rule>` (NEW) | Resolves runtime tokens against current `project.yml` and prints what Claude would see. Restores inspectability lost when init stops pre-rendering. |
| `extension-*` | Unchanged (extensions subsystem out of scope). |
| `init --force` | Detects shadowed artifacts and prints `dotnet-ai migrate` invocation. Does NOT auto-migrate (preserves no-silent-cleanup rule). |

### Agent generation strategy

- One markdown body per logical agent in `agents/<name>.md` (source of truth)
- `src/dotnet_ai_kit/agent_generators.py` with explicit per-host generator functions: `generate_claude_agent()`, `generate_cursor_agent()`, `generate_copilot_agent()`
- `AGENT_FRONTMATTER_MAP` deleted; current Claude-only mapping at `src/dotnet_ai_kit/agents.py:63-83` was earning nothing for Cursor/Copilot anyway
- Tests assert no unsupported fields leak per host and no `skills:` preload regression

### Rule classification (converged 5/11 split)

**Conventions** (always-on; referenced from skill bodies via `${CLAUDE_PLUGIN_ROOT}/rules/conventions/`):
1. `async-concurrency.md` — broad `**/*.cs` correctness
2. `coding-style.md` — C# basics
3. `existing-projects.md` — detect-before-generate meta-principle
4. `security.md` — always-on
5. `tool-calls.md` — AI behavior governance

**Domain** (JIT-loaded; referenced from relevant skills):
1. `api-design.md` — Controllers/Endpoints/Program.cs
2. `architecture.md` — Microservice/Generic branches; profile-like
3. `configuration.md` — Options-pattern code
4. `data-access.md` — Infrastructure/Persistence/Repositories
5. `error-handling.md` — has architecture branches (Codex's correction; moved out of always-on)
6. `localization.md` — niche
7. `multi-repo.md` — microservice multi-repo only
8. `naming.md` — needs runtime `${Company}/${Domain}` substitution (Codex's correction)
9. `observability.md` — Logging/Telemetry
10. `performance.md` — broad but not startup-necessary (Codex's correction)
11. `testing.md` — tests/

Token math: convention bucket ≈ 5 × ~80 lines = ~400 lines, ~3000 tokens (after trimming for compact SessionStart bootstrap). Domain bucket loaded only on relevance. Net always-on cost drops from ~9000 → ~2500-3000 tokens.

### SessionStart hook redesign

- Target: **≤500 tokens** stdout
- Content: compact bootstrap index (project.yml pointer, `dotnet-ai check` reminder, lazy-load instruction, current architecture profile *name*)
- NOT: concatenated 5000+ tokens of rule bodies (the token-burn precedent showed this defeats lazy loading)
- Convention rules reach context via skill body references using `${CLAUDE_PLUGIN_ROOT}` paths, not SessionStart injection

## Commit order — 15 commits in a single PR

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

## Quality impact estimates

| Lever | Direction | Magnitude |
|--|--|--|
| Skill selection accuracy (Claude) | + | 248 → 124 entries |
| Command selection accuracy (Claude) | + | 3 → 1 entries per command |
| Always-on context cost | + | ~9000 → ~2500-3000 tokens |
| Customization fidelity | + | Eliminates Jinja-staleness silent failure mode |
| Detected-paths accuracy | + | Read at invocation; survives layer renames |
| Plugin update propagation | + | Single `/plugin update` reaches all Claude/Codex/Cursor projects |
| Inspectability | − | Mitigated by `dotnet-ai render` |
| Drift across team repos | + | Eliminated for plugin tools |
| Copilot users | = | Same as today; render-time staleness via `check` + `upgrade --copilot` |
| `available skills` per-session size | + | Lean — only plugin entries; no duplicate `.claude/skills/` listing |

## Items deferred to v1.1

- `bin/dotnet-ai` launcher (spike result documented in FINAL; pending cross-platform verification)
- Codex native plugin agent support (revisit when Codex docs catch up)
- Cursor full subagent generation (gated on v1 spike result)
- Multi-repo activity monitor (spike justified but not bundled in v1)

## Items out of scope

- Extensions subsystem (maintainer direction)
- Per-project Copilot plugin support (no plugin host; render-time is the only path)

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

## Verification gates before merge

Three smoke tests, one per plugin host:
1. **Claude**: drop a Claude-native agent in `agents-claude/` with `agents` field in `.claude-plugin/plugin.json`. Verify `/agents` lists it as `dotnet-ai-kit:<name>`.
2. **Codex**: drop a SKILL.md in plugin `skills/`. Verify Codex CLI sees it after install.
3. **Cursor**: drop a subagent fixture per Cursor format. Verify Cursor lists it.

Plus per-host packaging tests: `pip install` from wheel must produce working `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` in the installed plugin directory.

## Sign-off

This Claude-side report is signed-off as the converged Claude position. The Codex-side mirror at `codex/final-merged-findings.md` carries the same decisions with Codex's voice. The cross-AI debate is closed; implementation can proceed.

Codex's explicit sign-off statement is preserved at `discussion/round2-codex-signoff.md`.
