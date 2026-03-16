# Handoff Schema Contracts: dotnet-ai-kit v1.0

## Overview

8 schema formats used by commands to pass data between SDD lifecycle
steps. All stored in `.dotnet-ai-kit/features/{NNN}-{short-name}/`.
Full schema definitions in `planning/13-handoff-schemas.md`.

## Schema Summary

| Schema | Created by | Read by | Microservice | Generic |
|--------|-----------|---------|-------------|---------|
| spec.md | /specify | /clarify, /plan, /analyze, /review, /pr | Yes | Yes (Architecture Scope instead of Service Map) |
| plan.md | /plan | /tasks, /implement, /analyze | Yes | Yes (layer-based phases) |
| service-map.md | /plan | /implement, /analyze | Yes | No |
| tasks.md | /tasks | /implement, /status | Yes ([Repo:*] prefix) | Yes (no repo prefix) |
| analysis.md | /analyze | /implement, /review | Yes (9 analysis passes) | Yes (5 passes) |
| review.md | /review | /pr | Yes | Yes |
| handoff.md | /checkpoint, /wrap-up | Next session | Yes | Yes |
| event-catalogue/ | /plan, /implement | /analyze | Yes | No |

## Validation Rules

1. All files in a feature directory MUST have the same feature_id
2. Status progression: draft → clarified → planned → in-progress → completed
3. Events in spec.md must appear in plan.md and event-catalogue/
4. Every entity/event/endpoint in spec must have at least one task
5. Repos in tasks.md must match service-map.md
6. All dates in ISO 8601 format (YYYY-MM-DD)
