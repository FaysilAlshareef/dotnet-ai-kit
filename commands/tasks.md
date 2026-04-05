---
description: "Breaks the plan into ordered executable tasks. Use when ready to start coding after planning."
---

# /dotnet-ai.tasks — Task Generation

You are an AI coding assistant executing the `/dotnet-ai.tasks` command.
Your job is to generate a structured task list from an implementation plan.

## Usage

```
/dotnet-ai.tasks $ARGUMENTS
```

**Examples:**
- (no args) — Generate tasks.md from current plan
- `--dry-run` — Preview task structure without writing

## Input

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

## Step 1: Load Prerequisites

1. Find the active feature in `.dotnet-ai-kit/features/`.
2. Load these artifacts (all from the feature directory):
   - `plan.md` — required. If missing: "No plan found. Run /dotnet-ai.plan first."
   - `spec.md` — required for user stories and priorities.
   - `service-map.md` — required for microservice mode, ignored for generic.
   - `event-flow.md` — optional, used for event-related task ordering.
3. Detect mode from plan.md content or config.
4. If `--verbose`, print loaded artifacts and detected mode.

## Step 2: Load Skills on Demand

Based on detected mode, read relevant skills:
- Always: `skills/workflow/sdd-lifecycle/SKILL.md`
- Microservice: `skills/workflow/multi-repo-workflow/SKILL.md`
- If command-side tasks: `skills/microservice/command/aggregate-design/SKILL.md`
- If query-side tasks: `skills/microservice/query/query-entity/SKILL.md`
- If gateway tasks: `skills/microservice/gateway/gateway-endpoint/SKILL.md`
- If controlpanel tasks: `skills/microservice/controlpanel/blazor-component/SKILL.md`

## Step 3: Generate Tasks (Microservice Mode)

Create `tasks.md` in the feature directory. Organize tasks by phase:

```markdown
# Tasks: {Feature Name}

**Feature**: {NNN}-{short-name} | **Mode**: Microservice
**Generated**: {DATE} | **Total Tasks**: {N}

## Phase 1: Setup
- [ ] T001 [Repo:{repo}] Clone/open {repo}, create branch feature/{NNN}-{short-name}
- [ ] T002 [P] [Repo:{repo2}] Clone/open {repo2}, create branch feature/{NNN}-{short-name}

## Phase 2: Command Side

**CONSTRAINT**: Event-sourced — generate ONLY Aggregates, Events, Value Objects, Enums, Domain Exceptions. NEVER create entities/projections. Use gRPC client tasks for external state queries.

- [ ] T003 [Repo:command] Create {Aggregate} with {Event} event
      File: src/{Domain}/Aggregates/{Aggregate}.cs
- [ ] T004 [Repo:command] Add {Command} command handler
      File: src/{Domain}/Commands/{Command}Handler.cs
- [ ] T005 [Repo:command] Register services in DI
      File: src/{Domain}/Extensions/ServiceCollectionExtensions.cs

## Phase 3: Query Side
- [ ] T006 [P] [Repo:query] Create {Entity} entity with event constructors
      File: src/{Domain}/Entities/{Entity}.cs
- [ ] T007 [P] [Repo:query] Add {Event}Handler for projection
      File: src/{Domain}/EventHandlers/{Event}Handler.cs
- [ ] T008 [Repo:query] Add query handler for {Query}
      File: src/{Domain}/Queries/{Query}Handler.cs

## Phase 4: Processor (if applicable)
- [ ] T009 [Repo:processor] Add listener for {Event}
- [ ] T010 [Repo:processor] Add routing handler

## Phase 5: Gateway
- [ ] T011 [depends: T008] [Repo:gateway] Add {Endpoint} endpoint
      File: src/Endpoints/{Domain}/{Endpoint}.cs
- [ ] T012 [Repo:gateway] Register gRPC client for {service}

## Phase 6: Control Panel (if applicable)
- [ ] T013 [depends: T011] [Repo:controlpanel] Add {Page} page
      File: src/Pages/{Domain}/{Page}.razor
- [ ] T014 [Repo:controlpanel] Add gateway facade method

## Phase 7: Testing
- [ ] T015 [P] [Repo:command] Unit tests for {Aggregate}
- [ ] T016 [P] [Repo:query] Unit tests for {Entity} handlers
- [ ] T017 [P] [Repo:gateway] Integration tests for {Endpoint}

## Phase 8: DevOps (if applicable)
- [ ] T018 [P] [Repo:*] Update K8s manifests with new env vars
- [ ] T019 [P] [Repo:*] Update GitHub Actions if needed
```

## Step 4: Generate Tasks (Generic Mode)

For generic .NET projects, organize by architectural layer:

```markdown
# Tasks: {Feature Name}

**Feature**: {NNN}-{short-name} | **Mode**: Generic
**Generated**: {DATE} | **Total Tasks**: {N}

## Phase 1: Setup
- [ ] T001 Create feature branch feature/{NNN}-{short-name}

## Phase 2: Domain Layer
- [ ] T002 Create {Entity} entity
      File: src/{Domain}/Entities/{Entity}.cs
- [ ] T003 [P] Create {ValueObject} value object
      File: src/{Domain}/ValueObjects/{ValueObject}.cs
- [ ] T004 [P] Add domain events
      File: src/{Domain}/Events/{Event}.cs

## Phase 3: Application Layer
- [ ] T005 Create {Command} command + handler
      File: src/{Application}/Commands/{Command}Handler.cs
- [ ] T006 [P] Create {Query} query + handler
      File: src/{Application}/Queries/{Query}Handler.cs
- [ ] T007 Add validator for {Command}
      File: src/{Application}/Validators/{Command}Validator.cs

## Phase 4: Infrastructure Layer
- [ ] T008 Create {Repository} repository
      File: src/{Infrastructure}/Repositories/{Repository}.cs
- [ ] T009 Add EF configuration for {Entity}
      File: src/{Infrastructure}/Configurations/{Entity}Configuration.cs
- [ ] T010 Register services in DI

## Phase 5: API Layer
- [ ] T011 Add {Endpoint} endpoint
      File: src/{API}/Endpoints/{Endpoint}.cs
- [ ] T012 [P] Create request/response DTOs
      File: src/{API}/Models/{Dto}.cs

## Phase 6: Testing
- [ ] T013 [P] Unit tests for domain
- [ ] T014 [P] Unit tests for handlers
- [ ] T015 Integration tests for endpoints

## Phase 7: Polish
- [ ] T016 [P] Code cleanup, XML docs, and project documentation
```

## Task Format Rules

- Every task has a unique ID: `T001`, `T002`, etc.
- `[P]` = can run in parallel (different files, no dependency within the phase)
- `[depends: T{N}]` = blocked until T{N} completes; `[Repo:{name}]` = target repo (microservice)
- Tasks without markers depend on the previous task (sequential default)
- Include exact file paths; each task should be completable in one step

## Step 5: Report

```
Tasks generated for {NNN}-{short-name}.
- Total: {N} tasks across {M} phases
- Parallel opportunities: {count} tasks marked [P]
- {Microservice: across {R} repositories}

Next: /dotnet-ai.analyze (consistency check) or /dotnet-ai.implement (start coding)
```

## Cross-Repo Feature Tracking (microservice mode)

For each secondary repo in `service-map.md`, resolve path from `config.yml`. If local path exists: update `feature-brief.md` in `.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{name}/` (create if missing) with filtered `[Repo:this-repo]` tasks, dependencies, and phase "Tasks Generated". Auto-commit with `chore: update feature brief {NNN}-{name} — tasks-generated`. If repo not cloned: skip with note.

### Secondary Repo Branch Safety

Before committing: check branch with `git -C {repo_path} rev-parse --abbrev-ref HEAD`. If on main/master/develop, create or reuse `chore/brief-{NNN}-{name}`. If dirty (`status --porcelain`): warn and skip. NEVER commit to main/master/develop.

## Dry-Run / Error Handling

- `--dry-run`: print task list, do NOT create tasks.md, prefix `[DRY-RUN]`
- Missing plan.md: direct to `/dotnet-ai.plan`; missing spec.md: direct to `/dotnet-ai.specify`
- Microservice without service-map.md: warn, generate tasks from plan.md only
