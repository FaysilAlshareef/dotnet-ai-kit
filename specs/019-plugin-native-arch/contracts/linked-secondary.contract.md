# Contract: Linked-Secondary-Repository Writer

**Spec source**: FR-033, SC-014, CP3/CP7 resolution, edge case "Linked secondary repositories"
**Implementation**: refactor `src/dotnet_ai_kit/copier.py:1090-1147` to consume `src/dotnet_ai_kit/hosts/<host>.write_secondary()` rather than its own copy paths

## Purpose

The existing primary→secondary repo writer at `copier.py:1090-1147` is the FR-033 "back door" — it bulk-copies commands, rules, skills, and agents into linked sibling repositories, preserving the legacy per-solution copy architecture. This contract refactors that writer to honor the plugin-native footprint.

## Refactor

### Before (current, FR-033 back door)

`copier.py:1090-1147` (per merged-findings line 92): the linked-repo writer iterates over linked repos in `ProjectMetadata.linked_repos` and writes commands, rules, skills, agents into each secondary's `.claude/` directory. Per-host footprint distinction is absent.

### After (per FR-033, host-adapter consumption)

The linked-repo writer iterates over linked repos, and for each, iterates over the configured hosts. For each host, it calls `hosts.<host>.write_secondary(secondary_path, project_metadata, primary_user_config)`:

- **Claude**: write only `.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`, `.claude/settings.json` permissions merge. NO commands/rules/skills/agents bulk copy.
- **Codex**: write only `.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`. NO root `AGENTS.md` (per FR-008 / A-008).
- **Cursor**: write only `.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`.
- **Copilot**: write only `.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`, plus Copilot renders at `.github/copilot-instructions.md`, `.github/instructions/<area>.instructions.md`, `.github/agents/<name>.agent.md` (matching primary's Copilot footprint).

Each file written is recorded in the secondary's own `.dotnet-ai-kit/manifest.json` with the appropriate `host_owner`.

## Secondary manifest semantics

- Each linked secondary repo has its own `.dotnet-ai-kit/manifest.json` (schema_version=2 going forward; v1 readable per R16 for legacy)
- Hash tracking, backup rotation, and migrate semantics work identically to primary

## Init behavior

Per spec FR-014 / clarify Q4: primary `init` triggers the interactive host-selection prompt. After primary init, the linked-repo writer iterates secondaries and calls each host's `write_secondary()` with the configured set. Secondaries are written ONLY when primary init explicitly requests linked-repo deployment (the user has opt-in to multi-repo via `project_metadata.linked_repos`).

## Migrate behavior

`dotnet-ai migrate` on a primary repo with linked secondaries:

1. Migrate the primary first (clean files → primary backup; user-modified preserved)
2. For each linked secondary, migrate the secondary in turn (clean files → secondary backup; user-modified preserved)
3. Each secondary's classification respects the secondary's own manifest

`dotnet-ai migrate --include-modified` propagates to secondaries.

## Tests (FR-033 / SC-014)

### `tests/unit/test_fr033_linked_secondary_init.py`

- Setup: primary repo + one linked secondary, both with `enabled_hosts=[claude, copilot]`
- Run `init` (or equivalent test fixture invocation)
- Assert: secondary contains `.dotnet-ai-kit/config.yml`, `.dotnet-ai-kit/project.yml`, `.claude/settings.json`, `.github/copilot-instructions.md`, etc.
- Assert: secondary does NOT contain `.claude/commands/`, `.claude/skills/`, `.claude/agents/` (the legacy back door)
- Assert: secondary's `.dotnet-ai-kit/manifest.json` has correct `host_owner` per file

### `tests/unit/test_fr033_linked_secondary_migrate.py`

- Setup: primary + one linked secondary, both with legacy v1 manifests (feature 018 layout)
- Run `migrate` on primary
- Assert: secondary's legacy artifacts moved to `.dotnet-ai-kit/backups/migrate/<timestamp>/` in the SECONDARY
- Assert: user-modified files in secondary preserved per FR-022
- Assert: secondary's manifest upgraded to v2

## What the linked-secondary writer MUST NOT do (per FR-033)

- MUST NOT bulk-copy commands, rules, skills, agents into secondaries for any plugin-supporting host
- MUST NOT preserve the v0 per-solution copy architecture as a back door
- MUST NOT skip the secondary's own manifest (every file written tracked)
- MUST NOT write to unmanaged paths in secondaries (FR-008 / A-008 applies per-secondary)

## CHK references

- CHK049 — linked-secondary writer refactored through `hosts/`
- CHK050 — secondary init does not create legacy copies
- CHK051 — secondary migrate cleans up legacy copies (subject to user-modified preservation)
- SC-014 — binding success criterion
