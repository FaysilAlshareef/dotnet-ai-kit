# Quickstart: Fix v1.0 Gap Report Issues

**Feature**: 010-fix-v1-gaps | **Date**: 2026-03-25

## Implementation Order

Work in this order to minimize dependencies:

### Phase A: Quick fixes (no dependencies)
1. **FR-003**: Rename duplicate skill name in `skills/api/controller-patterns/SKILL.md`
2. **FR-009**: Replace `--preview` with `--dry-run` across 12 command files
3. **FR-011**: Verified already resolved — no action needed

### Phase B: Python changes (test after each)
4. **FR-004**: Remove `CodeRabbitConfig`, `IntegrationsConfig` from `models.py`, add `domain` field to `NamingConfig`
5. **FR-006**: Wire `NamingConfig` to `copier.py` template context (depends on FR-004)
6. **FR-005**: Add hook execution + version check to `extensions.py`

### Phase C: New content (independent)
7. **FR-001**: Create `commands/learn.md` (the `/dai.learn` command)
8. **FR-002**: Wire constitution check in `commands/plan.md` and `skills/workflow/plan-templates/SKILL.md`
9. **FR-010**: Add service-map.md as explicit output in `commands/specify.md`
10. **FR-007**: Create 4 knowledge documents (CQRS, DDD, Clean Arch, VSA)
11. **FR-008**: Expand `plugin.json` with full catalog

### Phase D: Documentation updates
12. Update `CLAUDE.md` (command count 26→27, add `/dai.learn` row)
13. Update `planning/12-version-roadmap.md` (reflect changes)
14. Update `.specify/memory/constitution.md` (knowledge base count 11→15, commands 26→27)

## Verification

After implementation, verify:
```bash
# SC-002: No duplicate skill names
grep -r "^name:" skills/ | sort | uniq -d  # Should return empty

# SC-003: No --preview in commands
grep -r "\-\-preview" commands/  # Should return empty

# FR-004: Models removed
grep -r "CodeRabbitConfig\|IntegrationsConfig" src/  # Should return empty

# FR-005: Tests pass
pytest tests/test_extensions.py -v

# FR-006: Tests pass
pytest tests/test_copier.py -v

# All tests pass
pytest --cov=dotnet_ai_kit
```

## Key Files to Read First

Before implementing, read these files to understand current patterns:
1. `commands/detect.md` — understand detection flow (learn chains this)
2. `src/dotnet_ai_kit/models.py:99-224` — current model structure
3. `src/dotnet_ai_kit/copier.py:364-373` — hardcoded template context
4. `src/dotnet_ai_kit/extensions.py:30-93` — extension manifest handling
5. `knowledge/event-sourcing-flow.md` — example knowledge doc format
