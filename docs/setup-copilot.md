# GitHub Copilot Setup Guide

**Mode**: Render-only · **No plugin manifest**

Copilot has no plugin system, so dotnet-ai-kit projects a render-only surface:
a generated **`.github/copilot-instructions.md`** (conventions Copilot loads
automatically) plus **149 skills** as reference material. There are no agents,
no hooks, and no command-skills on Copilot.

---

## 1. Install the CLI tool

```bash
dotnet tool install --global DotnetAiKit.Tool
dotnet-ai --version          # 2.0.0
```

## 2. Render the Copilot files into your repo

Copilot reads `.github/copilot-instructions.md` from the repository. Copy the
generated file (and skills, if you want them browsable) into your repo:

```bash
dotnet-ai generate                 # writes build/copilot/.github/copilot-instructions.md
# copy build/copilot/.github/copilot-instructions.md → <your-repo>/.github/
```

| Projected path | Contents |
|----------------|----------|
| `build/copilot/.github/copilot-instructions.md` | All conventions, inlined (Copilot has no per-file scope) |
| `build/copilot/skills/*/SKILL.md` | 149 skills as reference docs |

---

## 3. Keeping it current

Because Copilot files are **rendered into your repo** (not served from a plugin),
re-render them when the corpus changes:

```bash
dotnet-ai upgrade --copilot        # re-render Copilot files only
```

This is the one host where `upgrade` does real work — the plugin-native hosts
(Claude/Codex/Cursor) serve from the install path, so their `upgrade` is a no-op.

---

## 4. What does NOT apply to Copilot

- **Hooks** (PreToolUse / Stop) — Claude-specific.
- **Command-skills** (`/dai.*`) — Copilot has no slash-command surface.
- **Agents** — not projected.

**Deterministic enforcement** still applies: the shipped Roslyn analyzer
(`DAK0001`, `DAK0004` + code-fix) runs at build time regardless of which assistant
wrote the code.

---

## 5. Verify

```bash
dotnet-ai check        # 0 = pass; non-zero identifies the failing class
```
