# Contract: Architecture Profile File Format

## Frontmatter

```yaml
---
alwaysApply: true
description: "Architecture profile for {project_type} projects — hard constraints"
---
```

## Body Structure

All profiles follow this structure:

```markdown
# Architecture Profile: {Project Type}

## HARD CONSTRAINTS

- NEVER [violation description]. [Anti-pattern example: ...]
- ALWAYS [required pattern]. [Why: ...]
- MUST [requirement]. [Example: ...]
- MUST NOT [forbidden pattern]. [Why: ...]

## Testing Requirements

- ALWAYS [test pattern requirement]
- NEVER [test anti-pattern]

## Data Access

- MUST [data access rule]
- NEVER [data access anti-pattern]
```

## Budget

- Maximum 100 lines per profile (including frontmatter)
- Aim for 70-90 lines to leave room for future additions
- Only highest-severity constraints per project type

## Deployment Target

Deployed as: `{rules_dir}/architecture-profile.md`

Examples:
- Claude Code: `.claude/rules/architecture-profile.md`
- Cursor: `.cursor/rules/architecture-profile.md`
