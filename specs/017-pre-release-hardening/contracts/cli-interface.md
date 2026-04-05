# CLI Interface Contract: Pre-Release v1.0.0 Hardening

**Phase**: 1 — Contracts
**Date**: 2026-04-04

Documents all CLI interface changes introduced in this feature.

---

## 1. `dotnet-ai init` — New `--permissions` flag

### Before
```
dotnet-ai init [PATH] [--ai TOOL...] [--type TYPE] [--force] [--dry-run] [--json]
```

### After
```
dotnet-ai init [PATH] [--ai TOOL...] [--type TYPE] [--permissions LEVEL]
               [--force] [--dry-run] [--json]
```

**New flag**:

| Flag | Type | Default | Valid values | Description |
|------|------|---------|-------------|-------------|
| `--permissions` | `str` | `None` | `minimal`, `standard`, `full` | Apply permission level during init. If omitted, uses config default or defers to `configure`. |

**Behaviour change**:
- When `--permissions` is provided: sets `config.permissions_level` before config save; calls `copy_permissions()` during init (same path as configure)
- Invalid value: typer error `"Invalid value for '--permissions': ..."`, exit code 2
- Interacts with `--dry-run`: permission level is set in preview but `copy_permissions()` is NOT called

---

## 2. `dotnet-ai changelog` — New command

```
dotnet-ai changelog
```

**No flags**.

**Behaviour**:
1. Call `_get_package_dir()` to locate asset root
2. If `CHANGELOG.md` exists there: print its contents to console; exit 0
3. Else: run `git tag --sort=-version:refname` (no stderr capture — if git missing, no output)
4. Take first 5 tags; for each, run `git log {tag} --format="%ai %D" -1` to get date
5. Print formatted list; exit 0
6. If no CHANGELOG.md and git produces no output: print `"No changelog available."`, exit 0

**Exit codes**:

| Code | Condition |
|------|-----------|
| 0 | Always (CHANGELOG absence is not an error) |

---

## 3. `dotnet-ai extension-add` — Changed error behaviour for catalog installs

**No flag changes.** Only the error output format changes when `--dev` is omitted:

### Before
```
Error: Catalog-based extension install for 'jira' is not yet supported. Use --dev with a local path instead.
```
(red text, exit 1)

### After
```
Note: Catalog-based installs are not yet supported. Use --dev to install from a local path: dotnet-ai extension-add --dev ./my-ext
```
(yellow text, exit 1)

---

## 4. `dotnet-ai extension-list` — Empty state message

**No flag changes.**

### Before
(no output, exit 0)

### After
```
No extensions installed. Use 'dotnet-ai extension-add --dev <path>' to install one.
```
(standard console output, exit 0)

---

## 5. `dotnet-ai configure --json` — `warnings` array for full permissions

When `permissions_level == "full"` and `--json` is active:

### Before
```json
{"status": "ok", "company": "Acme", ...}
```

### After
```json
{"status": "ok", "company": "Acme", ..., "warnings": ["bypassPermissions enabled — all operations run without confirmation"]}
```

The `"warnings"` key is only present when non-empty.

---

## 6. `dotnet-ai configure --dry-run` — Init guard bypass

**No flag changes.**

### Before
Running `configure --dry-run` without prior `init` exits with code 1 and message "dotnet-ai-kit is not initialized."

### After
Running `configure --dry-run` without prior `init` shows:
```
[yellow]Warning: Not initialized. Showing default config preview.[/yellow]
[DRY-RUN] dotnet-ai-kit configure preview
...
```
Exit code 0.

---

## 7. `dotnet-ai check --verbose` — Profile/Hook detail

**No flag changes.**

### Before (verbose = normal output)
```
┌────────────────────┐
│ AI Tools           │
│ Claude Code  configured  27  15  120  13  deployed  deployed │
```

### After (verbose shows additional lines after table)
```
  Profile: .claude/rules/architecture-profile.md
  Hook: model=claude-haiku-4-5-20251001, timeout=15s
```
(printed for each tool where profile or hook is "deployed")

---

## 8. `dotnet-ai upgrade --force` — Profile/hook always re-deployed

**No flag changes.**

### Before
`upgrade --force` re-copies commands/rules/skills/agents. Profile/hook only deployed when `project.yml` is present and version comparison occurs.

### After
`upgrade --force` also unconditionally calls `copy_profile()` and `copy_hook()` for each tool, even if version file says already current. Guards remain for missing project.yml (graceful fallback to "generic" type).
