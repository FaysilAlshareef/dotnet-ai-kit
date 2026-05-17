# Phase 1 Data Model: Plugin-Native Architecture

**Branch**: `019-plugin-native-arch` | **Date**: 2026-05-17 | **Plan**: [plan.md](./plan.md)

This file enumerates every entity introduced or modified by the plugin-native architecture feature. Field shapes are pydantic-v2-ready; JSON Schema artifacts live in `contracts/`.

## 1. `PluginManifest` (3 variants)

Each plugin-supporting host has its own manifest schema. Manifests share a small common surface (name, version, description) and diverge on supported primitives.

### 1a. `ClaudePluginManifest` (`.claude-plugin/plugin.json`)

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string | yes | `dotnet-ai-kit` |
| `version` | string | yes | semver; matches `src/dotnet_ai_kit/__init__.py:__version__` |
| `description` | string | yes | short marketing line |
| `agents` | array of paths | yes (NEW for this feature) | references `agents-claude/*.md` per FR-026 |
| `skills` | array of paths | yes | references `skills/**/SKILL.md` |
| `commands` | array of paths | yes | references `commands/*.md` |
| `hooks` | object | yes | references `hooks/hooks.json` |
| `mcpServers` | object | yes | references `.mcp.json`; v1 keeps `codebase-memory-mcp` only after commit 12 |
| `lspServers` | object | yes (NEW for this feature) | references `csharp-lsp` plugin per FR-028 |
| `outputStyles` | array | optional | unused in v1 |
| `dependencies` | array | yes (NEW for this feature) | includes `csharp-lsp` per commit 11 |
| `userConfig` | object | optional | per architecture-phase R-resolution |
| `channels` | array | optional | unused in v1 |

### 1b. `CodexPluginManifest` (`.codex-plugin/plugin.json`)

Per Codex docs `https://developers.openai.com/codex/plugins/build:843-860`, manifest field values are **scalar relative path strings with the `./` prefix** (not arrays/objects).

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string | yes | `dotnet-ai-kit` |
| `version` | string | yes | semver |
| `description` | string | yes | |
| `interface` | string | optional | metadata field per Codex docs |
| `skills` | string (path) | yes | `"./skills/"` — scalar relative path |
| `mcpServers` | string (path) | yes | `"./.mcp.json"` |
| `hooks` | string (path) | yes | `"./hooks/hooks.json"` |
| `apps` | string (path) | optional | unused in v1 |
| `assets` | string (path) | optional | unused in v1 |

**Fields explicitly NOT present**: `agents` (OOS-004), `lspServers`, `monitors`, `settings`, `bin` (not documented by Codex CLI; FR-002 forbids inclusion).

### 1c. `CursorPluginManifest` (`.cursor-plugin/plugin.json`)

Per the verified working example at `https://raw.githubusercontent.com/cursor/plugins/main/agent-compatibility/.cursor-plugin/plugin.json`, manifest fields are **scalar relative path strings with `./` prefix**. The agent-bearing field is `agents` (NOT `subagents`) and the verified path is `./agents/` at the plugin root.

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string | yes | `dotnet-ai-kit` |
| `version` | string | yes | semver |
| `description` | string | yes | |
| `skills` | string (path) | yes | `"./skills/"` |
| `rules` | string (path) | yes | `"./rules/cursor/"` — generated `.mdc` files |
| `mcpServers` | string (path) | yes | `"./.mcp.json"` |
| `hooks` | string (path) | yes | `"./hooks/hooks.json"` |
| `agents` | string (path) | conditional | `"./agents/"` — conditional on A-005 spike fixture passing. If fixture fails, this field MUST be absent and `cursor-fixture-decision.contract.md` binding rule triggers. |

## 2. `ProjectMetadata` (`.dotnet-ai-kit/project.yml`)

Per-solution descriptor. Validated against `contracts/project-yml.schema.json` per FR-017 / CHK013. Resolved at runtime by skills, rules, SessionStart hook, and PreToolUse hook (FR-009, FR-010, FR-034).

| Field | Type | Required | Validation | Notes |
|--|--|--|--|--|
| `company` | string | yes | non-empty | e.g., `Contoso` |
| `domain` | string | yes | non-empty | e.g., `Sales` |
| `side` | enum `server` \| `client` | yes | | |
| `project_type` | enum (12 values) | yes | one of: `command`, `query-sql`, `query-cosmos`, `processor`, `gateway`, `controlpanel`, `hybrid`, `vsa`, `clean-arch`, `ddd`, `modular-monolith`, `generic` | clarify Q1 binding; matches existing `models.py:88-99` |
| `architecture_branch` | enum `microservice` \| `generic` | yes | derived from `project_type` | `command/query-sql/query-cosmos/processor/gateway/controlpanel/hybrid` → `microservice`; others → `generic` |
| `detected_paths` | object (string→string) | yes | non-empty values | runtime-resolved by skills |
| `architecture_profile_name` | string | optional | references existing profile in `profiles/<branch>/<name>.md` | drives PreToolUse hook output per FR-034 |
| `dotnet_version` | string | yes | semver subset | e.g., `8.0`, `9.0`, `10.0` |
| `linked_repos` | array of objects | optional | per-entry: `name`, `path`, `hosts` | constrains FR-033 / SC-014 |

## 3. `UserConfig` (`.dotnet-ai-kit/config.yml`)

Per-solution descriptor of the developer's tool preferences. Validated against `contracts/config-yml.schema.json`. Pydantic reader accepts the legacy `ai_tools` field name (used in pre-019 code at `copier.py:1096-1100`) and maps it to `enabled_hosts` on read; writer always emits `enabled_hosts`.

| Field | Type | Required | Validation | Notes |
|--|--|--|--|--|
| `enabled_hosts` | array of enum | yes | subset of `claude`, `codex`, `cursor`, `copilot` | from clarify Q4 interactive selection. Pydantic reader accepts legacy `ai_tools` as alias. |
| `retention` | int | optional | default 3 | matches feature 018's backup rotation |
| `permission_profile` | enum | optional | one of `minimal`, `standard`, `full`, `mcp` | matches existing `config/` JSON files |
| `plugin_version` | string | yes | semver | recorded at init for migrate detection |

## 4. `ManagedFile` (entry in `.dotnet-ai-kit/manifest.json`)

Extended from feature 018's `DeployedFile`. The extension adds `host_owner` for per-host migration scoping (R11). Field is **optional-on-read** (legacy v1 manifests lack it; inferred from path patterns) and **required-on-write** (new v2 manifests must include it).

| Field | Type | Required (write) | Required (read) | Notes |
|--|--|--|--|--|
| `path` | string | yes | yes | repo-root-relative path |
| `sha256` | string | yes | yes | hex digest of file content at deploy time |
| `plugin_version` | string | yes | yes | semver at deploy time |
| `deployed_at` | datetime (UTC) | yes | yes | ISO 8601 |
| `source_template` | string \| null | optional | optional | jinja2 template path that produced this file, for Copilot renders |
| `host_owner` | enum \| null | yes | inferred-if-absent | `claude` \| `codex` \| `cursor` \| `copilot` \| `null`. Reader infers from path patterns when reading legacy v1 manifests (per R11/R16). |

## 5. `Manifest` (`.dotnet-ai-kit/manifest.json`)

Schema versioned per R11/R16. Reader accepts v1 (feature 018, `schema_version="1"`) and v2 (feature 019, `schema_version="2"`). Writer always emits v2.

| Field | Type | Required | Notes |
|--|--|--|--|
| `schema_version` | string (enum `"1"` \| `"2"`) | yes | Determines reader behavior. Currently feature 018 writes `"1"` (per `src/dotnet_ai_kit/cli.py:433-438`); feature 019 writer emits `"2"`. |
| `plugin_version` | string | yes | initialized at first `init` |
| `created_at` | datetime (UTC) | yes | first `init` timestamp |
| `last_upgrade_at` | datetime (UTC) \| null | optional | most recent successful upgrade |
| `last_migrate_at` | datetime (UTC) \| null | optional | most recent successful migrate (v2 only) |
| `files` | array of `ManagedFile` | yes | full list of files the tool wrote |

## 6. `MigrationBackup` (entry in `.dotnet-ai-kit/backups/migrate/<timestamp>/`)

Records what `migrate` moved aside in a single run.

| Field | Type | Required | Notes |
|--|--|--|--|
| `timestamp` | datetime (UTC) | yes | folder name `<YYYYMMDD-HHMMSS>` |
| `entries` | array of `MigrationBackupEntry` | yes | one per file moved |
| `unmoved_user_modified` | array of strings | yes | repo-root-relative paths preserved in place per FR-022 |

### `MigrationBackupEntry`

| Field | Type | Required | Notes |
|--|--|--|--|
| `original_path` | string | yes | where the file was before migrate |
| `backup_path` | string | yes | inside the backup folder |
| `original_sha256` | string | yes | for safety verification on restore |
| `classification` | enum `clean` \| `user-modified` | yes | per FR-020 |
| `host_owner` | enum \| null | yes | per `ManagedFile.host_owner` |

## 7. `Agent` (source-of-truth definition in `agents-source/<name>.md`)

The source markdown body per logical agent, per FR-026. Located in `agents-source/` after round-3 P2 rename (was `agents/` pre-019; the `agents/` directory now serves as Cursor build output per the verified Cursor manifest path). Host-specific files are generated by `agent_generators.py` per `contracts/agent-source.contract.md`. The markdown body is the document body (everything after the closing `---`), NOT a frontmatter field.

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string (frontmatter) | yes | e.g., `dotnet-architect` |
| `description` | string (frontmatter) | yes | short description |
| `host_overrides` | object (host→object, frontmatter) | optional | per-host frontmatter allow-list overrides; unsupported fields per host are rejected at generator time per FR-027. See `contracts/agent-source.contract.md` for allow-list per host. |
| (body) | markdown | yes | document body after closing `---`. Used verbatim by all generators (Claude, Cursor, Copilot). |

## 8. `Rule` (subtypes)

Two distinct subtypes per spec FR-011.

### 8a. `ConventionRule` (always-on, exactly 5 instances)

Located at `rules/conventions/<name>.md`. Whitelist (FR-011): `async-concurrency`, `coding-style`, `existing-projects`, `security`, `tool-calls`.

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string | yes | matches the file name without `.md` |
| `body` | markdown | yes | ≤100 lines per Constitution V |

### 8b. `DomainRule` (just-in-time, exactly 11 instances)

Located at `rules/domain/<name>.md`. Whitelist (FR-011): `api-design`, `architecture`, `configuration`, `data-access`, `error-handling`, `localization`, `multi-repo`, `naming`, `observability`, `performance`, `testing`.

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string | yes | matches the file name without `.md` |
| `body` | markdown | yes | ≤100 lines per Constitution V |
| `loads_when` | string (paths or skill scope) | yes | describes when the rule should be loaded |

## 9. `ArchitectureProfile`

Located at `profiles/<branch>/<name>.md`. Twelve instances per clarify Q1.

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string | yes | one of 12 from `models.py:88-99` |
| `branch` | enum `microservice` \| `generic` | yes | |
| `body` | markdown | yes | ≤100 lines per Constitution V |
| `loads_at` | enum `pretooluse` \| `lazy` | yes | profiles load at PreToolUse hook fire-time per FR-034 |

## 10. `SmokeFixture` (per plugin host)

The minimal artifact used as the merge-gate per FR-029 / SC-008. Three instances in v1.

| Field | Type | Required | Notes |
|--|--|--|--|
| `host_name` | enum `claude` \| `codex` \| `cursor` | yes | |
| `fixture_path` | string | yes | source-repo path of the fixture file |
| `expected_listing_path` | string | yes | host-CLI output to grep for fixture's presence (per docs) |
| `verification_command` | string | yes | the test invocation that asserts fixture is listed |

## 11. `LinkedSecondaryRepo`

Constrained by FR-033 / SC-014. Each entry corresponds to a row in `ProjectMetadata.linked_repos`.

| Field | Type | Required | Notes |
|--|--|--|--|
| `name` | string | yes | logical name |
| `path` | string | yes | filesystem path (absolute or relative to primary) |
| `hosts` | array of enum | yes | hosts to deploy in this linked repo (subset of `UserConfig.enabled_hosts`) |

## 12. `HookConfig` (entries in `hooks/hooks.json`)

`hooks/hooks.json` is an event-keyed object (NOT a flat array), matching the actual current shape at `hooks/hooks.json:2-60` and Codex docs at `https://developers.openai.com/codex/plugins/build:930-955`. Top-level keys: `SessionStart`, `PreToolUse`, `PostToolUse`.

| Hook script | Event key | Matcher / if | Notes |
|--|--|--|--|
| `session-start-bootstrap.sh` | `SessionStart` | (none) | REPLACED in commit 13; outputs ≤500 token compact bootstrap per SC-013 / FR-013 |
| `pretooluse-arch-profile.sh` | `PreToolUse` | (matcher TBD per commit 13 design) | NEW in commit 13; reads `project.yml` at fire-time per FR-034 |
| `pre-bash-guard.sh` | `PreToolUse` | `matcher: "Bash"` | UNCHANGED from feature 018 |
| `pre-commit-lint.sh` | `PreToolUse` | `matcher: "Bash"`, `if: "Bash(git commit*)"` | UNCHANGED from feature 018 |
| `post-edit-format.sh` | `PostToolUse` | `matcher: "Edit\|Write"`, `if: "Edit(*.cs)" \| "Write(*.cs)"` | UNCHANGED from feature 018 |
| `post-scaffold-restore.sh` | `PostToolUse` | `matcher: "Bash"`, `if: "Bash(dotnet new*)"` | UNCHANGED from feature 018 |

## State transitions

### `Manifest` lifecycle

```
[no manifest]
    │
    │ `dotnet-ai init` (commit 4 onward)
    ▼
[Manifest v1.0]  ──── `dotnet-ai upgrade` (no-op for plugin hosts) ────► [Manifest v1.0]
    │                                                                        │
    │ `dotnet-ai upgrade --copilot`                                           │
    ▼                                                                        │
[Manifest v1.0, Copilot files re-rendered]                                   │
    │                                                                        │
    │ `dotnet-ai migrate`                                                     │
    ▼                                                                        │
[Manifest v1.0, legacy files moved to .dotnet-ai-kit/backups/migrate/]       │
    │                                                                        │
    └────────────────────────────────────────────────────────────────────────┘
```

### `MigrationBackup` lifecycle

```
[before migrate]
    │
    │ `dotnet-ai migrate` (commit 10)
    ▼
[backup folder created: .dotnet-ai-kit/backups/migrate/<timestamp>/]
    │
    │ classification: clean files moved; user-modified preserved in place
    ▼
[backup folder rotated: 3-keep retention applied; oldest folders deleted]
    │
    │ (reversal — manual: user copies file from backup folder back to repo)
    ▼
[file restored]
```

### `SmokeFixture` lifecycle (per host)

```
[fixture file in source repo]
    │
    │ commit 6 (or commit 3 for Claude/Codex)
    ▼
[fixture in plugin manifest's primitives field]
    │
    │ host installs plugin (via host-native install path)
    ▼
[fixture appears in host's listing]
    │
    │ CI smoke test asserts presence
    ▼
[PASS → merge gate satisfied / FAIL → A-005 trigger for Cursor; merge blocked for Claude/Codex]
```

## Cross-entity invariants

- Every `ManagedFile` MUST have a `host_owner` that matches a value in the corresponding solution's `UserConfig.enabled_hosts`, or `null` for non-host-specific files.
- Every `MigrationBackupEntry.original_path` MUST appear in the source `Manifest.files` (otherwise the file was not managed and should not have been touched by `migrate`).
- The set of `ConventionRule` instances MUST be exactly the 5 names in FR-011's whitelist; the set of `DomainRule` instances MUST be exactly the 11 names. CHK031 / CHK032 enforce this.
- Every `ArchitectureProfile.name` MUST be one of the 12 values from `models.py:88-99` (clarify Q1).
- `ProjectMetadata.architecture_branch` MUST be consistent with `project_type` per the derivation rule above (validated at schema load).
- Every linked secondary repo MUST honor FR-033: no legacy copies in any sibling's working tree after `init` or `migrate`.

## File-system layout summary

```
.claude-plugin/plugin.json   ┐
.codex-plugin/plugin.json    ├── plugin manifests (commits 1-3, 11)
.cursor-plugin/plugin.json   ┘

agents-source/<name>.md      ── source-of-truth (renamed from agents/ in commit 4 per round-3 P2)
agents-claude/<name>.md      ── Claude-format build output (commit 4)
agents/<name>.md             ── Cursor-format build output (commit 6, conditional on A-005). Referenced by .cursor-plugin/plugin.json "agents": "./agents/" per verified Cursor evidence.
agents-copilot-templates/    ── jinja2 templates for per-project Copilot render (commit 7)

rules/conventions/<5 files>  ── always-on (commit 14)
rules/domain/<11 files>      ── JIT (commit 14)
rules/cursor/*.mdc           ── generated (commit 6)

profiles/microservice/<7>    ── existing (clarify Q1)
profiles/generic/<5>         ── existing (clarify Q1)

hooks/hooks.json             ── 6 entries (commit 13)
hooks/*.sh                   ── 6 scripts (4 unchanged + 2 new in commit 13)

schemas/*.schema.json        ── 7 contract files (commits 3, 8)

.mcp.json                    ── modified in commit 12 (csharp-ls removed)
.dotnet-ai-kit/              ── per-project deployment artifact (post-init)
  ├── config.yml             ── UserConfig
  ├── project.yml            ── ProjectMetadata
  ├── manifest.json          ── Manifest
  ├── backups/upgrade/<...>/ ── existing (feature 018)
  └── backups/migrate/<...>/ ── new (commit 10; FR-021)
```
