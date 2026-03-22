---
name: dotnet-ai-plan-artifacts
description: "Supporting artifact generation for complex features in /dotnet-ai.plan"
---

# Plan Artifacts Skill

Generate supporting artifacts when feature is classified as **Complex**.

## research.md

Document technical decisions with rationale:

```markdown
# Research: {Feature Name}

## R1: {Decision Topic}
**Decision**: {What was chosen}
**Rationale**: {Why}
**Alternatives considered**: {What else was evaluated}
```

## data-model.md

Extract entities from spec, define fields, relationships, validation:

```markdown
# Data Model: {Feature Name}

## Entities

### {Entity Name}
| Field | Type | Description |
|-------|------|-------------|
{fields}

## Relationships
{entity relationship descriptions}

## Validation Rules
{constraints and rules}
```

## contracts/ directory

Define interface contracts appropriate to the project type:
- **CLI tools**: Command schemas, flag definitions, output formats
- **Web services**: API endpoints, request/response models
- **Libraries**: Public API surface, type definitions
- **Microservices**: Proto definitions, event schemas, message contracts

## quickstart.md

Provide a practical implementation guide:

```markdown
# Quickstart: {Feature Name}

## Overview
{Brief description}

## Implementation Order
{Numbered steps with files to modify}

## Dev Setup
{Commands to install, test, lint}

## Dependency Changes
{New packages or tools needed}
```

## When to skip

If the feature is **Simple** (no HIGH complexity indicators), skip all artifacts.
The plan.md alone is sufficient for simple features.
