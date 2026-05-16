# Phase 1 Data Model — Fix Token Burn

**Feature**: `018-fix-token-burn` | **Date**: 2026-05-16
**Source plan**: [plan.md](./plan.md) §Project Structure
**Source spec entities**: [spec.md](./spec.md) §Key Entities

## Entities

### 1. `DeployedFile` (manifest entry)

Represents a single file that dotnet-ai-kit deployed into a target project. The unit of identity for the atomic-upgrade rollback path (FR-031, FR-032).

| Field | Type | Required | Notes |
|---|---|---|---|
| `path` | `str` | yes | Project-relative path with forward slashes; e.g. `.claude/skills/api/controllers/SKILL.md`. Normalised by `pathlib.PurePosixPath`. |
| `sha256` | `str` | yes | 64-char lowercase hex SHA-256 of the file's bytes at the moment of deployment. Used to detect user modifications during `/dai.upgrade`. |
| `plugin_version` | `str` | yes | Value of `dotnet_ai_kit.__version__` at deployment time. Used to spot files deployed by older plugins. |
| `deployed_at` | `datetime` (ISO-8601, UTC) | yes | Wall-clock timestamp when the bytes were written. Tie-breaker for diagnostics. |
| `source_template` | `str \| None` | optional | Path within the plugin repo (e.g. `skills/api/controllers/SKILL.md`) that this file was rendered from. `None` for files with no template origin (e.g. generated `config.yml`). |

**Validation rules**:
- `path` MUST NOT contain `..` segments after normalisation (FR-031 safety).
- `sha256` MUST match `^[0-9a-f]{64}$`.
- `plugin_version` MUST match `pyproject.toml`'s version regex (`^\d+\.\d+\.\d+(\.\d+)?$`).
- `deployed_at` MUST be timezone-aware (UTC).

**State transitions**: immutable. A new `DeployedFile` is written whenever the file is (re-)deployed; old entry is replaced.

### 2. `Manifest`

Single-file root container for the project's manifest. Lives at `.dotnet-ai-kit/manifest.json` (FR-032).

| Field | Type | Required | Notes |
|---|---|---|---|
| `plugin_version` | `str` | yes | Plugin version at last write. Convenience denormalisation; individual `files[].plugin_version` is the truth per file. |
| `schema_version` | `str` | yes | Manifest schema version. Starts at `"1"`. Bumped if the manifest shape itself changes. |
| `created_at` | `datetime` (ISO-8601, UTC) | yes | First write of this manifest (set on `/dai.init`). |
| `last_upgrade_at` | `datetime \| None` | optional | Set by `/dai.upgrade`; `None` until the first upgrade lands. |
| `files` | `list[DeployedFile]` | yes | All managed files. Empty list permitted (post-init, pre-deploy). |

**Validation rules**:
- `files` MUST contain no duplicate `path` values.
- `created_at` ≤ `last_upgrade_at` if both set.
- File is JSON-serialisable via `pydantic.BaseModel.model_dump_json(indent=2)`. Forward slashes preserved on Windows.

**State transitions**:
- Created on `/dai.init` (empty `files`).
- Updated on every `/dai.init`, `/dai.upgrade`, `/dai.configure` deployment.
- Atomic write: write to `.dotnet-ai-kit/manifest.json.tmp`, then `replace()`.

### 3. `UpgradeBackup`

In-memory model that mirrors a backup record on disk under `.dotnet-ai-kit/backups/upgrade/<run_id>/`. Used by `src/dotnet_ai_kit/upgrade.py` for atomic rollback (FR-031, SC-013).

| Field | Type | Required | Notes |
|---|---|---|---|
| `original_path` | `Path` | yes | Project-relative path of the file being backed up before overwrite. |
| `original_sha256` | `str` | yes | SHA-256 of the original bytes. Used to verify the restore matched what was there. |
| `backup_path` | `Path` | yes | Absolute path under `.dotnet-ai-kit/backups/upgrade/<run_id>/`. Mirrors `original_path` structure. |
| `restored` | `bool` | yes (default `False`) | Set to `True` after a successful restore during rollback. |

**Validation rules**:
- `backup_path` MUST exist and be readable before `restored` can transition to `True`.
- `original_sha256` after restore MUST match the value at backup time.

**State transitions**:
- Created when a managed file is about to be overwritten (before any write).
- Marked `restored = True` after successful rollback.
- Persisted only for the duration of an upgrade run; the backup directory is retained on rollback for human inspection. Last 3 successful-or-rolled-back run directories kept; older rotated.

**Disk layout**:

```
.dotnet-ai-kit/backups/upgrade/
└── 2026-05-16T14-30-00Z-<uuid4>/
    ├── manifest-pre.json                  # copy of pre-run manifest
    ├── .claude/rules/api-design.md        # mirror-of-tree backups
    ├── .claude/skills/...
    └── _meta.json                         # run metadata: started_at, ended_at, status (success/rolled-back), failing_file
```

### 4. `MCPHealth`

In-memory result of `codebase-memory-mcp` runtime detection. Produced by `src/dotnet_ai_kit/mcp_check.py` (FR-019, FR-035).

| Field | Type | Required | Notes |
|---|---|---|---|
| `server_name` | `str` | yes | Fixed string `"codebase-memory-mcp"`. |
| `present` | `bool` | yes | `True` if `codebase-memory-mcp --version` succeeded with exit 0. |
| `version` | `str \| None` | optional | Parsed semver from `--version` stdout. `None` if `present=False` or parse failed. |
| `min_required` | `str` | yes | Plugin-side constant; currently `"0.6.1"`. |
| `meets_minimum` | `bool` | yes | `True` iff `present` AND `version >= min_required` (semver comparison). |

**Validation rules**:
- `version` MUST match `^\d+\.\d+\.\d+(?:-[\w.]+)?$` if non-`None`.
- Semver comparison uses `packaging.version.Version` to avoid lexical pitfalls.

**State transitions**: ephemeral. Recreated each time `mcp_check.run()` is called.

---

## Relationships

```text
Manifest ──┬── files: list[DeployedFile]
           │
           └── (logical: every DeployedFile's path is one of the plugin's managed paths)

UpgradeBackup (×N)        — created during /dai.upgrade per file about to change
   │
   └── reads from Manifest.files to know which files to back up

MCPHealth                 — standalone, queried by /dai.init, the 7 operational commands, and the fallback notice emitter
```

No persistent relational store. All entities serialise to JSON or live in-memory only.

---

## Validation Rules Cross-Reference

| Rule | Source | Enforced by |
|---|---|---|
| `path` no `..` segments | FR-031 safety | `manifest.py` pydantic field validator |
| `sha256` 64 hex chars | FR-032 | `manifest.py` regex validator |
| Manifest no duplicate paths | FR-032 | `manifest.py` model validator |
| Backup path mirrors source | implementation invariant | `upgrade.py` deploy phase |
| `version >= min_required` semver | FR-019 | `mcp_check.py` `Version` comparison |
| `${detected_paths.X}` resolves OR aborts (no empty/broad substitution) | FR-033 | `copier.py::_substitute_paths()` |
| `manifest.json` write is atomic | FR-032 invariant | `manifest.py::save()` via `tmp + replace` |

---

## Schemas

JSON Schema for `Manifest` is published at `contracts/manifest.schema.json` (Phase 1 contract). YAML frontmatter contracts for skills and rules at `contracts/skill-frontmatter.schema.yaml` and `contracts/rule-frontmatter.schema.yaml`. Hook config and MCP config contracts at `contracts/hooks.schema.json` and `contracts/mcp.schema.json`.
