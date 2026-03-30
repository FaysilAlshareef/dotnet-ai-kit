---
description: "Creates a feature specification from a description. Use when starting a new feature or user story."
---

# /dotnet-ai.specify — Feature Specification

You are an AI coding assistant executing the `/dotnet-ai.specify` command.
Your job is to create a structured feature specification from user input.

## Input

Feature description: `$ARGUMENTS`
Flags: `--dry-run` (preview without writing), `--verbose` (diagnostic output)

## Load Specialist Agent

Based on the detected project type, read the specialist agent for architectural guidance:
- **Microservice mode**:
  - command → Read `agents/command-architect.md`
  - query-sql → Read `agents/query-architect.md`
  - query-cosmos → Read `agents/cosmos-architect.md`
  - processor → Read `agents/processor-architect.md`
  - gateway → Read `agents/gateway-architect.md`
  - controlpanel → Read `agents/controlpanel-architect.md`
  - hybrid → Read both `agents/command-architect.md` and `agents/query-architect.md`
- **Generic mode** (VSA, Clean Arch, DDD, Modular Monolith):
  - Read `agents/dotnet-architect.md`

Load all skills listed in the agent's Skills Loaded section.

## Step 1: Detect Project Mode

1. Read `.dotnet-ai-kit/config.yml` if it exists. Extract `project_mode` (generic | microservice).
2. If no config, scan the current directory:
   - Multiple repo references or `repos:` config → **microservice**
   - Single `.sln` / `.slnx` / `.csproj` → **generic**
3. If `--verbose`, print: "Detected mode: {mode}"

## Step 2: Check for Existing Features

1. Scan `.dotnet-ai-kit/features/` for existing feature directories.
2. If incomplete features found (no `tasks.md` or tasks with unchecked items):
   - Ask: "Resume feature NNN-{name} or create new?"
   - If resume: load existing spec and skip to Step 5 (quality check).
3. If `$ARGUMENTS` is empty and no features to resume, ask for a feature description.

## Step 3: Create Feature Directory

1. Determine next feature number: scan ONLY `.dotnet-ai-kit/features/` for highest NNN, increment.
   - Feature numbers are per-repo. Scan ONLY `.dotnet-ai-kit/features/`. NEVER scan `.dotnet-ai-kit/briefs/` — those are projected features from other repos with their own independent numbering. If no features exist in `features/`, start at 001.
2. Generate short-name from `$ARGUMENTS` (lowercase, hyphenated, max 4 words).
   - Example: "Add order management" → `order-management`
3. Create directory: `.dotnet-ai-kit/features/{NNN}-{short-name}/`
4. If `--dry-run`, print the path and continue without creating.

## Step 4: Generate spec.md

Read `skills/workflow/sdd-lifecycle/SKILL.md` for lifecycle patterns.

Generate `spec.md` inside the feature directory using this structure:

```markdown
# Feature Specification: {Feature Name}

**Feature ID**: {NNN}-{short-name}
**Created**: {DATE}
**Status**: Draft
**Input**: "$ARGUMENTS"

## User Stories

### User Story 1 - {Title} (Priority: P1)
{Description}
**Acceptance Scenarios**:
1. **Given** ..., **When** ..., **Then** ...

### User Story 2 - {Title} (Priority: P2)
...

### User Story 3 - {Title} (Priority: P3)
...

## Requirements

### Functional Requirements
- **FR-001**: System MUST ...
- ...

### Key Entities
- **{Entity}**: {description, key attributes}

## {MODE-SPECIFIC SECTION}

## Edge Cases
- ...

## [NEEDS CLARIFICATION] Items
- ...

## Success Criteria
- **SC-001**: ...
```

### Mode-Specific Sections

**Generic mode** — add "Architecture Scope":
- Affected layers: Domain, Application, Infrastructure, API
- Which layers need new files vs modifications
- Read `skills/architecture/vertical-slice/SKILL.md` or `skills/architecture/clean-architecture/SKILL.md` based on detected pattern

**Microservice mode** — add "Service Map":
- Which repos are affected (command, query, processor, gateway, controlpanel)
- What each repo needs (new aggregates, events, entities, endpoints, pages)
- Events to create/handle across services
- Read `skills/workflow/multi-repo-workflow/SKILL.md` for cross-repo patterns
- Auto-detect affected repos by analyzing the feature description against config repos
- Generate `service-map.md` in the feature directory with:
  - Mermaid diagram showing service dependencies
  - Per-service change summary (what each repo needs)
  - Affected repos list with specific artifacts to create/modify

### Constraints

- User stories MUST have priorities (P1, P2, P3)
- Each user story MUST be independently testable
- Maximum 3 `[NEEDS CLARIFICATION]` markers — only for genuinely ambiguous items
- Do NOT mark items as unclear if a reasonable default exists; state the default instead
- Include events, entities, and endpoints sections as applicable

## Step 5: Generate Quality Checklist

Create `checklists/requirements.md` in the feature directory:

```markdown
# Requirements Checklist: {Feature Name}

- [ ] All user stories have acceptance scenarios
- [ ] All functional requirements are testable
- [ ] Key entities identified with relationships
- [ ] {mode-specific checks}
- [ ] Edge cases documented
- [ ] Success criteria are measurable
- [ ] Max 3 [NEEDS CLARIFICATION] markers
```

**Microservice additions**:
- [ ] All affected repos identified
- [ ] Events defined with data schemas
- [ ] Service communication patterns specified
- [ ] Feature briefs projected to secondary repos

### Step 4b: Project Feature Briefs (microservice mode)

For each repo listed in `service-map.md` (except the current/primary repo):
1. Resolve repo path from `config.yml` repos section.
2. Determine source repo name: current repo's directory name (e.g., `company-domain-command`).
3. If local path exists for the target repo:
   - Create `{target-repo}/.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{short-name}/`
   - Write `feature-brief.md` with: Feature ID, Projected date, Phase "Specified", Source Repo name/path, This Repo's Role (from service-map), Required Changes (filtered), Events Produces/Consumes.
   - Auto-commit: `chore: project feature brief {NNN}-{name} from {source-repo-name}`. Skip auto-commit if secondary repo has uncommitted changes (warn instead).
4. If `github:org/repo` (not cloned locally): skip, note "Brief not projected — not cloned locally".
5. If repo path is null: skip, note "Brief not projected — repo not configured".

Report: "Projected feature briefs to {N} repos: {list}"

## Step 6: Report

Print summary:
```
Feature {NNN}-{short-name} specified.
- {N} user stories (P1: {x}, P2: {y}, P3: {z})
- {N} functional requirements
- {N} [NEEDS CLARIFICATION] markers
- Affected: {repos or layers list}

Next: /dotnet-ai.clarify    (resolve ambiguities)
      /dotnet-ai.plan       (skip to planning)
```

## Dry-Run Behavior

When `--dry-run` is active:
- Print all generated content to the terminal
- Show file paths that WOULD be created
- Do NOT create any directories or files
- Prefix output with `[DRY-RUN]`

## Error Handling

- If `$ARGUMENTS` is empty and no resumable features: ask for a description
- If config is missing: warn but proceed with auto-detection
- If feature directory already exists with same name: append incremented number
