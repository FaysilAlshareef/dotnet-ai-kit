# GitHub Copilot Setup Guide

**Mode**: Render-only · **No plugin manifest**

GitHub Copilot has no plugin runtime, so dotnet-ai-kit takes a different
approach: content is rendered into your repository as static Markdown files
that Copilot reads as custom instructions. Re-render any time assets change.

---

## What gets rendered

`dotnet-ai init --ai copilot` writes three file classes to `.github/`:

| Path pattern | Purpose |
|-------------|---------|
| `.github/copilot-instructions.md` | Repository-wide instructions (always loaded) |
| `.github/instructions/<area>.instructions.md` | Path-scoped instructions per detected area |
| `.github/agents/<name>.agent.md` | One file per specialist agent (13 total) |

These files are generated from Jinja2 templates in `agents-copilot-templates/`
using your `project.yml` metadata (company, domain, project type, detected paths).

---

## Initialize your project

```bash
# Initialize Copilot support
dotnet-ai init . --ai copilot

# Preview what would be written
dotnet-ai init . --ai copilot --dry-run

# Set project metadata inline for richer renders
dotnet-ai init . --ai copilot --company Acme --domain Orders --side server

# Initialize all hosts at once
dotnet-ai init . --ai claude --ai codex --ai cursor --ai copilot
```

### What init writes

In addition to the standard `.dotnet-ai-kit/` config files, Copilot init
writes the rendered `.github/` files:

| Path | Purpose |
|------|---------|
| `.dotnet-ai-kit/config.yml` | Company, repos, permissions, enabled hosts |
| `.dotnet-ai-kit/project.yml` | Detected architecture, .NET version |
| `.dotnet-ai-kit/manifest.json` | SHA-256 registry of every managed file |
| `.github/copilot-instructions.md` | Rendered repo-wide instructions |
| `.github/instructions/*.instructions.md` | Rendered path-scoped instructions |
| `.github/agents/*.agent.md` | 13 rendered specialist agent files |

---

## Commit the rendered files

The `.github/` files are committed to your repository — that is how Copilot
reads them. Add them to git after init:

```bash
git add .github/ .dotnet-ai-kit/
git commit -m "chore: add dotnet-ai-kit Copilot instructions"
```

---

## Conflict policy — protecting your files

If a `.github/` file already exists before `dotnet-ai init`, it is
**preserved in place** by default. The init command reports the conflict
and exits non-zero; nothing is overwritten without explicit consent.

To overwrite a specific pre-existing file, use `--force-render`:

```bash
# Opt in to overwriting a specific file
dotnet-ai init . --ai copilot --force-render .github/copilot-instructions.md

# Overwrite multiple files
dotnet-ai init . --ai copilot \
  --force-render .github/copilot-instructions.md \
  --force-render ".github/agents/api-designer.agent.md"
```

`--force-render` applies to exact paths only and is recorded in
`manifest.json` with explicit-consent metadata.

---

## Keeping files fresh

Copilot render files can drift from the plugin templates when:
- You update the dotnet-ai-kit plugin
- Your `project.yml` metadata changes (new architecture detection, new domain)
- You change company or naming config

### Re-render all Copilot files

```bash
dotnet-ai upgrade --copilot
```

This re-renders only files that are still **managed** (SHA-256 matches
the manifest entry). User-modified files are preserved; use
`--force-render` to overwrite them.

### Check freshness

```bash
dotnet-ai check          # reports stale Copilot renders under "Copilot freshness"
dotnet-ai check --json   # machine-readable freshness result
```

---

## How managed vs. user-modified works

`dotnet-ai` tracks every rendered file in `.dotnet-ai-kit/manifest.json`
with a SHA-256 hash and `host_owner: "copilot"`.

| State | SHA matches manifest? | What happens on upgrade |
|-------|-----------------------|-------------------------|
| **Managed** | Yes | Re-rendered automatically |
| **User-modified** | No | Preserved (use `--force-render` to overwrite) |
| **Missing** | N/A | Re-rendered (same as managed) |

---

## Migrating from pre-v1.0

Pre-v1.0 Copilot files were written by a different path. After upgrading the
plugin, run:

```bash
# 1. Preview the migration
dotnet-ai migrate --dry-run --host copilot

# 2. Apply (moves managed files to .dotnet-ai-kit/backups/migrate/)
dotnet-ai migrate --host copilot

# 3. Re-render fresh Copilot files
dotnet-ai upgrade --copilot

# 4. Verify
dotnet-ai check
```

---

## Limitations

- Copilot has no session reload mechanism for instructions — Copilot reads
  the `.github/` files from the committed repo contents. Push changes and
  start a new Copilot session for updates to take effect.
- Path-scoped instructions (`.github/instructions/`) require Copilot support
  for per-file instruction scoping; availability depends on Copilot version.
- `dotnet-ai render --host copilot` (runtime rendering for Copilot shape) is
  deferred to v1.1.
