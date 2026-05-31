# Contract: User-owned-file policy (FR-022-13/14)

How `init`/`upgrade` treat files a user may have edited, and how the outcome is reported.

## Classification

| Class | Files | Default action |
|---|---|---|
| **Managed** | `.dotnet-ai-kit/*` (config/project/manifest/version), `.claude/rules/*.md` | always (re)written |
| **User-owned** | `.claude/settings.json`, `AGENTS.md`, `.cursor/rules*`, `.github/*` | merge / preserve / consent (below) |

## Decision table (user-owned)

| State | Action | `HostWriteResult` |
|---|---|---|
| absent | write | `Written` |
| present, byte-equals last managed render | refresh | `ForceRendered` (refreshed) |
| present, user-edited, **JSON deep-merge possible** (`settings.json`) | merge managed keys into user file | `Preserved` (merged) |
| present, user-edited, not safely mergeable | back up (3-keep) + diff-preview + leave user file | `PendingConsent` (+ `BackupPath`) |
| present, invalid JSON | back up + warn, do not discard | `PendingConsent` (+ `BackupPath`) |

- Deep-merge is deterministic: managed keys added/updated; user keys never dropped; arrays union by value where unambiguous, else `PendingConsent`.
- Backups reuse `BackupRotationService` (3-keep, NFR-7).
- `--force` (where offered) downgrades a merge/consent to overwrite-after-backup and reports `ForceRendered`.

## Invariant

A pre-existing user-edited `.claude/settings.json` MUST survive `init` (content preserved or merged, never silently clobbered) and the action MUST appear in `HostWriteResult` (SC-022-5). No user-owned write is silent.
