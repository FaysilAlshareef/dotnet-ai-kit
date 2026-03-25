# Data Model: Fix v1.0 Gap Report Issues

**Feature**: 010-fix-v1-gaps | **Date**: 2026-03-25

## Entity Changes

### Modified: NamingConfig (models.py)

**Current fields**: `solution`, `topic`, `namespace` (all string patterns)

**Add field**:
- `domain: str` — Default: `"Domain"`. The domain name used in template rendering (e.g., "Draw", "Order", "Invoice").

**Relationships**: Read by `copier.py:scaffold_project()` to populate Jinja2 template context. Values come from `.dotnet-ai-kit/config.yml` under `naming:` section.

**State**: Static configuration — set once via `/dai.configure`, read during template rendering.

### Removed: CodeRabbitConfig (models.py)

**Fields removed**: `enabled`, `auto_fix`, `severity_threshold`
**Reason**: Deferred to v1.1. Zero functional references in codebase.

### Removed: IntegrationsConfig (models.py)

**Fields removed**: `coderabbit` (CodeRabbitConfig)
**Reason**: Only contained CodeRabbitConfig. Deferred to v1.1.
**Impact on DotnetAiConfig**: Remove `integrations` field (line 212-215).

### Modified: DotnetAiConfig (models.py)

**Remove field**: `integrations: IntegrationsConfig` (line 212-215)
**Keep fields**: `version`, `company`, `naming`, `repos`, `permissions_level`, `managed_permissions`, `ai_tools`

### New: Constitution File (.dotnet-ai-kit/memory/constitution.md)

**Not a Python model** — generated Markdown file. Structure:
- Architecture section (mode, type, .NET version)
- Domain Model section (aggregates, entities, events)
- Conventions section (namespaces, naming, DI, error handling, logging)
- Key Packages list
- Established Patterns list

**Lifecycle**: Created by `/dai.learn`, updated by `/dai.learn --update`, read by AI sessions on load.

### Modified: ExtensionManifest (extensions.py)

**No field changes**. Behavioral changes:
- `min_cli_version` now validated against current CLI version during install
- `hooks` dict now validated for well-formed structure and executed post-install

## Config Schema Changes

### config.yml — naming section

**Before**:
```yaml
naming:
  solution: "{Company}.{Domain}.{Side}"
  topic: "{company}-{domain}-{side}"
  namespace: "{Company}.{Domain}.{Side}.{Layer}"
```

**After** (new `domain` field):
```yaml
naming:
  domain: "Draw"  # NEW — used in template rendering
  solution: "{Company}.{Domain}.{Side}"
  topic: "{company}-{domain}-{side}"
  namespace: "{Company}.{Domain}.{Side}.{Layer}"
```

### config.yml — integrations section

**Before**:
```yaml
integrations:
  coderabbit:
    enabled: false
    auto_fix: false
    severity_threshold: warning
```

**After**: Section removed entirely. Existing config files with this section will have it silently ignored by pydantic (using `model_config = ConfigDict(extra="ignore")`).

## File Artifacts

### New files created

| File | Type | Size (est.) | FR |
|------|------|-------------|-----|
| `commands/learn.md` | Command template | ~180 lines | FR-001 |
| `knowledge/cqrs-patterns.md` | Reference doc | ~200 lines | FR-007 |
| `knowledge/ddd-patterns.md` | Reference doc | ~200 lines | FR-007 |
| `knowledge/clean-architecture-patterns.md` | Reference doc | ~200 lines | FR-007 |
| `knowledge/vsa-patterns.md` | Reference doc | ~200 lines | FR-007 |

### Modified files

| File | Change Type | FR |
|------|------------|-----|
| `models.py` | Remove 2 classes, add 1 field | FR-004, FR-006 |
| `copier.py` | Wire NamingConfig to template context | FR-006 |
| `extensions.py` | Add hook execution + version check | FR-005 |
| `plugin.json` | Expand with catalog | FR-008 |
| `plan.md` | Wire constitution check | FR-002 |
| `specify.md` | Add service-map.md output | FR-010 |
| `plan-templates/SKILL.md` | Update Constitution Check | FR-002 |
| `controller-patterns/SKILL.md` | Rename to unique name | FR-003 |
| 12 command files | `--preview` → `--dry-run` | FR-009 |
| `CLAUDE.md` | Update counts | Documentation |
| `12-version-roadmap.md` | Update counts | Documentation |
