# Contract: Universal Agent Frontmatter Schema

## Source Format (tool-agnostic)

```yaml
---
name: {agent-name}
description: "{agent description}"
role: advisory | implementation | testing | review
expertise:
  - skill-name-1
  - skill-name-2
complexity: high | medium | low
max_iterations: {integer}
---
```

## Claude Code Output Format

```yaml
---
name: {agent-name}
description: "{agent description}"
disallowedTools:          # from role mapping (omitted if empty)
  - Write
  - Edit
skills:                   # from expertise mapping
  - skill-name-1
  - skill-name-2
effort: high              # from complexity mapping
model: opus               # from complexity mapping
maxTurns: 20              # from max_iterations mapping
---
```

## Transformation Rules

| Universal Field | Claude Code Output | Mapping |
|----------------|-------------------|---------|
| name | name | Pass-through |
| description | description | Pass-through |
| role: advisory | disallowedTools: [Write, Edit] | Dict lookup |
| role: implementation | (no disallowedTools) | Dict lookup |
| role: testing | (no disallowedTools) | Dict lookup |
| role: review | disallowedTools: [Write, Edit] | Dict lookup |
| expertise: [...] | skills: [...] | Lambda: list pass-through |
| complexity: high | effort: high, model: opus | Dict lookup |
| complexity: medium | effort: medium, model: sonnet | Dict lookup |
| complexity: low | effort: low, model: haiku | Dict lookup |
| max_iterations: N | maxTurns: N | Lambda: int pass-through |
