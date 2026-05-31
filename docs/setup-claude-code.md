# Claude Code Setup Guide

**Mode**: Plugin-native (full enforcement) · **Manifest**: `build/.claude-plugin/plugin.json`

Claude Code is the primary host. It receives the entire corpus — **181 skills**
(including 32 command-skills), **15 agents**, **21 rules** (5 universal +
16 path-scoped domain), profiles, and knowledge docs — plus the full enforcement
stack: a shipped Roslyn analyzer and PreToolUse / Stop hooks. Everything is served
from the plugin install path; nothing is copied per-solution except a small config
footprint.

---

## 1. Install the CLI tool

The engine ships as a .NET global tool (`DotnetAiKit.Tool`, command `dotnet-ai`).
Requires the .NET 10 SDK.

```bash
dotnet tool install --global DotnetAiKit.Tool
dotnet-ai --version          # 2.0.0
```

## 2. Install the plugin

The generated `build/` tree is a marketplace (`build/.claude-plugin/marketplace.json`)
whose one plugin's `source` is `./claude`, so the plugin root is `build/claude/`.

```bash
# From the repo checkout (or a published marketplace)
/plugin marketplace add ./build
/plugin install dotnet-ai-kit
```

After install, all skills, command-skills (`/dai.*`), agents, and hooks are live
immediately. No `dotnet-ai init` is required just to *use* the plugin — `init` wires a
specific solution to the convention rules (`.claude/rules/*.md`).

---

## 3. Initialize a solution

Run `dotnet-ai init` once per solution to write the per-solution footprint —
critically, the **`.claude/rules/*.md`** files carrying `paths:` frontmatter so
domain rules load just-in-time and universal rules are always on (the v1
rule-delivery defect, now fixed and locked by tests).

```bash
dotnet-ai init .                 # detect architecture + write the footprint
dotnet-ai init . --dry-run       # preview every file; write nothing
dotnet-ai init . --host claude   # host is claude by default
```

### What `init` writes

| Path | Purpose |
|------|---------|
| `.claude/rules/<name>.md` | One per rule (21); domain rules carry `paths:`, universal rules are always-on |
| `.claude/settings.json` | Claude Code settings (schema-pinned) |
| `.dotnet-ai-kit/version.txt` | Installed corpus version |
| `.dotnet-ai-kit/config.yml` | Enabled hosts, permission profile, plugin version |
| `.dotnet-ai-kit/project.yml` | Detected architecture, .NET version, company |
| `.dotnet-ai-kit/manifest.json` | Host + rule count for `check` |

Skills, agents, and command-skills are **not** copied — they are served from the
plugin install path on every session.

---

## 4. Enforcement

All four enforcement tiers (planning/24) are wired and active for Claude Code:

- **T1 Advisory** — the `.claude/rules/*.md` written by `init` (domain rules carry
  `paths:` so they load just-in-time; universal rules are always on), **plus** the
  PreToolUse hook injecting the matching rule bodies as `additionalContext` on every
  Write/Edit (the runtime half of the rule-delivery fix).
- **T2 Interceptive** — the PreToolUse hook **denies** edits to generated/build-output
  files (`obj/`, `bin/`, `*.g.cs`, `*.Designer.cs`, `*.AssemblyInfo.cs`) before they reach disk.
- **T3 Deterministic** — the Roslyn analyzer: `DAK0001` (no `async void`) and `DAK0004`
  (aggregates expose no public setters, with a code-fix). Zero model tokens; fails the build.
- **T4 Completion gate** — the Stop / SubagentStop hook runs `dotnet build` + `dotnet test`
  when the assistant tries to finish and **blocks "done"** until both are green.

The hook tiers are projected to `build/claude/hooks/hooks.json` and call the on-PATH
`dotnet-ai hook pretooluse` / `dotnet-ai hook stop` (cross-platform — no bash/python).
Per planning/26 these hard tiers (T2/T4) are Claude-scoped; other hosts fall back to the
analyzer + CI. The Stop gate runs on every Stop/SubagentStop (an intentional always-on
default; planning/24 left always-on-vs-opt-in open) and honors `stop_hook_active` so a
red build can't wedge the session in a block loop.

> **Verified loadable.** `build/claude/` is a valid Claude plugin and `build/` a valid
> marketplace — both pass `claude plugin validate … --strict`. The marketplace
> (`build/.claude-plugin/marketplace.json`) points the plugin `source` at `./claude`, so the
> plugin root is `build/claude/` and its `skills/`, `agents/`, and `hooks/hooks.json` are
> auto-discovered. With the plugin installed, the PreToolUse/Stop hooks fire from
> `build/claude/hooks/hooks.json`; the `dotnet-ai hook` backend is verified end-to-end.

---

## 5. Verify

```bash
dotnet-ai check          # validates plugin footprint, rules, project.yml, manifest
```

Exit code `0` = pass; non-zero codes (10/12/14/16/…) identify the failing check class.

---

## 6. Updating

The plugin is the generated `build/` tree, so updates propagate by reinstalling /
reloading — there is nothing to copy. `dotnet-ai upgrade` is intentionally a no-op
for plugin-native Claude Code.

```bash
/reload-plugins          # reload within a running session
```

---

## Quick command reference

```text
/dai.do "Add order management with tracking"   # full SDD lifecycle
/dai.detect                                     # (re-)detect architecture
/dai.specify → /dai.plan → /dai.tasks → /dai.go # spec-driven flow
/dai.status                                     # feature progress
```

Command-skills carry `disable-model-invocation` so they stay off the always-loaded
listing (token-frugal) and are invoked explicitly as `/dai.*`.
