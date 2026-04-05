# Data Model Changes: Tool-Wide Quality Hardening

**Branch**: `016-tool-quality-hardening` | **Date**: 2026-04-04

## Existing Entities (Modified)

### DetectedProject (models.py:253)

**Current field**:
```
detected_paths: Optional[dict[str, str]] = Field(default=None)
```

**Change**: Add field_validator that warns on unknown keys.

**New constant** (module-level):
```
KNOWN_PATH_KEYS: frozenset[str] = frozenset({
    "aggregates", "events", "commands", "handlers", "entities",
    "tests", "test_live", "persistence", "controllers",
    "cosmos_entities", "cosmos_repositories", "features",
    "pages", "components",
})
```

**New validator**: Logs warning for keys not in KNOWN_PATH_KEYS. Does not reject — forward-compatible.

---

### DotnetAiConfig (models.py)

**No model changes needed.** The `integrations` section is removed from `config-template.yml` instead of adding model support (per spec assumption — integrations not yet implemented).

---

## New Constants (copier.py)

### COMMAND_SHORT_ALIASES

```python
COMMAND_SHORT_ALIASES: dict[str, str] = {
    "specify": "spec",
    "analyze": "check",
    "implement": "go",
    "add-aggregate": "agg",
    "add-entity": "entity",
    "add-event": "event",
    "add-endpoint": "ep",
    "add-tests": "tests",
    "checkpoint": "save",
    "wrap-up": "done",
}
```

Used in `copy_commands()` when generating short-prefix files (`dai.*.md`). If a source stem is in the dict, the alias is used; otherwise the original stem is the filename.

---

## Configuration Changes

### pyproject.toml — force-include

Add two entries:
```toml
"profiles" = "dotnet_ai_kit/bundled/profiles"
"prompts" = "dotnet_ai_kit/bundled/prompts"
```

### templates/config-template.yml

**Remove** the `integrations:` section (lines 44-53):
```yaml
# External tool integrations
integrations:
  coderabbit:
    enabled: false
    auto_fix: false
    severity_threshold: "warning"
```

Replace with comment:
```yaml
# External tool integrations are not yet supported.
# See documentation for future integration options.
```

---

## CLI Output Changes

### check command — new fields

**Rich table**: Add columns to AI Tools table:
- **Skills** (count of files in skills_dir)
- **Agents** (count of files in agents_dir)
- **Profile** (deployed / not deployed)
- **Hook** (deployed / not deployed)

**Config panel**: Add rows:
- **Linked from**: `{path}` or "N/A"
- **Detected paths**: `{count} categories` or "not detected"
- **Linked repos**: Per-repo status (path, exists, version)

**JSON output**: Add to `tools` dict per tool:
- `skills: int`
- `agents: int`
- `profile: bool`
- `hook: bool`

Add top-level:
- `linked_from: str | null`
- `detected_paths: dict | null`
- `linked_repos: list[{role, path, status}]`

---

## Skill Frontmatter Changes

### when-to-use additions (target: 80+ of 120)

New frontmatter field in YAML block:
```yaml
when-to-use: "When creating or modifying [specific context]"
```

Categories and counts:
| Category | Total | Has when-to-use | alwaysApply | Target additions |
|----------|-------|-----------------|-------------|-----------------|
| microservice/ | 33 | 7 | 0 | +26 |
| architecture/ | 7 | 0 | 0 | +7 |
| testing/ | 4 | 2 | 0 | +2 |
| data/ | 8 | 1 | 0 | +7 |
| api/ | 11 | 0 | 0 | +11 |
| cqrs/ | 6 | 0 | 0 | +6 |
| core/ | 12 | 0 | 9 | +3 (non-alwaysApply) |
| others | 39 | 1 | 0 | +7-10 (high-value) |
| **Total** | **120** | **11** | **9** | **+69-72** → **80-83** |

### paths token additions (target: 9+ of 120)

New/updated frontmatter:
```yaml
paths: "${detected_paths.KEY}/**/*.cs"
```

Specific additions:
| Skill | paths token |
|-------|------------|
| microservice/query/query-entity | `${detected_paths.entities}/**/*.cs` |
| microservice/query/event-handler | `${detected_paths.handlers}/**/*.cs` |
| microservice/cosmos/cosmos-entity | `${detected_paths.cosmos_entities}/**/*.cs` |
| microservice/gateway/gateway-endpoint | `${detected_paths.controllers}/**/*.cs` |
| testing/unit-testing | `${detected_paths.tests}/**/*.cs` |
| testing/integration-testing | `${detected_paths.test_live}/**/*.cs` |

Brings total from 3 to 9.
