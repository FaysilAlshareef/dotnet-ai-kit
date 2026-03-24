# Data Model: Fix Permission System

**Feature**: 009-fix-permission-bypass
**Date**: 2026-03-25

## Entity: DotnetAiConfig (modified)

Existing pydantic v2 model in `models.py`. Add one new field:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `managed_permissions` | `list[str]` | `[]` | Permission entries managed by the tool. Used to diff during level changes so user-added entries are preserved. |

**Lifecycle**:
- Created: During `init` or `configure` when permissions are first applied
- Updated: On every `configure` or `upgrade` that changes permission level
- Read: During merge to identify tool-managed vs user-added entries
- Persisted: In `.dotnet-ai-kit/config.yml`

## Entity: Claude Code Settings File

JSON file at `.claude/settings.json` (project) or `~/.claude/settings.json` (global).

| Field Path | Type | Description |
|------------|------|-------------|
| `$schema` | `string` | Schema URL (optional, preserved if present) |
| `permissions.allow` | `list[string]` | Commands allowed without prompting |
| `permissions.deny` | `list[string]` | Commands always blocked (preserved, never modified) |
| `permissions.ask` | `list[string]` | Commands that always prompt (preserved, never modified) |
| `permissions.defaultMode` | `string` | Permission mode: set to `"bypassPermissions"` for full level, removed/unset for other levels |

**Merge rules**:
- `permissions.allow`: Tool manages its entries; user entries preserved
- `permissions.deny`: NEVER modified by the tool
- `permissions.ask`: NEVER modified by the tool
- `permissions.defaultMode`: Set/removed based on permission level
- All other top-level keys: Preserved as-is (e.g., `hooks`, `env`, `autoMode`)

## Entity: Permission Template

JSON files in `config/` directory. Three variants:

| Template | File | Entry Count | Mode |
|----------|------|-------------|------|
| Minimal | `permissions-minimal.json` | ~8 entries | default |
| Standard | `permissions-standard.json` | ~40 entries | default |
| Full | `permissions-full.json` | ~80+ entries | bypassPermissions |

**Relationship**: Template entries become `managed_permissions` in config.yml after application.

## State Transitions

```
[No permissions] → init/configure → [Level applied]
[Level applied] → configure (new level) → [Level changed, old entries removed, new applied]
[Old version config] → upgrade → [Level applied from existing config]
[Project level] → configure --global → [Global level applied]
```
