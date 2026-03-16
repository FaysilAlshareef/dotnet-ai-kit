---
description: "Scan spec for ambiguities, ask targeted questions, update spec in place"
---

# /dotnet-ai.clarify — Resolve Specification Ambiguities

You are an AI coding assistant executing the `/dotnet-ai.clarify` command.
Your job is to find ambiguities in a feature spec and resolve them interactively.

## Input

Optional feature ID: `$ARGUMENTS` (e.g., `001` to target a specific feature)
Flags: `--dry-run` (show questions without updating), `--verbose` (diagnostic output)

## Step 1: Load Feature Spec

1. If `$ARGUMENTS` contains a feature ID, load `.dotnet-ai-kit/features/{ID}-*/spec.md`.
2. Otherwise, find the most recent feature directory in `.dotnet-ai-kit/features/`.
3. If no spec found, report error: "No feature spec found. Run /dotnet-ai.specify first."
4. If `--verbose`, print: "Loaded spec: {path}"

## Step 2: Detect Project Mode

1. Read `.dotnet-ai-kit/config.yml` if it exists. Extract `project_mode`.
2. If no config, infer from spec content:
   - "Service Map" section present → **microservice**
   - "Architecture Scope" section present → **generic**
3. Load relevant skills on demand:
   - Read `skills/workflow/sdd-lifecycle/SKILL.md` for lifecycle context

## Step 3: Scan for Ambiguities

Scan the spec against this taxonomy of ambiguity categories:

### Ambiguity Taxonomy

1. **Domain & Data Model**
   - Entity relationships undefined or contradictory
   - Missing attributes on key entities
   - Unclear ownership boundaries (which service owns what)

2. **Event Flow & Boundaries** (microservice priority)
   - Events referenced but not defined
   - Missing event data schemas
   - Unclear event ownership (who publishes, who subscribes)

3. **Service Communication** (microservice priority)
   - Undefined sync vs async boundaries
   - Missing error/retry semantics
   - Unclear service dependencies

4. **Query Patterns & Filtering**
   - Undefined search/filter criteria
   - Missing pagination requirements
   - Unclear sorting or ordering rules

5. **UI Requirements**
   - Vague page descriptions
   - Missing user interaction flows
   - Undefined validation rules for inputs

6. **Edge Cases**
   - Missing concurrent access handling
   - Undefined behavior for empty states
   - Missing authorization/permission rules

### What Counts as Ambiguous

- Explicit `[NEEDS CLARIFICATION]` markers in the spec
- Contradictions between user stories and requirements
- Requirements that cannot be implemented without assumptions
- Missing information that would block planning

### What Does NOT Count

- Items with reasonable defaults (document the default, do not ask)
- Implementation details (those belong in /plan, not /clarify)
- Style preferences (follow existing project conventions)

## Step 4: Prioritize Questions

1. Collect all ambiguities found (across all taxonomy categories).
2. Rank by impact: items that block planning rank highest.
3. Select the top 5 questions maximum.
4. If `--verbose`, print all found ambiguities before filtering to top 5.

Priority order:
1. CRITICAL: Blocks planning entirely (undefined core entity, missing event flow)
2. HIGH: Leads to wrong implementation (contradictory requirements)
3. MEDIUM: May cause rework (unclear edge cases)
4. LOW: Nice to know (UI details, formatting preferences)

## Step 5: Interactive Question Loop

Present ONE question at a time. For each question:

```
Clarification {N}/{total} [{category}] (priority: {level})

{Question text with context from the spec}

Options (if applicable):
  a) {Option A}
  b) {Option B}
  c) Other: {describe}
```

After each answer:
1. Update `spec.md` immediately — replace the ambiguous section with the resolved answer.
2. If the answer was a `[NEEDS CLARIFICATION]` marker, remove the marker.
3. Add the resolution to a `## Clarifications` section at the end of spec.md:
   ```
   ## Clarifications
   - **C-001** [{category}]: {question summary} → {resolution}
   ```
4. Print: "{N} markers resolved, {M} remaining"
5. Proceed to next question.

If `--dry-run`: show all questions but do NOT update spec.md. Print what would change.

## Step 6: Completion Report

After all questions are answered (or user exits early):

```
Clarification complete for {NNN}-{feature-name}.
- Resolved: {X} ambiguities
- Remaining: {Y} markers
- Categories covered: {list}

{If Y == 0}:
  Spec is ready for planning.
  Next: /dotnet-ai.plan

{If Y > 0}:
  {Y} ambiguities remain. You can:
  - Run /dotnet-ai.clarify again to continue
  - Run /dotnet-ai.plan (unresolved items will be noted in the plan)
```

## Dry-Run Behavior

When `--dry-run` is active:
- Show all detected ambiguities with categories and priorities
- Show the questions that WOULD be asked
- Do NOT modify spec.md
- Prefix output with `[DRY-RUN]`

## Error Handling

- If spec has no ambiguities and no markers: "Spec is clean. No clarifications needed."
- If user provides invalid feature ID: list available features
- If user exits mid-session: save progress (partial clarifications already written)
