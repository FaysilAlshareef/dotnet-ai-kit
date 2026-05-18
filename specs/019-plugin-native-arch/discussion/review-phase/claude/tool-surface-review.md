# Review-Phase: Claude Tool-Surface Review

**Date**: 2026-05-18
**Branch**: `019-plugin-native-arch`
**Phase**: Review (broader scope after first CLI-narrow `review.md`)
**Reviewer**: Claude (Opus 4.7, 1M context)
**Scope**: Plugin manifests, hooks, rules, skills, agents, commands,
templates, MCP, LSP, docs, configs, Copilot rendering paths — everything
outside the Python CLI behavior covered by `review.md`.
**Verdict**: **BLOCK-WITH-MINOR-FIXES** before v1.0.0 tag

## Why "BLOCK-WITH-MINOR-FIXES"

This is a stronger position than the CLI-narrow `review.md`
(`AGREED-WITH-NOTES`) because this scan surfaced **6 real
documentation and asset issues** that violate the spec or describe
pre-019 behavior. None are code defects, but four of them produce
user-visible inconsistencies the moment a user runs `/dotnet-ai.init`
under v1.0.0:

| # | Finding | Severity | Surface |
|---|---|---|---|
| F1 | `CHANGELOG.md` has no v1.0.0 / feature-019 entry — last entry is "[Unreleased] — Fix Token Burn (feature 018)" | **HIGH** | `CHANGELOG.md` |
| F2 | `commands/init.md` describes legacy bulk-copy behavior (6 stale references) that contradicts FR-005/FR-006 | **HIGH** | Slash-command body that the user sees |
| F3 | `commands/configure.md:126` says "re-copies commands with the selected style" — pre-019 language | **MEDIUM** | Slash-command body |
| F4 | `AGENTS.md` at repo root has stale counts: 15 rules / 5 hooks / 13 templates / "always-loaded conventions" | **MEDIUM** | Tool's own metadata file |
| F5 | `CONTRIBUTING.md` has stale counts: 9 rules / 4 hooks / "csharp-ls" in MCP description (csharp-ls removed in commit 12) | **MEDIUM** | Contributor-facing doc |
| F6 | `rules/cursor/` is empty (only `.gitkeep`) yet `.cursor-plugin/plugin.json` declares `"rules": "./rules/cursor/"` | **LOW-MEDIUM** | Cursor plugin manifest broken reference |

All 6 are docs-only fixes — none require Python code changes. The CLI
behavior verified in `review.md` is correct; this review is about the
**user-visible content** that ships with the tool.

## What I verified (and is clean)

### Plugin manifests (all references resolve)

I wrote a Python validator that resolved every path in the three host
manifests against the working tree. Result:

```
.claude-plugin/plugin.json:
  OK: agents   (13 entries, all exist)
  OK: skills   (124 entries, all exist)
  OK: commands (27 entries, all exist)
  OK: hooks    (configFile = hooks/hooks.json exists)
  OK: mcpServers (configFile = .mcp.json exists)

.codex-plugin/plugin.json:
  OK: skills   (./skills/ — folder-based discovery per A-006)
  OK: hooks    (./hooks/hooks.json)
  OK: mcpServers (./.mcp.json)
  (No agents declared — correct per A-006 / OOS-004)

.cursor-plugin/plugin.json:
  OK: skills    (./skills/)
  OK: hooks     (./hooks/hooks.json)
  OK: mcpServers (./.mcp.json)
  OK: agents    (./agents/)
  BROKEN: rules (./rules/cursor/ — folder is empty, only .gitkeep)
                see F6
```

The Cursor plugin's `agents: "./agents/"` reference resolves to a
folder that contains exactly **one** file (`dotnet-ai-architect.md`).
That's consistent with A-005 / OOS-005 (full Cursor sub-agent
generation only ships if the spike fixture passes; otherwise one
fixture is the minimum). Acceptable as v1.0 scope but worth a follow-
up entry to track the spike outcome.

### Hooks (`hooks/hooks.json` + 7 scripts)

All 7 hook scripts on disk are referenced from `hooks/hooks.json`:

| Hook script | Used in `hooks.json` | Trigger |
|---|---|---|
| `session-start-bootstrap.sh` | ✓ | `SessionStart` (NEW in 019) |
| `pretooluse-arch-profile.sh` | ✓ | `PreToolUse` on `Edit\|Write` (NEW in 019) |
| `pre-bash-guard.sh` | ✓ | `PreToolUse` on `Bash` |
| `pre-commit-lint.sh` | ✓ | `PreToolUse` on `Bash(git commit*)` |
| `post-edit-format.sh` | ✓ | `PostToolUse` on `Edit\|Write(*.cs)` |
| `post-scaffold-restore.sh` | ✓ | `PostToolUse` on `Bash(dotnet new*)` |

The `if:` conditional matchers in `hooks.json` use the v2.1.85+ syntax
(`if: Edit(*.cs)`, `if: Bash(dotnet new*)`) — consistent with what
018's PR1 introduced. Good.

**Verified against FR-013 / SC-013**: `session-start-bootstrap.sh`
emits 295 tokens (measured by `scripts/measure_always_on.py`),
**well under** the ≤500-token bootstrap budget.

**Verified against FR-034 / CHK046-048**:
`pretooluse-arch-profile.sh` is invoked on every Edit/Write tool use
and re-resolves architecture profile from current `project.yml`. Test
gate is `tests/unit/test_pretooluse_arch_profile.py` (4 tests, skipped
on Windows because the hook is bash; covered by Linux/macOS CI).

### Rules (5 conventions + 11 domain — constitution v1.0.8)

```
rules/conventions/ (5 universal, always-on):
  async-concurrency.md    50 lines
  coding-style.md         48 lines
  existing-projects.md    49 lines
  security.md             50 lines
  tool-calls.md           57 lines

rules/domain/ (11 path-scoped, JIT):
  api-design.md, architecture.md, configuration.md, data-access.md,
  error-handling.md, localization.md, multi-repo.md, naming.md,
  observability.md, performance.md, testing.md (47-90 lines each)
```

**All 16 rules are within the 100-line budget** (max: testing.md
at 90 lines). The 5+11 split aligns with constitution v1.0.8 and FR-011.

**Minor inconsistency** (not a finding, but worth noting): only
`rules/conventions/async-concurrency.md` declares a `paths:`
frontmatter (`paths: ["**/*.cs"]`). The other 4 universal rules omit
it. This is structurally correct because async-concurrency is the
only C#-specific universal rule, but the inconsistency could confuse
maintainers. Universal-vs-domain classification is by **folder**
(`conventions/` vs `domain/`), not by frontmatter — so `paths:` on a
universal rule is informational, not gating.

### Skills (124 SKILL.md across 16 categories)

```
skills/
  api (11), architecture (7), core (12), cqrs (6), data (8),
  detection (1), devops (5), docs (8), infra (4), microservice (37),
  observability (3), quality (3), resilience (3), security (5),
  testing (4), workflow (11)
  ────────────────────────────────────────────
  Total: 124 SKILL.md files
```

Sample frontmatter (`skills/api/caching-strategies/SKILL.md`):

```yaml
name: caching-strategies
description: Use when adding caching to .NET APIs...
metadata:
  category: api
  agent: api-designer
when_to_use: When implementing caching strategies...
```

Activation field `when_to_use` is correctly at top level (per 018's
PR2a). The remaining `metadata:` block carries non-activation
reference data (category, agent) and is harmless.

**No stale references found** in skill bodies — `grep -r "4 universal"`
across all 124 SKILL.md files returned nothing.

### Agents (13 in `agents-claude/`, 1 in `agents/`)

```
agents-claude/ (13 — per .claude-plugin/plugin.json):
  api-designer, command-architect, controlpanel-architect,
  cosmos-architect, devops-engineer, docs-engineer, dotnet-architect,
  ef-specialist, gateway-architect, processor-architect,
  query-architect, reviewer, test-engineer

agents/ (1 — per .cursor-plugin/plugin.json):
  dotnet-ai-architect.md (Cursor sub-agent spike fixture)
```

This split correctly implements **FR-026** (one source-of-truth per
logical specialist agent → generated per-host). The Claude path has
all 13; the Cursor path has the one mandatory spike fixture per A-005;
the Codex path has none per A-006.

### Commands (27 in `commands/`)

```
27 commands total. Max line counts (vs 200-line budget):
  tasks.md   196   (closest to budget)
  verify.md  194
  analyze.md 194
  detect.md  193
  ...lowest: undo.md 4147 bytes / ~85 lines
```

All 27 are within budget. The 27-command count matches:
- `.claude-plugin/plugin.json::commands` (27 entries)
- README.md badge text ("27 commands")
- `CLAUDE.md` "Commands (27 total)" table
- The actual files in `commands/`

### Templates (12 architecture profiles + scaffold files + config)

```
12 architecture profiles per spec.md:217 — ALL PRESENT:
  Microservice branch (7):
    command, query, cosmos-query, processor,
    gateway-consumer, gateway-management, controlpanel-module, hybrid
  Generic branch (5):
    generic-vsa, generic-clean-arch, generic-ddd,
    generic-modular-monolith, (generic itself is virtual — handled in code)

Plus:
  config-template.yml — default `config.yml` rendered at init
  hook-prompt-template.md — hook-prompt scaffolding
  commands/ — referenced template for command profile
```

Spec says "12 project types" in two branches. The microservice branch
should have 7 (`command, query-sql, query-cosmos, processor, gateway,
controlpanel, hybrid`) and the generic branch 5 (`vsa, clean-arch,
ddd, modular-monolith, generic`).

**Naming mapping** between spec terms and folder names:
- spec `query-sql` → `templates/query/`
- spec `query-cosmos` → `templates/cosmos-query/`
- spec `gateway` → `templates/gateway-consumer/` + `templates/gateway-management/` (two flavors)
- spec `controlpanel` → `templates/controlpanel-module/`
- spec `generic` → handled in models.py validation (no template folder)

The actual folder count is 12 (counting both gateway variants
separately), which is consistent with how the codebase already
validates the 12 distinct `project_type` values (per Clarifications Q1
in `spec.md:26`).

### MCP servers (`.mcp.json`)

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "codebase-memory-mcp",
      "args": ["--project", "."],
      "transport": "stdio",
      "dotnet_ai_kit_min_version": "0.6.1"
    }
  }
}
```

**csharp-ls was correctly removed in commit 12** per FR-028 / CHK012.
Validated by `tests/contract/test_mcp_csharp_removed.py`. The
remaining MCP is `codebase-memory-mcp` (introduced in feature 018,
PR4).

### LSP setup (csharp-lsp via plugin dependency)

`.claude-plugin/plugin.json` declares:

```json
"lspServers": {
  "csharp-lsp": {
    "_note": "References csharp-lsp plugin dependency (declared in `dependencies`)..."
  }
},
"dependencies": ["csharp-lsp"]
```

This is FR-028's plugin-native LSP route: csharp-ls is now a separate
plugin (`csharp-lsp`) listed as a `dependencies` entry of the main
plugin manifest, rather than an MCP server. The smoke test gate is
`tests/integration/test_smoke_claude_lsp.py` (CI-gated).
**`dotnet-ai check` detects missing csharp-ls binary** per SC-011 /
CHK011 / `test_check_filesystem_inspection.py`.

### Permission configs (4 JSON files)

```
config/
  permissions-minimal.json   (10 allow entries — basic dotnet/ls/cd)
  permissions-standard.json  (~30 allow entries)
  permissions-full.json      (full set + bypassPermissions warning)
  mcp-permissions.json       (GitHub MCP allow-list)
```

All 4 are intact. The `claude in ai_tools` permission gates (verified
in `review.md` at `cli.py:1132`, `:1931`, `:2337`, plus copier.py)
ensure these only get applied to `.claude/settings.json` when Claude
is a selected host. No 019 changes needed in the JSONs themselves.

### Repo-root docs status

| File | Status | Note |
|---|---|---|
| `README.md` | ✓ Updated for 019 | Line 783-786 has "Feature 019 (v1.0.0) plugin-native architecture" section; 1.0.0 badge; manifests reference |
| `CLAUDE.md` | ✓ Updated for 019 | "Feature 019 architecture (v1.0+)" section present with command surface + rule split + no-network invariant |
| `CHANGELOG.md` | ✗ **STALE — F1** | Last entry: "[Unreleased] — Fix Token Burn (feature 018)" — **no v1.0.0 entry** |
| `AGENTS.md` | ✗ **STALE — F4** | "15 always-loaded convention rules", "5 safety hooks", "13 project scaffolding templates" — pre-019 counts |
| `CONTRIBUTING.md` | ✗ **STALE — F5** | "9 always-loaded convention files", "4 Claude Code hooks", "csharp-ls for C# intelligence" |
| `CODE_OF_CONDUCT.md` | ✓ Generic | Not 019-affected |
| `SECURITY.md` | ✓ Generic | Not 019-affected |
| `pyproject.toml` | ✓ | version = "1.0.0" |

### `docs/` folder (v1.0 docs)

```
docs/
  migration-v1.md          # Migration guide from pre-019 layouts
  release-notes-v1.0.md    # v1.0 release notes
  unmanaged-paths.md       # A-008 user-owned paths inventory
```

Three v1.0-specific docs exist. **Note**: These three are the
*intended* user-facing release notes; they coexist with the missing
CHANGELOG.md entry (F1) but **do not replace it** — `CHANGELOG.md` is
the canonical changelog file at repo root and tools/sites
(e.g., GitHub release page) link to it.

## Findings detail (the 6 issues)

### F1 — CHANGELOG.md missing v1.0.0 / feature-019 entry  **[HIGH]**

**Evidence**:

```
$ grep -n "019\|plugin-native\|v1\.0\.0" CHANGELOG.md
169:### Added (spec-017: Pre-Release v1.0.0 Hardening)
```

The only `v1.0.0` mention is in the 017 hardening section. The
"Unreleased" header is for feature 018. Feature 019 contributed
19 commits and ~22,000 lines of change but has **no changelog
section**.

**Required fix**: Add a `## [1.0.0] — 2026-05-18` section that
summarizes the 35 FRs, 14 SCs, and the 5 OOS items, mirroring how
017 was documented. The content already exists in
`docs/release-notes-v1.0.md` — it just needs to be reflected (or
referenced) from `CHANGELOG.md`.

**Suggested entry skeleton**:

```markdown
## [1.0.0] — 2026-05-18 — Plugin-Native Architecture (feature 019)

Pre-v1.0.0 architectural release: plugin-native delivery for Claude
Code / Codex CLI / Cursor; rendered repository-native files for
GitHub Copilot. See `docs/release-notes-v1.0.md` for the full
narrative and `specs/019-plugin-native-arch/spec.md` for the
spec.

### Added
- `dotnet-ai check` — validation command (FR-017, 6 check classes)
- `dotnet-ai migrate` — pre-019 layout cleanup with 3-keep rotation
  (FR-018-025, `--include-linked` for FR-033)
- `dotnet-ai render <skill|rule>` — runtime-resolved inspectability
  (FR-019, SC-012)
- `dotnet-ai upgrade --copilot` — Copilot-only refresh (FR-015)
- Plugin manifests for Claude, Codex, Cursor hosts (FR-001-003)
- Constitution v1.0.8 — 5 universal + 11 path-scoped rules (FR-011)
- SessionStart compact bootstrap (≤500 tokens, FR-013, SC-013)
- PreToolUse arch-profile hook (FR-034)
- 3-OS CI matrix (Linux, macOS, Windows; A-010)

### Changed
- `init`/`upgrade`/`configure` for plugin-native hosts: NO bulk-copy
  of commands/rules/skills/agents (FR-005, FR-006)
- Cursor rules: per-rule `.mdc` files (drop one-blob layout)
- Always-on context: ~9000 → 2880 tokens (68% reduction, SC-004)
- Per-solution file count: ~180 → ≤18 (98% reduction for Claude-only,
  SC-001)

### Removed
- `csharp-ls` MCP server (moved to `csharp-lsp` plugin dependency, FR-028)
- Legacy per-solution `.claude/commands/`, `.claude/rules/`,
  `.claude/skills/`, `.claude/agents/` writes for plugin-native hosts

### Out of Scope (deferred to v1.1)
- Native Codex CLI plugin agents (OOS-004)
- `bin/` launcher (OOS-003)
- Multi-repo activity monitor (OOS-006)
- Full Cursor sub-agent generation (OOS-005 if spike fixture fails)
```

### F2 — `commands/init.md` describes legacy bulk-copy  **[HIGH]**

**Evidence**:

```
commands/init.md:34: "This creates the config directory, copies commands/rules, and applies permissions"
commands/init.md:60: "- Number of commands copied"
commands/init.md:76: "- AI tool command directory (e.g., `.claude/commands/`)"
commands/init.md:77: "- AI tool rules directory (e.g., `.claude/rules/`)"
commands/init.md:106: "  Copied: {N} commands"
commands/init.md:107: "  Copied: {N} rules"
commands/init.md:127: "  Copied: {N} commands"
commands/init.md:128: "  Copied: {N} rules"
```

These are the **slash-command body** that gets rendered into Claude
Code's AI session when the user types `/dotnet-ai.init`. Under
plugin-native architecture (FR-005, FR-006), `init` for plugin-
supporting hosts MUST NOT copy commands or rules. The doc contradicts
the actual implementation.

**Required fix**: Rewrite `commands/init.md` to describe the
plugin-native flow:

1. Strip the "Copied: {N} commands / rules" output lines.
2. Replace step 5 verification list: `.claude/commands/` and
   `.claude/rules/` are NOT written per-solution — they come from the
   plugin install path.
3. Update Step 2 description: init writes config + version +
   manifest + Copilot renders (if enabled) + permissions; no bulk
   copy.

### F3 — `commands/configure.md:126` stale  **[MEDIUM]**

**Evidence**:

```
commands/configure.md:126: "This updates `.claude/settings.json` with the
selected permission level and re-copies commands with the selected style."
```

The `configure` command no longer re-copies commands for plugin-native
hosts (per `cli.py:2377` skip on `PLUGIN_NATIVE_HOSTS ∪ RENDER_ONLY_HOSTS`).
The doc still says it does.

**Required fix**: Edit line 126 to:

```markdown
This updates `.claude/settings.json` with the selected permission level
and updates the recorded `command_style` in `.dotnet-ai-kit/config.yml`.
For plugin-native hosts (Claude/Codex/Cursor), commands are served from
the plugin install path; the style preference is read at runtime.
```

### F4 — `AGENTS.md` repo-root metadata stale  **[MEDIUM]**

**Evidence**:

```
AGENTS.md:82: "rules/  # 15 always-loaded convention rules"
            (should be: 16 rules = 5 universal + 11 path-scoped)
AGENTS.md:83: "agents/  # 13 specialist agent definitions"
            (1 file in agents/; 13 in agents-claude/)
AGENTS.md:84: "hooks/  # 5 safety hooks (bash scripts)"
            (7 hooks now: added session-start + pretooluse-arch-profile in 019)
AGENTS.md:85: "templates/  # 13 project scaffolding templates"
            (12 architecture profiles per spec.md:217)
```

**Note on FR-008**: The spec says `AGENTS.md` is a developer-owned
path that the tool MUST NOT write. This repo's `AGENTS.md` is the
**tool author's own** repo-root file (not a generated artifact), so
maintainer ownership is fine. The issue is content drift, not
ownership.

**Required fix**: Update the Project Structure block to match v1.0.0
counts.

### F5 — `CONTRIBUTING.md` stale  **[MEDIUM]**

**Evidence**:

```
CONTRIBUTING.md (first 20 lines, Project Structure block):
  "├── .mcp.json          # MCP server config (csharp-ls for C# intelligence)"
                                                ^^^^^^^^^ csharp-ls removed in commit 12
  "├── hooks/             # 4 Claude Code hooks ..."     (now 7)
  "├── rules/             # 9 always-loaded convention files ..." (now 5+11=16)
  "├── templates/         # 13 project scaffolds (9 microservice + 4 generic)" (now 12)
```

**Required fix**: Same as F4 — update counts and the `.mcp.json`
description (it's `codebase-memory-mcp` now, not csharp-ls).

### F6 — `rules/cursor/` is empty but declared in plugin manifest  **[LOW-MEDIUM]**

**Evidence**:

```
$ ls -la rules/cursor/
total 4
drwxr-xr-x .gitkeep   (only)

$ cat .cursor-plugin/plugin.json | grep rules
"rules": "./rules/cursor/",
```

The Cursor plugin manifest declares `rules` from a folder that has
only `.gitkeep`. This is a broken reference from Cursor's POV — when
the Cursor plugin loader resolves rules, it finds nothing.

**Two possible fixes**:

A. **Populate `rules/cursor/`** with per-rule `.mdc` files (the format
   Cursor consumes for rules), generated from the same 16 rule
   bodies. This is the plugin-symmetric option.

B. **Drop the `rules` declaration** from `.cursor-plugin/plugin.json`
   and let Cursor rely on `.cursor/rules/<name>.mdc` written by the
   per-solution path (which `copy_commands_cursor` already handles
   via `cli.py:980`). This treats Cursor rules as a per-solution
   fallback rather than a plugin-native asset.

**Recommendation**: Option B. The existing Cursor `.mdc` rendering
pipeline at `cli.py:976-981` (T056 — drop one-blob, emit per-rule
`.mdc` files) is the validated path; the plugin manifest's `rules`
declaration is the duplicate that's not used.

The Cursor smoke fixture (CHK003) passes today because Cursor reads
rules per-solution, not from the plugin path — so this is **not a
runtime regression**; it's a manifest cleanliness issue.

## Optimization opportunities (not blocking)

### O1 — Extend `doc_lint.py` SCAN_GLOBS to cover commands and rules

`scripts/doc_lint.py` SCAN_GLOBS (line 36-41) covers:
- `README.md`
- `CLAUDE.md`
- `docs/**/*.md`
- `planning/**/*.md`

**Missing**: `commands/**/*.md`, `rules/**/*.md`, `skills/**/SKILL.md`,
`agents-claude/**/*.md`, `AGENTS.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.

Had this been broader, **F2/F3/F4/F5 would have been caught
automatically** during routine lint runs. The 24-files-scanned output
gives false confidence.

**Suggested patch** (post-merge, low priority):

```python
# scripts/doc_lint.py:36
SCAN_GLOBS = (
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "docs/**/*.md",
    "planning/**/*.md",
    "commands/**/*.md",
    "rules/**/*.md",
)
```

Plus add a stale-phrase check for pre-019 bulk-copy language:

```python
STALE_PHRASES = (
    "4 universal rules",
    "4 universal (always loaded",
    "Copied: {N} commands",                # NEW
    "Copied: {N} rules",                   # NEW
    "9 always-loaded convention",           # NEW (CONTRIBUTING.md)
    "15 always-loaded convention",          # NEW (AGENTS.md)
    "5 safety hooks",                       # NEW (AGENTS.md)
    "csharp-ls for C# intelligence",        # NEW (CONTRIBUTING.md after commit 12)
    "re-copies commands",                   # NEW (configure.md)
)
```

### O2 — Add a manifest-resolves-on-disk pytest gate

The Python validator I ran in this review (resolving every manifest
path against the working tree) should be a pytest gate, not an
ad-hoc check. The current `tests/contract/test_*_plugin_schema.py`
tests validate JSON schema shape but **do not assert that
`agents[]` / `skills[]` / `commands[]` paths exist**.

**Suggested test** (`tests/contract/test_plugin_manifest_paths.py`):

```python
@pytest.mark.parametrize("manifest", [
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
])
def test_manifest_paths_resolve(manifest):
    data = json.loads((REPO / manifest).read_text(encoding="utf-8"))
    for key in ("agents", "skills", "commands"):
        if isinstance(data.get(key), list):
            for entry in data[key]:
                assert (REPO / entry).exists(), \
                    f"{manifest}::{key}[]={entry} does not exist"
```

This would have caught F6 immediately.

### O3 — Promote the `metadata:` skill block to top level (or document it)

Skills carry both top-level fields (`name`, `description`,
`when_to_use`) and a nested `metadata:` block (`category`, `agent`).
The 018 PR2a lifted **activation** fields to top level. The remaining
`metadata:` block is fine but could be:

A. **Promoted to top level** (`category` and `agent` move up).
B. **Documented as a stable block** in `data-model.md` /
   `agents.py` (so contributors know it's not deprecated).

This is purely cosmetic / documentation-discipline. Not blocking.

### O4 — Drop or document the `paths:` on `async-concurrency.md`

Only the C#-specific universal rule has `paths:`. The frontmatter is
correct semantically but inconsistent with siblings. Two options:

A. Remove `paths:` from `async-concurrency.md` (universal rules are
   loaded by folder classification, not frontmatter).
B. Add `paths:` to all 5 conventions for symmetry — even broad ones
   would carry `paths: ["**/*"]`.

Pick one and document. Not blocking.

## Optional v1.1 follow-ups (not 019 scope)

- Populate `rules/cursor/` with rendered `.mdc` rule files if/when
  the Cursor sub-agent generation passes its A-005 fixture in v1.1.
- Add a docs/site link from `CHANGELOG.md` directly to
  `specs/019-plugin-native-arch/spec.md` so the spec is discoverable.
- Add `agents-claude/` validator that re-verifies the 13 agent files
  match the `.claude-plugin/plugin.json::agents[]` list (catch
  if/when a new agent is added without manifest update).

## What I confirmed against `review.md` (no conflict)

The CLI-narrow `review.md` found **AGREED-WITH-NOTES** with 2
non-blocking nits (constant duplication, extension-add OOS-002).
This broader scan does not contradict that — the **CLI behavior is
correct**. What this scan adds is that the **documentation and asset
layer around** the CLI has drift:

- The CLI does the right thing.
- The docs that describe what the CLI does are stale in 4 places.
- One plugin manifest reference is broken (F6, low impact).

No regression of any verified CLI invariant.

## Pre-tag checklist (incorporating both reviews)

1. **F1**: Add `## [1.0.0]` section to `CHANGELOG.md`.
2. **F2**: Rewrite `commands/init.md` to describe plugin-native flow.
3. **F3**: Update `commands/configure.md:126`.
4. **F4**: Update `AGENTS.md` Project Structure block.
5. **F5**: Update `CONTRIBUTING.md` Project Structure block + MCP
   description.
6. **F6**: Either populate `rules/cursor/` or drop the manifest
   declaration.
7. (From `review.md`) Open PR to `development` so CI 3-OS matrix
   runs.
8. (From `review.md`) Apply `[smoke]` label so SC-008 fixtures
   execute.
9. (From `review.md`) Tag v1.0.0 only after CI green.

Items 1-6 are docs-only fixes; they don't touch any Python code or
require new tests. ETA: under 1 hour for a focused commit.

## Command evidence (reproducible)

```
$ python -c "import json; data=json.loads(open('.claude-plugin/plugin.json').read()); print(len(data['agents']),'agents,',len(data['skills']),'skills,',len(data['commands']),'commands')"
13 agents, 124 skills, 27 commands

$ ls .claude-plugin .codex-plugin .cursor-plugin
.claude-plugin/marketplace.json  .claude-plugin/plugin.json
.codex-plugin/plugin.json
.cursor-plugin/plugin.json

$ wc -l rules/conventions/*.md rules/domain/*.md | tail -1
906 total  (max single rule 90 lines, under 100 budget)

$ find skills -name SKILL.md | wc -l
124

$ ls commands/*.md | wc -l
27

$ ls -la rules/cursor/
.gitkeep   # ONLY file

$ grep -nE "Copied: \{N\}|copies commands|re-copies commands|\.claude/commands|\.claude/rules" commands/*.md
commands/configure.md:126: ... re-copies commands ...
commands/init.md:34: ... copies commands/rules ...
commands/init.md:60: ... Number of commands copied
commands/init.md:76: ... .claude/commands/
commands/init.md:77: ... .claude/rules/
commands/init.md:106: ...   Copied: {N} commands
commands/init.md:107: ...   Copied: {N} rules

$ grep -nE "019|plugin-native|v1\.0\.0" CHANGELOG.md
169: ### Added (spec-017: Pre-Release v1.0.0 Hardening)
# (No feature-019 section.)
```

## Final verdict

**BLOCK-WITH-MINOR-FIXES** — the 6 findings above (1 HIGH, 3 MEDIUM,
1 MEDIUM, 1 LOW-MEDIUM) should be resolved before the v1.0.0 tag.

None are code defects. The Python implementation verified in
`review.md` is correct. The block is on user-visible documentation
and asset content that contradicts what the code now does.

If the maintainer prefers to ship 1.0.0 with the docs as-is and patch
in 1.0.1, F1 (CHANGELOG) is the only one I'd argue is genuinely
release-blocking because it's the canonical changelog entry the world
sees on the GitHub release page. F2-F6 can slip if the maintainer
chooses, but they're better fixed now while the implementation is
fresh.
