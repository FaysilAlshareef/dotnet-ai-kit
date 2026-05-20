# Contract: `dotnet-ai migrate` CLI

**Spec source**: FR-018, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, SC-007, US4
**Implementation**: `src/dotnet_ai_kit/cli.py` `migrate` command + `src/dotnet_ai_kit/manifest.py` (extended)

## Purpose

Manifest-driven cleanup of legacy per-solution copies. Reads `.dotnet-ai-kit/manifest.json` (v1 or v2 per R11/R16 backward-compat), classifies each managed file by content hash, moves clean files to a timestamped project-local backup, preserves user-modified files in place.

## CLI shape

```
dotnet-ai migrate [--dry-run] [--include-modified] [--host <host>]
```

| Flag | Behavior |
|--|--|
| `--dry-run` | Print classification report and the planned actions; do not move/delete any files. Constitution V mandates this. |
| `--include-modified` | Explicit user opt-in to remove user-modified files too. Default: preserve modified per FR-022 |
| `--host <host>` | Scope migration to files with `host_owner` = `<host>`. Default: all hosts. |

## Legacy manifest read behavior (per R11/R16)

`migrate` reads `manifest.json` and detects `schema_version`:

| Version | Behavior |
|--|--|
| `"1"` (feature 018) | Read all fields; infer `host_owner` per file from path patterns: `.claude/*` → claude, `.codex/*` → codex, `.cursor/*` → cursor, `.github/agents/*.agent.md` or `.github/copilot-instructions.md` or `.github/instructions/*.instructions.md` → copilot, otherwise `null` |
| `"2"` (feature 019) | Read `host_owner` directly from each file entry |

After a successful `migrate` operation that writes the manifest, the manifest is upgraded to v2 (writer always emits v2).

## Classification report (per FR-020 / SC-007)

For each file in `manifest.json.files`:

1. Compute current content hash if the file exists on disk
2. Compare with `manifest.files[*].sha256`:
   - **clean**: current hash matches manifest hash → move to backup (FR-021)
   - **user-modified**: current hash differs from manifest hash → preserve in place (FR-022); only removed if `--include-modified`
   - **missing**: file path no longer on disk → already gone; remove from manifest

## Output

### `--dry-run` output

```
dotnet-ai migrate (dry-run)
============================
Manifest: .dotnet-ai-kit/manifest.json (schema_version=1, inferred host_owners)

Planned actions:
  7 files MOVE to .dotnet-ai-kit/backups/migrate/20260517-180000/
    .claude/commands/dotnet-ai.do.md          [clean, host_owner=claude]
    .claude/commands/dai.do.md                [clean, host_owner=claude]
    .claude/skills/detect/SKILL.md            [clean, host_owner=claude]
    ... (4 more)
  
  2 files PRESERVE in place (user-modified):
    .claude/commands/my-customized.md         [host_owner=claude, hash mismatch]
    .claude/agents/dotnet-architect.md        [host_owner=claude, hash mismatch]

  1 file already missing (will be removed from manifest):
    .claude/skills/old-skill/SKILL.md         [host_owner=claude]

To apply, run: dotnet-ai migrate
To also remove user-modified files: dotnet-ai migrate --include-modified
```

### Apply output

Same structure; "Planned actions" → "Applied actions"; backup folder path printed; manifest updated to v2.

## Backup behavior (FR-021, FR-023)

- Backup folder: `.dotnet-ai-kit/backups/migrate/<YYYYMMDD-HHMMSS>/` (project-local)
- 3-keep rotation: oldest backup folder removed when a 4th is created
- Each entry preserves the file's original repo-root-relative path under the backup folder (e.g., `backups/migrate/20260517-180000/.claude/commands/dotnet-ai.do.md`)

## What `migrate` MUST NOT do

- MUST NOT re-render Copilot files (FR-024 — that's `upgrade --copilot`'s job)
- MUST NOT delete user-modified files without `--include-modified` (FR-022)
- MUST NOT touch unmanaged paths (FR-008 / A-008)
- MUST NOT make outbound network calls (A-011)
- MUST NOT delete files outright; always move to backup (FR-021)

## What `init --force` MUST do (FR-025)

`init --force` detects shadowed legacy artifacts. It MUST NOT auto-delete them. Instead it MUST print the exact `dotnet-ai migrate` invocation:

```
Detected legacy artifacts shadowed by the new architecture:
  - .claude/commands/dotnet-ai.do.md (managed)
  - .claude/skills/detect/SKILL.md (managed)
  - ... (5 more)

Run: dotnet-ai migrate --dry-run  # to preview
     dotnet-ai migrate            # to apply

`init --force` will NOT auto-migrate to preserve the no-silent-cleanup rule.
```
