# Quickstart: Plugin-Native dotnet-ai-kit

**Branch**: `019-plugin-native-arch` | **Date**: 2026-05-17 | **Plan**: [plan.md](./plan.md)

This quickstart shows how a developer installs and uses the plugin-native dotnet-ai-kit, plus how an existing user migrates from the previous per-solution layout.

## Prerequisites

- **One of these AI hosts installed**: Claude Code, Codex CLI, Cursor, or GitHub Copilot
- **Python 3.10+**: required for the `dotnet-ai` CLI
- **.NET SDK 8.0 / 9.0 / 10.0**: in your target .NET solution
- **For Claude Code C# intelligence**: `csharp-ls` binary on PATH (the language server). Check with `dotnet-ai check`.

The tool works on Windows, macOS, and Linux (binding per spec A-010).

## 1. Install the plugin (per host)

### Claude Code

```bash
# Add the plugin marketplace
/plugin marketplace add FaysilAlshareef/dotnet-ai-kit

# Install
/plugin install dotnet-ai-kit
```

After install, `/dotnet-ai-kit:*` commands and skills are available immediately.

### Codex CLI

Per the current Codex docs at `https://developers.openai.com/codex/plugins`, plugin install routes through the Codex CLI interactive surface:

```bash
# Launch Codex CLI
codex

# Inside Codex, browse and install from the plugin marketplace
/plugins
# Select dotnet-ai-kit from the listing and confirm install
```

After install, `dotnet-ai-kit` skills and MCP servers are visible to Codex CLI. The installed plugin lives at `~/.codex/plugins/cache/<marketplace>/dotnet-ai-kit/<version>/` per the Codex plugin docs.

### Cursor

Per Cursor's plugin marketplace, two install paths:

**Marketplace install (production)**:
```
# In Cursor's chat
/add-plugin dotnet-ai-kit
```

**Local development install (testing)**:
```bash
# Linux / macOS
ln -s /path/to/dotnet-ai-kit ~/.cursor/plugins/local/dotnet-ai-kit

# Windows
mklink /D "%USERPROFILE%\.cursor\plugins\local\dotnet-ai-kit" "C:\path\to\dotnet-ai-kit"
```

After install, Cursor sees the plugin's skills, rules, and (if the A-005 sub-agent spike passed) Cursor-shaped agents at `./agents/`.

### GitHub Copilot

Copilot has no plugin host. The plugin's content reaches Copilot through repository-rendered files. Continue to step 2 — `dotnet-ai init` with Copilot selected will render the files.

## 2. Initialize a .NET solution

```bash
# In the root of your .NET solution
pip install dotnet-ai-kit
dotnet-ai init
```

The interactive flow asks which AI hosts you want enabled (per clarify Q4 — no silent defaults). Pick any subset of `claude`, `codex`, `cursor`, `copilot`.

After init, your solution contains:

```
.dotnet-ai-kit/
├── config.yml        # which hosts you enabled + your preferences
├── project.yml       # detected project metadata (company, domain, layer paths, etc.)
└── manifest.json     # internal tracking of what the tool wrote

.claude/
└── settings.json     # permissions merge only (for Claude users)
```

If you enabled Copilot, also:

```
.github/
├── copilot-instructions.md           # repo-wide
├── instructions/<area>.instructions.md   # path-scoped (per the 11 domain areas)
└── agents/<name>.agent.md            # per-agent (13 specialists)
```

**The previous ~180 files per solution are gone.** Per-solution footprint is now under 10 files for plugin-host users (per SC-001).

## 3. Verify state

```bash
dotnet-ai check
```

This single command verifies:

- The plugin is installed in each of your enabled hosts (filesystem inspection per clarify Q3)
- The `csharp-ls` binary is on PATH (for Claude users with C# intelligence)
- `.dotnet-ai-kit/project.yml` is valid and consistent with your working tree
- `.dotnet-ai-kit/manifest.json` is intact (no files tampered)
- Copilot renders (if enabled) are fresh against current plugin source

Expected output on a healthy install:

```
✅ Claude Code plugin: installed at ~/.claude/plugins/cache/.../dotnet-ai-kit/<version>/
✅ csharp-ls binary: /usr/local/bin/csharp-ls
✅ project.yml: valid (company=Contoso, project_type=command, branch=microservice)
✅ manifest.json: 7 files tracked, all hashes match
(no Copilot renders to check)

dotnet-ai check passed in 1.2s
```

Run with `--verbose` to see per-host details.

## 4. Use slash commands

In your AI host:

- **Claude Code**: `/dotnet-ai-kit:do "<task>"` (or `/dotnet-ai-kit:plan`, `/dotnet-ai-kit:implement`, etc.)
- **Codex CLI**: `dotnet-ai-kit:do "<task>"` via Codex CLI's command surface
- **Cursor**: `/dotnet-ai-kit do <task>` in Cursor's chat
- **GitHub Copilot**: Use a custom agent — type `@<agent-name> <task>` (e.g., `@dotnet-architect`)

Skills and rules load on-demand. The session-start orientation is now ≤500 tokens of compact bootstrap (per SC-013) rather than the ~5000-token rule-body dump that older versions used.

## 5. Customization that survives refactors

If you rename your company, change your domain, or refactor a layer folder:

```bash
# Update .dotnet-ai-kit/project.yml with the new value
$EDITOR .dotnet-ai-kit/project.yml
```

The next AI session — or the next pre-tool-use hook fire in an active session (per FR-034) — observes the new value. **No upgrade or re-init needed**.

For Copilot users only, re-render after metadata changes:

```bash
dotnet-ai upgrade --copilot
```

## 6. Migrate from the old layout

If you previously installed the tool under the per-solution copy layout (≤v0.x), you have files like `.claude/commands/dotnet-ai.do.md` shadowing the plugin. Clean up:

```bash
# Preview what migrate will do (recommended first)
dotnet-ai migrate --dry-run

# Apply
dotnet-ai migrate
```

What `migrate` does:

1. Reads `.dotnet-ai-kit/manifest.json` to identify managed legacy files
2. Classifies each by content hash: `clean` (matches the original generated content) or `user-modified`
3. Moves clean files to `.dotnet-ai-kit/backups/migrate/<timestamp>/` (project-local; not the OS data directory)
4. **Preserves user-modified files in place** unless you explicitly select them for removal
5. Rotates the migrate-backups folder to keep the 3 most recent runs

To reverse a migrate, copy files from `.dotnet-ai-kit/backups/migrate/<timestamp>/` back to their original paths.

`init --force` does **not** auto-migrate. If you run `dotnet-ai init --force` and the tool detects shadowed legacy artifacts, it prints the exact `dotnet-ai migrate` invocation for you.

## 7. Inspect runtime-resolved content

The new layout means commands and skills are no longer pre-rendered into your repository. To see what a parameterized skill or rule actually resolves to with your current `project.yml`:

```bash
dotnet-ai render skill <skill-name>
dotnet-ai render rule <rule-name>
```

Output shows the resolved content as Claude Code would see it (v1 scope; other hosts' render shapes are v1.1 work per SC-012).

## 8. Common scenarios

### Add a new AI host after init

```bash
dotnet-ai configure
# Pick the new host(s)
dotnet-ai init  # writes only files for newly-enabled hosts
```

### Disable a host

```bash
dotnet-ai configure
# Deselect the host
dotnet-ai migrate  # cleans up files for the now-disabled host (host_owner-scoped)
```

### Verify packaging in CI

```bash
python -m build
pip install dist/dotnet_ai_kit-*.whl
ls ~/.local/lib/python*/site-packages/dotnet_ai_kit/
# Should contain .claude-plugin/, .codex-plugin/, .cursor-plugin/ (and other manifest dirs per SC-009)
```

### Test the host smoke fixtures

```bash
# Claude Code (needs claude on PATH)
CLAUDE_CODE_SMOKE=1 pytest -m smoke tests/integration/test_smoke_claude.py

# Codex CLI (needs codex on PATH)
CODEX_SMOKE=1 pytest -m smoke tests/integration/test_smoke_codex.py

# Cursor (needs cursor on PATH; gates A-005 outcome)
CURSOR_SMOKE=1 pytest -m smoke tests/integration/test_smoke_cursor.py
```

### Trigger a Copilot refresh after upstream change

```bash
# After pulling a new dotnet-ai-kit version
dotnet-ai check  # Reports Copilot renders as stale
dotnet-ai upgrade --copilot  # Re-renders against current plugin source + project.yml
dotnet-ai check  # Now clean
```

## 9. Privacy and network posture

Per spec A-011: **the tool makes no outbound network calls and emits no telemetry.** No analytics, no crash reporting, no auto-update check. Host plugin installation (when the host fetches a plugin from its plugin registry) is the host's responsibility and runs in the host's process, not the tool's.

This is verified by `tests/unit/test_no_network_no_telemetry.py` — the tool's import graph contains no `requests`, no `urllib.request.urlopen`, no `httpx`, no socket connections.

## 10. Troubleshooting

- **`dotnet-ai check` reports plugin missing but I installed it**: clarify Q3 binds filesystem inspection. The check looks at the host's documented plugin-cache directory. If your host uses a non-default plugin cache location, please file an issue with the location and OS so the per-host check can be extended.
- **C# intelligence not surfacing diagnostics at edit time**: ensure `csharp-ls` binary is on PATH; ensure your Claude Code version supports plugin LSP dependencies (per architecture-phase R6). `dotnet-ai check` reports this.
- **Migrate moved a file I wanted to keep**: it's in `.dotnet-ai-kit/backups/migrate/<timestamp>/`. Copy back to where it was. Per FR-022 the tool MUST NOT have classified a user-modified file as `clean`; if it did, please file an issue.
- **Cursor sub-agents not visible**: the A-005 spike outcome determines whether full sub-agent generation shipped. Check the release notes and `discussion/plan-phase/cursor-spike-outcome.md` for the status.
