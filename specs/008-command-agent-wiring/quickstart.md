# Quickstart: Wire All Commands to Appropriate Agents and Skills

**Feature**: 008-command-agent-wiring | **Date**: 2026-03-23

## Implementation Order

### Wave 1: Fix Agent Skill Paths (prerequisite for all other waves)

1. Read each of the 13 agent files
2. Cross-reference each skill in "Skills Loaded" against the actual `skills/` directory
3. Fix all shorthand references to full paths (`skills/{category}/{subcategory}/SKILL.md`)
4. Remove references to skills that don't exist

### Wave 2: Code Generation Commands (7 commands, highest impact)

For each command, add an agent loading section near the top:

1. `add-aggregate.md` — add `agents/command-architect.md`
2. `add-entity.md` — add `agents/query-architect.md` (SQL) or `agents/cosmos-architect.md` (Cosmos) + `agents/ef-specialist.md`
3. `add-event.md` — add `agents/command-architect.md`
4. `add-endpoint.md` — add `agents/gateway-architect.md` + `agents/api-designer.md`
5. `add-page.md` — add `agents/controlpanel-architect.md`
6. `add-tests.md` — add `agents/test-engineer.md`
7. `add-crud.md` — add primary architect (by project type) + `agents/ef-specialist.md` + `agents/api-designer.md`

### Wave 3: Expand implement.md (1 command, already partially done)

1. Add missing agents to the routing matrix: dotnet-architect, api-designer, ef-specialist, cosmos-architect, test-engineer, devops-engineer, docs-engineer, reviewer
2. Add task-type-based secondary agent loading logic
3. Keep under 200 lines

### Wave 4: Lifecycle Commands (8 commands)

1. `review.md` — add `agents/reviewer.md`
2. `docs.md` — add `agents/docs-engineer.md`
3. `verify.md` — add `agents/test-engineer.md` + `agents/devops-engineer.md`
4. `analyze.md` — add primary architect (by project type)
5. `plan.md` — add primary architect (by project type)
6. `tasks.md` — add primary architect (by project type)
7. `specify.md` — add primary architect (by project type)
8. `clarify.md` — add primary architect (by project type)

### Wave 5: Verification

1. For each modified command: verify under 200 lines (`wc -l`)
2. For each skill path in commands: verify file exists (`test -f`)
3. For each agent: verify all "Skills Loaded" entries have valid paths

## Agent Loading Pattern

Use this consistent pattern across all commands:

```markdown
## Load Specialist Agent

Read the specialist agent for architectural guidance based on detected project type:
- **Microservice mode**:
  - command → Read `agents/command-architect.md`
  - query-sql → Read `agents/query-architect.md`
  - query-cosmos → Read `agents/cosmos-architect.md`
  - processor → Read `agents/processor-architect.md`
  - gateway → Read `agents/gateway-architect.md`
  - controlpanel → Read `agents/controlpanel-architect.md`
  - hybrid → Read `agents/command-architect.md` and `agents/query-architect.md`
- **Generic mode** (VSA, Clean Arch, DDD, Modular Monolith):
  - Read `agents/dotnet-architect.md`
```

For commands that always load a specific agent regardless of project type:
```markdown
## Load Specialist Agent

Read `agents/{specialist}.md` for {domain} guidance.
```
