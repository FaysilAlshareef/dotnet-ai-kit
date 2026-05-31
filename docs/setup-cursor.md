# Cursor Setup Guide

**Mode**: Plugin-native · **Manifest**: `build/.cursor-plugin/plugin.json`

Cursor receives **149 skills**, **32 command-skills** (as `commands/*.md`), and
**21 rules** projected as Cursor `.mdc` files (`rules/*.mdc`) carrying glob scoping
so domain rules attach to matching files. Agents are not projected to Cursor.

---

## 1. Install the CLI tool

```bash
dotnet tool install --global DotnetAiKit.Tool
dotnet-ai --version          # 2.0.0
```

## 2. Install the plugin

The plugin is the generated `build/` tree (Cursor reads `build/.cursor-plugin/plugin.json`).

```bash
# Point Cursor at the built plugin directory, or copy build/cursor/* into the workspace
```

| Projected path | Contents |
|----------------|----------|
| `build/cursor/rules/*.mdc` | 21 rules with glob scoping (5 universal + 16 domain) |
| `build/cursor/commands/*.md` | 32 command-skills (`/dai.*`) |
| `build/cursor/skills/*/SKILL.md` | 149 skills |

---

## 3. Initialize a solution (optional)

```bash
dotnet-ai init . --dry-run   # preview the per-solution footprint
```

`init` writes the project metadata footprint (`.dotnet-ai-kit/*`). Cursor reads
conventions from the projected `.mdc` rules.

---

## 4. How conventions apply

- **Rules** project to `.mdc` with Cursor glob frontmatter — domain rules attach
  to matching files, universal rules apply always. This mirrors Claude's path-scoped
  delivery (the v1 rule-delivery defect is fixed for Cursor too).
- **Deterministic enforcement** comes from the shipped Roslyn analyzer
  (`DAK0001`, `DAK0004` + code-fix) at build time, independent of the host.
- PreToolUse / Stop hooks are Claude-specific and do not apply to Cursor.

---

## 5. Verify & update

```bash
dotnet-ai check        # 0 = pass; non-zero identifies the failing class
dotnet-ai generate     # re-project artifacts/ → build/ (maintainers)
```

The generated tree is CI drift-gated, so what Cursor loads always matches the single
authored `artifacts/` source.
