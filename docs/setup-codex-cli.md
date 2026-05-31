# Codex CLI Setup Guide

**Mode**: Plugin-native · **Manifest**: `build/.codex-plugin/plugin.json`

Codex CLI receives **181 skills** (including 32 command-skills), **15 agents**, and
a generated **`AGENTS.md`** that inlines every convention rule. Codex has no
per-file rule scoping, so all rules (universal + domain) are concatenated into
`AGENTS.md` and applied globally.

---

## 1. Install the CLI tool

```bash
dotnet tool install --global DotnetAiKit.Tool
dotnet-ai --version          # 2.0.0
```

## 2. Install the plugin

The plugin is the generated `build/` tree (Codex reads `build/.codex-plugin/plugin.json`).

```bash
# Point Codex at the built plugin directory
codex plugin add ./build
```

`AGENTS.md`, `agents/`, and `skills/` are served from the plugin path — nothing is
copied per-solution by the plugin itself.

---

## 3. Initialize a solution (optional)

```bash
dotnet-ai init . --dry-run   # preview the per-solution footprint
```

> Note: `init` writes the Claude-shaped per-solution footprint
> (`.claude/rules/*`, `.dotnet-ai-kit/*`). Codex applies conventions through the
> generated `AGENTS.md` instead, so per-solution `init` is optional for Codex-only
> projects. The `dotnet-ai` CLI verbs (`check`, `render`, `detect`, `generate`) work
> the same regardless of host.

---

## 4. How conventions apply

Codex has a single global instruction surface, so:

- **All 21 rules** (5 universal + 16 domain) are inlined into `AGENTS.md` — there is
  no path-scoped JIT loading on Codex, so they apply globally.
- **Deterministic enforcement** still comes from the shipped Roslyn analyzer
  (`DAK0001`, `DAK0004` + code-fix) at build time, independent of the host.
- The interceptive PreToolUse / Stop hooks are **Claude-specific** and do not apply
  to Codex.

---

## 5. Verify & update

```bash
dotnet-ai check        # 0 = pass; non-zero identifies the failing class
dotnet-ai generate     # re-project artifacts/ → build/ (maintainers)
```

The generated tree is CI drift-gated (`generate --check`), so what Codex loads
always matches the single authored `artifacts/` source.
