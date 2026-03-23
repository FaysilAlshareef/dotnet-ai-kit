# Quickstart: Fix All 25 Identified Tool Issues

**Feature**: 007-fix-tool-issues | **Date**: 2026-03-23

## Implementation Order

Work in this order to minimize dependencies and enable incremental testing:

### Wave 1: Critical Bug Fixes (no dependencies)

These can all be done in parallel:

1. **Fix `config-template.yml`** — Change `permissions: { level: "standard" }` to `permissions_level: "standard"`. Update AI tools comment.
2. **Fix `pre-commit-lint.sh`** — Add parentheses around find OR conditions.
3. **Fix `copier.py` Jinja2** — Change `jinja2.Undefined` to `jinja2.StrictUndefined`.

### Wave 2: Python Code Changes (copier.py, cli.py, models.py, extensions.py)

4. **Add `copy_skills()` to copier.py** — Recursive directory copy following `copy_rules()` pattern.
5. **Add `copy_agents()` to copier.py** — Flat file copy following `copy_rules()` pattern.
6. **Update `cli.py` init()** — Call `copy_skills()` and `copy_agents()` after `copy_rules()`.
7. **Update `cli.py` upgrade()** — Same additions as init.
8. **Add hybrid to microservice types in cli.py**.
9. **Add repo path validation in models.py**.
10. **Add extension cleanup + file locking in extensions.py**.
11. **Standardize CLI exit codes in cli.py**.

### Wave 3: Command/Rule/Skill Markdown Changes

12. **Update `implement.md`** — Add always-loaded skills (configuration, DI) + agent loading per repo type.
13. **Update `tasks.md`** — Add command-side entity constraint + document `[P]` marker.
14. **Update `specify.md`** — Enforce per-repo feature numbering.
15. **Update `plan.md`** — Make constitution check optional.
16. **Update `analyze.md`** — Remove event-catalogue reference.
17. **Update `agents/query-architect.md`** — Add Cosmos routing guidance.
18. **Create `rules/configuration.md`** — Options pattern enforcement.
19. **Create `rules/testing.md`** — CQRS test patterns.
20. **Create `skills/core/error-handling/SKILL.md`**.
21. **Create `skills/microservice/command/event-versioning/SKILL.md`**.
22. **Fix SaveChangesAsync consistency** — Audit all skills, add `cancellationToken` where missing.
23. **Add `spec-link.md` generation** — Update `tasks.md` for cross-repo features.

### Wave 4: Tests

24. **Add tests for `copy_skills()` and `copy_agents()`**.
25. **Add tests for extension cleanup and locking**.
26. **Run full test suite** — `pytest --cov=dotnet_ai_kit`.

## Key Files to Read First

Before making changes, read these files to understand current patterns:

```
src/dotnet_ai_kit/copier.py       # Lines 56-165: copy_commands() and copy_rules() patterns
src/dotnet_ai_kit/cli.py          # Lines 198-420: init() flow; Lines 643-802: upgrade() flow
src/dotnet_ai_kit/models.py       # Lines 116-142: ReposConfig; Line 205: permissions_level
src/dotnet_ai_kit/extensions.py   # Lines 190-255: install function
templates/config-template.yml     # Line 54: permissions bug
hooks/pre-commit-lint.sh          # Line 34: find command bug
commands/implement.md             # Lines 27-41: skill loading section
commands/tasks.md                 # Lines 49-55: Phase 2 command side
```

## Verification Checklist

After all changes:

- [ ] `pytest` passes (all existing tests green)
- [ ] `ruff check src/ tests/` passes (no lint errors)
- [ ] `ruff format --check src/ tests/` passes (formatting correct)
- [ ] Config template loads with pydantic without errors
- [ ] New rules are under 100 lines each
- [ ] New skills are under 400 lines each
- [ ] `pip install -e ".[dev]"` succeeds with new filelock dependency
