# Quickstart: Fix Permission System

**Feature**: 009-fix-permission-bypass
**Date**: 2026-03-25

## Implementation Order

### Step 1: Add `managed_permissions` field to DotnetAiConfig

**File**: `src/dotnet_ai_kit/models.py`

Add a `managed_permissions: list[str]` field with default `[]`. This tracks which permission entries the tool wrote, enabling clean diffs when the level changes.

### Step 2: Expand permission template files

**Files**: `config/permissions-full.json`, `config/permissions-standard.json`

Expand `permissions-full.json` to ~80+ entries covering all common dev commands. Add `defaultMode: bypassPermissions` to the full template. Add ~15 missing commands to standard template (grep, find, head, tail, wc, etc.).

### Step 3: Add `copy_permissions()` and `merge_permissions()` to copier.py

**File**: `src/dotnet_ai_kit/copier.py`

Two new functions:
- `merge_permissions(existing_settings, template_entries, managed_entries, level)` — pure function that computes the merged settings dict
- `copy_permissions(target_dir, config, package_dir, global_install=False)` — reads template, loads existing settings, calls merge, writes result

### Step 4: Wire into CLI commands

**File**: `src/dotnet_ai_kit/cli.py`

- `init`: Call `copy_permissions()` after copying commands/rules/skills
- `configure`: Call `copy_permissions()` after saving config
- `upgrade`: Detect missing permissions and apply

Add `--global` flag to `configure` command.

### Step 5: Add one-time bypass warning

**File**: `src/dotnet_ai_kit/cli.py`

When `permissions_level == "full"`, display a rich Panel warning before applying.

### Step 6: Write tests

**Files**: `tests/test_copier.py`, `tests/test_cli.py`

Test cases:
- `merge_permissions` with empty settings (fresh project)
- `merge_permissions` with existing user entries (preserved)
- `merge_permissions` level change (old entries removed, new added)
- `merge_permissions` preserves deny/ask rules
- `copy_permissions` creates `.claude/settings.json` if missing
- `copy_permissions` with `global_install=True` targets home dir
- Full level sets `bypassPermissions` mode
- Standard level does NOT set `bypassPermissions`
- Invalid JSON handling (error reported, file not overwritten)

## Key Design Decisions

1. **`merge_permissions` is a pure function** — takes dicts, returns dict. Easy to test without filesystem.
2. **`copy_permissions` handles I/O** — reads/writes files, calls merge.
3. **Template files are the source of truth** — never hardcode permission entries in Python code.
4. **`managed_permissions` in config.yml** — the diff anchor for merge operations.
5. **Full level = bypass mode + comprehensive allow-list** — bypass handles everything, allow-list is documentation + fallback for downgrades.
