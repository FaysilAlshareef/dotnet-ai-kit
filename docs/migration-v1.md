# Migration Guide — dotnet-ai-kit v1.0

**Feature**: 019-plugin-native-arch | **Date**: 2026-05-18

Quick reference for upgrading a pre-019 (`~180-file footprint`) project to
v1.0 plugin-native architecture.

## When to run `dotnet-ai migrate`

Run `migrate` when:
- You have a pre-019 project with `.claude/commands/`, `.claude/skills/`,
  `.claude/rules/`, `.claude/agents/`, `.cursor/`, etc. directories populated
  by an old `dotnet-ai init`.
- You've upgraded the plugin to v1.0 and the new plugin install path now
  serves those assets — making the per-solution copies redundant.
- `dotnet-ai check` reports stale manifest entries or files that no longer
  match the new architecture.

## What `migrate` does

For each file in `.dotnet-ai-kit/manifest.json`:
- **clean** (SHA-256 matches manifest): MOVE to
  `.dotnet-ai-kit/backups/migrate/<YYYYMMDD-HHMMSS>/`
- **user-modified** (hash differs): PRESERVE in place by default; the
  `--include-modified` flag opts in to moving them too
- **missing** (file no longer on disk): remove from manifest

The manifest schema is upgraded from v1 (feature 018) to v2 (feature 019)
with `host_owner` per file (inferred from path patterns for legacy v1
entries per research R16).

## What `migrate` does NOT do

Per FR-024 / FR-022 / FR-021:
- MUST NOT re-render Copilot files — that's `dotnet-ai upgrade --copilot`'s
  job
- MUST NOT delete user-modified files without `--include-modified` opt-in
- MUST NOT touch paths outside the formally-managed manifest (per
  FR-008 / A-008 — see CHK026 for the unmanaged-paths-untouched rule)
- MUST NOT delete files outright — every removal goes to a backup folder

## Interaction with `upgrade --copilot`

`dotnet-ai migrate` and `dotnet-ai upgrade --copilot` are intentionally
separate:

| Command | Purpose | Scope |
|--|--|--|
| `migrate` | Clean up legacy per-solution copies | All hosts (via host_owner) |
| `upgrade --copilot` | Re-render Copilot files with current project.yml | Copilot only |

After running `migrate`, if Copilot's `.github/*.md` renders are stale
(per `dotnet-ai check`), run `dotnet-ai upgrade --copilot` (or
`dotnet-ai upgrade --copilot --force-render <path>` for a specific
overwrite per FR-008 path-specific opt-in).

## How to reverse a migration

Each migrate creates a backup folder named after the timestamp. To reverse:

1. Inspect the backup folder: `ls .dotnet-ai-kit/backups/migrate/`
2. Copy files from the backup folder back to their original paths:
   ```
   cp -r .dotnet-ai-kit/backups/migrate/<timestamp>/.claude .
   cp -r .dotnet-ai-kit/backups/migrate/<timestamp>/.cursor .
   ```
3. Manually restore the manifest entries (the backup folder preserves the
   original `path` for each entry under
   `MigrationBackupEntry.original_path`).

The 3-keep rotation (FR-023) means the **3 most recent** migrations are
recoverable. Older backups are removed automatically when a 4th migrate
runs.

## Typical workflow

```sh
# 1. Verify upgrade prerequisites
dotnet-ai check

# 2. Preview the migration (no mutations)
dotnet-ai migrate --dry-run

# 3. Apply the migration (clean files MOVE to backup; user-modified PRESERVED)
dotnet-ai migrate

# 4. Refresh Copilot renders separately if you use Copilot
dotnet-ai upgrade --copilot

# 5. Verify post-migration state
dotnet-ai check
```

## CLI surface summary

```
dotnet-ai migrate [--dry-run] [--include-modified] [--host <host>] [<project-path>]
```

| Flag | Behavior |
|--|--|
| `--dry-run` | Print classification report + planned actions; do not mutate. |
| `--include-modified` | Also move user-modified files to backup (default: PRESERVE in place). |
| `--host <host>` | Scope migration to files with `host_owner == <host>`. Default: all hosts. |

Per `contracts/migrate-cli.contract.md`.
