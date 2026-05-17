# dotnet-ai-kit: Plugin-Native Architecture Refactor — Claude Report

Status: initial Claude-side findings, ready for cross-AI debate with Codex
Date: 2026-05-17
Author: Claude (Opus 4.7, 1M context)
Branch target: next feature branch (post-018 token-burn merge)
Release context: **pre-v1.0.0** — no public users, no backward-compat tax
Predecessor: builds on the token-burn-optimization refactor (feature 018, merged in commit `63a532d`)
Companion: Codex's independent review will land at `issues/plugin-native-architecture/codex/REPORT.md`

**Sources verified:** official plugin docs ([code.claude.com/docs/en/plugins](https://code.claude.com/docs/en/plugins), [plugins-reference](https://code.claude.com/docs/en/plugins-reference), [developers.openai.com/codex/plugins/build](https://developers.openai.com/codex/plugins/build)), Cursor plugin spec ([github.com/cursor/plugins](https://github.com/cursor/plugins)), GitHub Copilot docs ([custom instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot), [custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)) + inspection of 6 real plugins on disk (`angular-development-assistant`, `code-review`, `hookify`, `skill-creator`, `example-plugin`, `coderabbit`).

---

## Decisions baked into this report

These are confirmed by the maintainer before this document was finalized:

1. **Multi-tool scope: all four tools supported at v1.0** (Claude Code, Codex, Cursor, GitHub Copilot).
2. **Agent style: keep universal frontmatter + `AGENT_FRONTMATTER_MAP` transformation.** Required because Copilot's `AGENTS.md` format diverges from the Claude-family format.
3. **Migration: single big-bang PR on one feature branch.** All changes ship together. No incremental rollout.
4. **Old init'd files: no silent cleanup.** New `dotnet-ai migrate` command (or equivalent) handles cleanup with explicit user confirmation; moves files to backup, doesn't delete.
5. **Extensions subsystem: out of scope** for this refactor.
6. **LSP migration**: bundled into the single PR (not standalone).

The "open questions" section at the bottom is intentionally removed — items are now decisions in Part 11.

---

## Part 1 — How Claude Code plugins actually work (verified)

### 1.1 Directory layout (auto-discovered when manifest is minimal)

| Directory / file | What it ships | Discovery |
|--|--|--|
| `.claude-plugin/plugin.json` | Manifest (only file allowed here) | Required for plugin identity; minimal manifest = name only |
| `skills/<name>/SKILL.md` | Skills (folder form) | **Auto-discovered**. Always scanned even if `skills` key set. |
| `commands/*.md` | Skills (flat-file form — same primitive as `skills/`) | **Auto-discovered** unless `commands` key in manifest overrides it |
| `agents/*.md` | Subagents | **Auto-discovered** unless `agents` key in manifest overrides it |
| `hooks/hooks.json` | Hook config | Default location; can be moved via `hooks` field |
| `.mcp.json` | MCP servers | Default location; can be moved |
| `.lsp.json` | LSP servers | Default location |
| `monitors/monitors.json` | Background watchers | Experimental |
| `output-styles/` | Output style files | Auto-discovered |
| `settings.json` | Plugin default settings (limited: `agent`, `subagentStatusLine`) | Auto-loaded |
| `bin/` | Executables added to Bash PATH | Auto-loaded |
| `themes/` | Color themes | Experimental |
| **NO `rules/` primitive** | Rules are **not** a plugin component type | Rules in *projects* live in `.claude/rules/*.md` and trigger the `InstructionsLoaded` event |

### 1.2 Namespacing

Plugin-shipped artifacts appear as **`<plugin-name>:<artifact-name>`** in `/agents`, available-skills lists, etc. Confirmed in this session: `angular-development-assistant:01-typescript-fundamentals`, `dotnet-ai-kit:add-aggregate`, `coderabbit:autofix`. Standalone `.claude/` artifacts appear **unnamespaced** (`/hello`).

### 1.3 Path-resolution variables (substituted in skill/agent content, hook commands, MCP/LSP configs)

| Variable | Resolves to |
|--|--|
| `${CLAUDE_PLUGIN_ROOT}` | Plugin install dir. Stable across a session; changes on plugin update. |
| `${CLAUDE_PLUGIN_DATA}` | Persistent state dir, survives updates: `~/.claude/plugins/data/<id>/` |
| `${CLAUDE_PROJECT_DIR}` | **The user's project root.** This is the key: skills/agents/hooks can read project-specific files (like `project.yml`) at runtime via this variable. |

### 1.4 Hook events (the ones that matter for us)

- `SessionStart` — fires once per session. Hook stdout **enters Claude's context**.
- `InstructionsLoaded` — fires when `CLAUDE.md` or `.claude/rules/*.md` is loaded.
- `PreToolUse` with `matcher`/`if` — fires before specific tool calls (e.g., `Edit(*.cs)`).
- `UserPromptSubmit` — fires before Claude sees the prompt.

### 1.5 Standalone vs plugin precedence

Per official migration guide: *"After migrating, you can remove the original files from `.claude/` to avoid duplicates. The plugin version will take precedence when loaded."*

This **confirms** today's per-solution copy creates duplicates Claude Code sees both. "Takes precedence" is for name collisions; both still exist as listed entries.

---

## Part 2 — How Codex CLI plugins actually work (verified)

Source: [developers.openai.com/codex/plugins/build](https://developers.openai.com/codex/plugins/build), confirmed by coderabbit plugin's `.cursor-plugin/` twin in `~/.claude/plugins/cache/`.

### 2.1 Directory layout

```
my-plugin/
├── .codex-plugin/
│   └── plugin.json          (Required: plugin manifest)
├── skills/<name>/SKILL.md    (Same format as Claude Code)
├── hooks/hooks.json          (Same schema as Claude Code)
├── .mcp.json                 (Same as Claude Code)
├── .app.json                 (Codex-specific: app/connector mappings)
└── assets/                   (Optional)
```

### 2.2 Compatibility with Claude Code

**Near-100% file format compatibility** between Claude Code and Codex plugins:
- Same SKILL.md format with YAML frontmatter (name, description)
- Same `hooks/hooks.json` schema
- Same `.mcp.json` MCP server format
- Path variables map: `${PLUGIN_ROOT}` in Codex ≈ `${CLAUDE_PLUGIN_ROOT}` in Claude Code (Codex documentation explicitly mentions `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA` for legacy compatibility)
- Codex even reads `.claude-plugin/marketplace.json` as a legacy-compatible marketplace location

### 2.3 Gotcha — plugin hooks gated

"Plugin hooks are off by default in this release; bundled hooks won't run unless `[features].plugin_hooks = true`." This is a feature flag in `~/.codex/config.toml`. Document this for users.

### 2.4 Agents

Codex documents "subagents" as a concept but does not detail a plugin-shipped agent format. Recommend testing — likely either auto-discovers from `agents/*.md` (like Claude Code) or doesn't load them at all. If the latter, agent functionality is Claude-Code-only for now.

### 2.5 Install location

`~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` — direct parallel to Claude Code's `~/.claude/plugins/cache/`.

---

## Part 3 — How Cursor plugins actually work (verified)

Source: [cursor/plugins GitHub](https://github.com/cursor/plugins), confirmed by coderabbit's `.cursor-plugin/plugin.json` on disk.

### 3.1 Directory layout

```
plugin-name/
├── .cursor-plugin/
│   └── plugin.json        # Per-plugin manifest
├── skills/                # Agent skills (SKILL.md format)
├── rules/                 # Cursor rules (.mdc files)
├── mcp.json              # MCP server definitions
```

### 3.2 Key differences from Claude Code

- Manifest dir: `.cursor-plugin/` (not `.claude-plugin/`)
- Manifest has UI-presentation fields: `displayName`, `logo`, `category`, `tags`
- Rules use **`.mdc` files** (Cursor's Markdown-with-frontmatter format) with activation modes: Always Apply, Auto Attached (globs), Agent Requested, Manual
- Skill format **compatible** with Claude Code (SKILL.md + frontmatter)
- Agents not documented as first-class plugin component

### 3.3 Coderabbit's cross-platform pattern (the model to copy)

The coderabbit plugin (`~/.claude/plugins/cache/claude-plugins-official/coderabbit/1.1.1/`) ships **one source repo with both `.claude-plugin/` and `.cursor-plugin/` manifests** sharing the same `skills/`, `agents/`, `commands/` directories. The Cursor manifest adds UI metadata (`displayName`, `logo`); the Claude manifest is minimal. Same content, two thin wrappers. This is the gold pattern.

---

## Part 4 — How GitHub Copilot custom instructions work (verified)

Source: [GitHub Copilot CLI custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions), [custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli).

### 4.1 Copilot has NO plugin system

Per-project files only. No marketplace, no namespacing, no central distribution. The customization primitives are:

| Artifact | Location | Purpose |
|--|--|--|
| Custom instructions | `.github/copilot-instructions.md` (repo) or `$HOME/.copilot/copilot-instructions.md` (user) | Rules equivalent — always-loaded context |
| Custom agents | `AGENTS.md` files in repo root, cwd, or dirs listed in `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` | Agent-equivalent — specific structure |
| Agent hooks | Public preview, configured via Copilot settings | Hook events at session points |
| MCP servers | Configured separately, location varies by Copilot client | MCP integration |

### 4.2 What this means for dotnet-ai-kit

For Copilot users, init **must** continue to write files into the project. There is no plugin host to serve from globally. The existing copy infrastructure in `copier.py`/`extensions.py` stays alive for the Copilot code path.

---

## Part 5 — What's broken in dotnet-ai-kit today

### 5.1 Triple-listing of every command (Claude Code)

Plugin source has `commands/do.md`. Plugin exposes it as `dotnet-ai-kit:do`. But `dotnet-ai init` also writes:
- `.claude/commands/dotnet-ai.do.md` → exposed as `dotnet-ai.do` (unnamespaced)
- `.claude/commands/dai.do.md` → exposed as `dai.do` (unnamespaced)

Net per init'd project: **3 listed entries for the same command**.

### 5.2 Skills double-listed (Claude Code)

124 skills in plugin `skills/` are loaded as `dotnet-ai-kit:<skill>`. Init copies all 124 (Jinja-rendered) to `.claude/skills/` where they reload **unnamespaced**. Every init'd Claude Code project has 248 entries for 124 logical skills.

### 5.3 Agents not plugin-served

`plugin.json` has no `agents` field today. Agents ship with universal frontmatter (`role`, `expertise`, `complexity`, `max_iterations`) — Claude Code's loader rejects these. The init-time `AGENT_FRONTMATTER_MAP` transformation in [agents.py:63-83](src/dotnet_ai_kit/agents.py) is the only reason agents work.

### 5.4 Stale Jinja2 substitution

Skills rendered with `${Company}`, `${Domain}`, `${Side}`, `${ProjectType}` at init time. Rename your domain → skills still reference the old name.

### 5.5 Stale `detected_paths`

`project.yml` captures layer paths at init. Refactoring renames a project → skill token resolution targets nonexistent paths.

### 5.6 Upgrade requires per-repo action

Bug fix in a skill ships in plugin v1.1, but every init'd project keeps the v1.0 render until `dotnet-ai upgrade` runs in that repo.

### 5.7 csharp-ls mis-categorized as MCP

`.mcp.json` ships `csharp-ls` as an MCP server. It's actually an LSP server. MCP requires explicit invocation; LSP pushes diagnostics in real-time during edits. Wrong primitive for the job.

### 5.8 No multi-tool plugin model

`.codex-plugin/` and `.cursor-plugin/` manifests don't exist. dotnet-ai-kit installs as a Claude Code plugin only despite the codebase intending multi-tool support.

---

## Part 6 — Target architecture (plugin-native + Copilot fallback)

### 6.1 The split

```
PLUGIN SOURCE REPO (one install path per plugin-host tool)
  .claude-plugin/plugin.json     ← Claude Code manifest
  .codex-plugin/plugin.json      ← Codex manifest (twin)
  .cursor-plugin/plugin.json     ← Cursor manifest (twin, +UI fields)
  
  skills/                         ← shared by Claude/Codex/Cursor (SKILL.md compatible)
  commands/                       ← bare names, no dotnet-ai./dai. prefix files
  agents/                         ← universal frontmatter source-of-truth
  agents-claude/                  ← Claude-native frontmatter (generated at build)
  agents-copilot/                 ← AGENTS.md files (generated at build)
  hooks/hooks.json                ← plugin-served for Claude/Codex
  rules/
    conventions/                  ← always-on rules (SessionStart hook)
    domain/                       ← reference rules (JIT loaded by skills)
    profiles/                     ← architecture profiles by project type
    cursor/*.mdc                  ← Cursor-format rules (generated at build)
  scripts/                        ← helpers: inject-rules.sh, render-profile.sh

PER-SOLUTION (what init writes)
  Claude / Codex / Cursor users:
    .dotnet-ai-kit/config.yml     ← unchanged
    .dotnet-ai-kit/project.yml    ← unchanged
    .claude/settings.json         ← permissions merge ONLY (hook is plugin-served)
    (no commands, no skills, no agents, no rules copied)
  
  Copilot users (add on top of above):
    .github/copilot-instructions.md  ← rendered from rules/conventions/ + project.yml
    AGENTS.md                         ← rendered from agents/ universal source
    .github/copilot-mcp.json          ← MCP config (if applicable)
```

### 6.2 How each artifact reaches each tool

| Artifact | Claude Code | Codex | Cursor | Copilot |
|--|--|--|--|--|
| Commands | Plugin-served namespaced | Plugin-served namespaced | Plugin-served namespaced | Per-project copy (already today) |
| Skills | Plugin-served, runtime token resolution | Plugin-served | Plugin-served | Embedded into instruction files |
| Agents | Plugin-served (Claude-native variant) | Plugin-served (same files) | Skip (not first-class) | Per-project `AGENTS.md` (Copilot variant) |
| Rules — conventions | SessionStart hook injects from plugin | SessionStart hook (gated by feature flag) | `.cursor-plugin/rules/*.mdc` | Aggregated into `.github/copilot-instructions.md` |
| Rules — domain | Referenced from skills via `${CLAUDE_PLUGIN_ROOT}` | Same | Auto-attached `.mdc` (via globs) | Embedded into instructions on-demand |
| Architecture profile | PreToolUse hook reads project.yml | Same (when hooks enabled) | Rule with glob activation | Section in copilot-instructions.md |
| Hooks (general) | Plugin-served (already today) | Plugin-served | Cursor doesn't expose hooks the same way | Copilot agent hooks (preview) |
| MCP servers | `.mcp.json` (plugin-served) | `.mcp.json` (plugin-served) | `mcp.json` (plugin-served) | Per-project copy |
| LSP | Dependency on `csharp-lsp` plugin | Likely same mechanism | Cursor uses VSCode LSP | N/A |

### 6.3 Single source of project-specific truth

`${CLAUDE_PROJECT_DIR}/.dotnet-ai-kit/project.yml` is read at runtime by plugin-served skills/hooks for Claude/Codex/Cursor. For Copilot, the same `project.yml` is read by `dotnet-ai upgrade` to re-render `.github/copilot-instructions.md` and `AGENTS.md`.

---

## Part 7 — Per-command before / after

### 7.1 CLI commands (`dotnet-ai *`)

| Command | NOW does | AFTER does | Why |
|--|--|--|--|
| `init` | Detects project. Writes `config.yml` + `project.yml`. Copies all 27 commands. Copies all 124 skills with Jinja2 rendering. Copies 13 agents. Copies 16 rules + profile. Merges permissions. Injects hook. ~180 files written. | Detects project. Writes `config.yml` + `project.yml`. Merges permissions into `.claude/settings.json`. **If `ai_tools` includes copilot:** renders `.github/copilot-instructions.md` + `AGENTS.md` (~10 files for Copilot). **For plugin tools:** 3 files total. | Plugin tools = 3 files; Copilot adds ~10 files. Down from ~180. |
| `detect` | Runs detection, writes `project.yml`. | Unchanged. `project.yml` is now load-bearing — plugin skills/hooks read it at runtime. | Detection itself sound; consumer changes. |
| `configure` | Interactive wizard. Optionally re-runs copy if command_style changes. | Interactive wizard. Triggers Copilot re-render only if Copilot is in `ai_tools`. No copy for plugin tools. | Removes staleness for plugin tools. |
| `upgrade` | Re-copies + re-renders everything for all tools. | **For plugin tools: near no-op** (validates config schemas; user must `/plugin update`). **For Copilot:** re-renders `.github/` files from current plugin source + `project.yml`. | Plugin updates flow automatically; Copilot uses existing render pipeline. |
| `check` | Validates copies match plugin source. | Validates `config.yml`/`project.yml` schemas. Checks plugins installed. Verifies `project.yml` paths still exist. For Copilot: validates rendered files are current. | Drift detection becomes "is project.yml stale" + "is Copilot output current". |
| `migrate` (NEW) | — | Detects shadowed files in `.claude/commands`, `.claude/skills`, `.claude/agents`, `.claude/rules` from prior init. Lists them. Asks confirmation per category. Moves to `.dotnet-ai-kit/backups/<timestamp>/` (not deletion). | Explicit cleanup with user consent. No silent file removal. Reversible. |
| `render <skill\|rule>` (NEW) | — | Resolves runtime tokens against current `project.yml` and prints what Claude would see. | Restores inspectability lost when init stops pre-rendering. |
| `extension-*` | Manages extensions. | Unchanged. | Extensions out of scope. |

### 7.2 Slash commands (the 27 `dotnet-ai.*` markdown files)

| Slash command | NOW | AFTER |
|--|--|--|
| `/dotnet-ai.do`, `/dai.do` | 3 entries visible to Claude (full-prefix copy + short-prefix copy + plugin). Jinja-frozen Company/Domain. | Single entry: `/dotnet-ai-kit:do`. Body uses `${CLAUDE_PROJECT_DIR}/.dotnet-ai-kit/project.yml` references at runtime. (Codex: same but with `${PLUGIN_ROOT}`/`${CWD}`.) (Cursor: namespace-loaded same way.) (Copilot: instructions embedded in `copilot-instructions.md`.) |
| `/dotnet-ai.add-aggregate` etc. | Pre-rendered ProjectType/Domain. Hardcoded layer paths. | Reads `project.yml` at invocation. Live paths. Fixes "renamed layer breaks scaffold" failure mode. |
| SDD lifecycle (specify, plan, tasks, implement, verify, review, pr) | Per-solution copies, drift across team's repos. | Plugin-served. Same content everywhere. Improvements roll out instantly. |
| Code-gen, session commands | Per-solution copies. | Plugin-served. |

### 7.3 Skills (124 SKILL.md files)

| Skill class | NOW | AFTER |
|--|--|--|
| Workflow skills | Copied + Jinja-rendered per solution. | Plugin-served. Body references `project.yml` at runtime. |
| Architecture skills | Same. | Plugin-served. References domain rules via `${CLAUDE_PLUGIN_ROOT}/rules/domain/`. |
| Detection skills | `${detected_paths.*}` rendered at init. | Plugin-served. Tokens resolved at invocation. |

### 7.4 Agents (13 files)

**Decision: keep universal frontmatter source-of-truth + `AGENT_FRONTMATTER_MAP`** (reversal of earlier draft). Required because Copilot's `AGENTS.md` format diverges from Claude-family.

| Now | After |
|--|--|
| Universal frontmatter source. `AGENT_FRONTMATTER_MAP` transforms to Claude format at init. Copied to `.claude/agents/`. | Universal frontmatter source remains. Build step generates: (a) Claude-native variants → `agents-claude/`, listed in `.claude-plugin/plugin.json` `agents` field; (b) Codex shares Claude-native files via `.codex-plugin/`; (c) Cursor skipped (no agents primitive); (d) Copilot `AGENTS.md` files in `agents-copilot/`, rendered to project at init time. |

### 7.5 Rules (16 files) — convention vs domain split

**Conventions** (always-on, ~8 files):

| File | Reason | Notes |
|--|--|--|
| `async-concurrency.md` | Applies to any C#; correctness-critical | Path `**/*.cs` |
| `coding-style.md` | C# basics; always relevant | Broad |
| `existing-projects.md` | Meta-principle ("detect before generate") | Foundational |
| `security.md` | Always-on | Broad |
| `tool-calls.md` | Governs AI behavior itself | Highest leverage |
| `error-handling.md` | Broad `**/*.cs` | Has profile-aware branches in body |
| `performance.md` | Broad `**/*.cs` | Anti-patterns to always avoid |
| `naming.md` | Always-on naming; needs `${Company}/${Domain}` runtime resolution | Special case |

**Domain reference** (JIT-loaded, ~8 files):

| File | Loaded by | Reason |
|--|--|--|
| `api-design.md` | `add-endpoint`, REST skills | Path-scoped to Controllers/Endpoints |
| `architecture.md` | Architecture skills, profile loader | Has Microservice/Generic branches; profile-like |
| `configuration.md` | `configure` skill, Options-pattern skills | Path-scoped |
| `data-access.md` | `add-entity`, EF/Dapper skills | Path-scoped to Infrastructure/Persistence/Repositories |
| `localization.md` | Localization skills only | Niche |
| `multi-repo.md` | Multi-repo coordination | Only in microservice multi-repo work |
| `observability.md` | Observability skills | Path-scoped to Logging/Telemetry |
| `testing.md` | `add-tests`, test skills | Path-scoped to tests/ |

Token math: convention bucket ≈ 8 × ~80 lines = ~640 lines (~5000 tokens) always-loaded. Domain bucket loaded only when relevant skill fires. Today's 16-always-loaded = ~9000 tokens. **Reduction ≈ 45%** in always-on rule cost.

### 7.6 Hooks (existing 6 files + 2 new)

Already plugin-served via `${CLAUDE_PLUGIN_ROOT}`. New hooks:

| Hook | Purpose | Trigger |
|--|--|--|
| `SessionStart: convention-rules-inject.sh` (NEW) | Concatenate `rules/conventions/*.md`, emit. | Session start |
| `PreToolUse: arch-profile-inject.sh` (REFACTORED) | Read `${CLAUDE_PROJECT_DIR}/.dotnet-ai-kit/project.yml`, pick profile, emit constraints. | Edit/Write `*.cs` |
| Existing (pre-bash-guard, pre-commit-lint, post-edit-format, post-scaffold-restore) | Unchanged | Same as today |

---

## Part 8 — Quality impact

| Quality lever | Today | After refactor (plugin tools) | Net effect |
|--|--|--|--|
| Skill selection accuracy | 248 entries × ambiguous namespacing per init'd Claude project | 124 namespaced entries | **+** Less confusion |
| Command selection accuracy | 3 entries per command | 1 entry per command | **+** Best in plugin tools |
| Context cost per turn | All listings + rules always loaded | Convention rules + 124 skills (domain rules JIT) | **+** ~30-40% reduction |
| Customization fidelity | Jinja frozen at init | Runtime substitution | **+** Eliminates silent failure mode |
| Detected-paths accuracy | Baked at init | Read at invocation | **+** Eliminates broken-path failures |
| Plugin update propagation | Per-repo `dotnet-ai upgrade` | `/plugin update` once for Claude/Codex/Cursor | **+** Predictability |
| Inspectability | `cat .claude/skills/X.md` shows rendered | Needs `dotnet-ai render` helper | **−** Mitigated by new command |
| Missing `project.yml` failure | N/A | New failure surface | **−** Mitigated with schema validation + safe defaults |
| Drift across repos | Real | Eliminated for plugin tools | **+** |
| Copilot users | Same as today | Same as today (per-project copy preserved) | **=** No regression |

---

## Part 9 — Risks (honest)

1. **`agents` auto-discovery vs explicit listing**: If `agents` field set in plugin.json, default dir is replaced not extended. Decide pattern (angular plugin lists explicitly; Anthropic plugins auto-discover). Recommend explicit listing.
2. **Codex plugin hooks disabled by default**: Document that users enable `[features].plugin_hooks = true` in `~/.codex/config.toml`. Without it, SessionStart and PreToolUse hooks don't fire.
3. **Cursor agents skip**: We're not shipping agents to Cursor users in v1. Document this; reconsider if Cursor adds first-class agent support.
4. **`project.yml` staleness**: today frozen at init; after refactor every skill depends on it. Mitigation: `dotnet-ai check` validates layer paths; `dotnet-ai detect --refresh` updates it.
5. **Plugin update mid-session**: hooks/MCP keep using old plugin dir until `/reload-plugins`. Document.
6. **No `rules` field in plugin.json**: SessionStart-hook injection is a workaround, not a sanctioned path. Acceptable; hookify plugin uses same pattern.
7. **Big-bang PR risk**: large surface area, harder to bisect issues. **Mitigation**: organize the branch into clean per-area commits even if shipping as one PR. Pre-v1.0 status reduces blast radius (no production users to break).
8. **Universal-frontmatter maintenance**: `AGENT_FRONTMATTER_MAP` stays alive because Copilot diverges. Acceptable tradeoff for keeping multi-tool reach.

---

## Part 10 — LSP servers, monitors, output styles

### 10.1 lspServers — yes, add via dependency

Today: `csharp-ls` ships as MCP server in `.mcp.json`. Wrong primitive — MCP is for callable tools; LSP is for push diagnostics during edits.

After: declare dependency on official `csharp-lsp` plugin:
```json
{
  "dependencies": [
    { "name": "csharp-lsp", "version": "^1.0.0" }
  ]
}
```

Remove `csharp-ls` from `.mcp.json` (keep `codebase-memory-mcp`). Quality win: instant diagnostics, hover info, go-to-definition during edits — without explicit invocation.

### 10.2 monitors — skip

Considered: `dotnet build`, test runner, sibling-repo git activity, `project.yml` change watch. None pass the "meaningfully changes quality" bar. LSP covers diagnostics; explicit invocations cover everything else cheaper. Cross-repo monitor is the only revisit candidate if multi-repo workflows become annoying.

### 10.3 outputStyles — skip

Wrong primitive for a dev productivity tool. Per-command output format belongs in the command's markdown body, not a global style.

### 10.4 Clean MCP/LSP split

```
.mcp.json                       → codebase-memory-mcp only
plugin.json dependencies        → csharp-lsp (provides LSP)
```

---

## Part 11 — Single-PR migration plan

**Branch**: `019-plugin-native-architecture` (or similar)

Per maintainer decision: one branch, one PR, all changes ship together. Pre-v1.0.0 release status means no backward-compat concerns and lower blast radius.

### 11.1 Commit organization (within the single PR)

Each item is a clean reviewable commit:

| # | Commit | Scope |
|--|--|--|
| 1 | Add multi-platform manifest twins | `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/plugin.json` |
| 2 | Add csharp-lsp dependency; remove csharp-ls from .mcp.json | LSP migration |
| 3 | Plugin-serve commands (drop full-prefix/short-prefix duplicates) | Stop copying `dai.*`/`dotnet-ai.*` files |
| 4 | Refactor skills to runtime token resolution | Skills read `project.yml` at invocation |
| 5 | Split rules into conventions/domain/profiles | Reorganize `rules/` directory |
| 6 | Add SessionStart convention-rules-inject hook | New hook in `hooks/hooks.json` |
| 7 | Refactor PreToolUse arch-profile hook to runtime | Reads `project.yml` at fire-time |
| 8 | Generate Claude-native + Copilot agent variants from universal source | Build step in CLI |
| 9 | Refactor `init` CLI: plugin tools = 3-file generator; Copilot = render path | Split logic in `cli.py` |
| 10 | Refactor `upgrade` CLI: near no-op for plugin tools | Validate-only |
| 11 | Add `dotnet-ai migrate` command | Explicit cleanup with backups |
| 12 | Add `dotnet-ai render <skill\|rule>` command | Inspectability |
| 13 | Cursor `.mdc` rules generator | Convert convention/domain rules to Cursor format |
| 14 | Update tests | Multi-manifest packaging, migrate, render, runtime resolution |
| 15 | Documentation | README, CLAUDE.md, planning/ |

### 11.2 Verification before merge

Three one-off tests to run before declaring done:

1. **Plugin-served agent discovery**: drop a Claude-native agent in plugin `agents/`, set `agents` field in `.claude-plugin/plugin.json`, confirm it appears as `dotnet-ai-kit:reviewer` in `/agents`.
2. **SessionStart hook payload size**: confirm ~2000 tokens of concatenated convention rules emit without truncation.
3. **Cross-tool init**: run `dotnet-ai init` on a test repo with all four `ai_tools` enabled; verify files written match the table in Part 7.1.

---

## Part 12 — Decisions log (resolving open questions)

| Original question | Decision | Rationale |
|--|--|--|
| Multi-tool scope going forward | All four tools (Claude, Codex, Cursor, Copilot) | Pre-v1.0; no reason to cut features arbitrarily. Plugin tools converge; Copilot uses existing copy code. |
| Agent frontmatter: universal vs per-tool native | Keep universal + `AGENT_FRONTMATTER_MAP` | Copilot requires `AGENTS.md` format; abstraction earns its keep. |
| Migration timing | Single big-bang PR | Pre-v1.0; no users to break; one feature branch. |
| Old init'd repos cleanup | Explicit `migrate` command; no silent delete | User explicitly requested no silent cleanup. Move to backup, not rm. |
| Extensions subsystem | Out of scope | User direction. |
| LSP migration sequencing | Bundled in single PR | User direction (single branch). |

---

## Sources

- [Create plugins (Claude Code)](https://code.claude.com/docs/en/plugins)
- [Plugins reference (Claude Code)](https://code.claude.com/docs/en/plugins-reference)
- [Build plugins (Codex)](https://developers.openai.com/codex/plugins/build)
- [Codex CLI plugin overview](https://developers.openai.com/codex/plugins)
- [Cursor plugin specification](https://github.com/cursor/plugins)
- [Cursor rules docs](https://cursor.com/docs/context/rules)
- [GitHub Copilot custom instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [GitHub Copilot custom agents for CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)
- Live inspection of `~/.claude/plugins/cache/` — angular-development-assistant, code-review, hookify, skill-creator, example-plugin, coderabbit, ui-ux-engineer, dotnet-ai-kit, csharp-lsp
- Code citations: `src/dotnet_ai_kit/cli.py`, `src/dotnet_ai_kit/copier.py`, `src/dotnet_ai_kit/agents.py`, `hooks/hooks.json`, `.claude-plugin/plugin.json`, `.mcp.json`
- Predecessor work: `issues/token-burn-optimization/FINAL-REPORT.md` (feature 018)
