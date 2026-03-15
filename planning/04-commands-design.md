# dotnet-ai-kit - Slash Commands Design

## Which Command Do I Use?

```
I want to...
├── Build a feature fast           → /dotnet-ai.do "description"
├── Build a feature step-by-step   → /dotnet-ai.specify → plan → implement
├── Add CRUD for an entity         → /dotnet-ai.add-crud Order
├── Add one component              → /dotnet-ai.add-endpoint, add-event, add-page
├── Check my progress              → /dotnet-ai.status
├── Undo a mistake                 → /dotnet-ai.undo
├── Learn a pattern                → /dotnet-ai.explain "topic"
├── Resume from yesterday          → /dotnet-ai.status → follow "Next:" suggestion
└── Preview before doing anything  → Add --dry-run to any command
```

## Core 5 Commands (90% of daily work)

| Command | What it does |
|---------|-------------|
| `/dotnet-ai.do "description"` | Build a feature — one command, full lifecycle |
| `/dotnet-ai.add-crud Entity` | Generate complete CRUD (entity, handlers, endpoint, tests) |
| `/dotnet-ai.status` | See feature progress and what to do next |
| `/dotnet-ai.undo` | Revert the last step safely |
| `/dotnet-ai.explain topic` | Learn any pattern with examples |

## All 25 Commands by Category

### A. SDD Lifecycle Commands (step-by-step feature building)
### B. Project Management Commands
### C. Code Generation Commands (quick add)
### D. Session Management Commands
### E. Documentation Commands
### F. Smart Commands (shortcuts and utilities)
### G. Command Alias System

---

## A. SDD LIFECYCLE COMMANDS

### `/dotnet-ai.specify` - Define Feature Specification

**Inspired by**: spec-kit `/speckit.specify`

**Description**: Create a feature specification for any .NET feature (generic or microservice)

**Usage**:
```bash
/dotnet-ai.specify "Add order management"           # New feature from description
/dotnet-ai.specify                                   # Resume existing or create new
/dotnet-ai.specify --dry-run "Add payments"          # Preview spec without writing
```

**Flow**:
1. Ask for feature description (natural language)
2. Generate feature directory: `.dotnet-ai-kit/features/{NNN}-{short-name}/`
3. Create `spec.md` from template with:
   - User stories with priorities (P1, P2, P3)
   - Affected services (which repos are involved)
   - Events to create/handle
   - Entities to create/modify
   - Endpoints to expose
   - Pages to build
   - [NEEDS CLARIFICATION] markers (max 3)
4. Generate quality checklist
5. Auto-detect which repos are affected

**Output**: `spec.md`, `checklists/requirements.md`

**Handoffs**: → clarify → plan

**Key Difference from spec-kit**: Spec includes a "Services Map" section showing which microservices are affected and what each needs.

**Feature Resume**:
- On start, checks `.dotnet-ai-kit/features/` for existing features
- If incomplete features found: "Resume feature NNN-name or create new?"
- Resuming loads existing spec, plan, and task status

---

### `/dotnet-ai.clarify` - Resolve Ambiguities

**Inspired by**: spec-kit `/speckit.clarify`

**Description**: Scan spec for ambiguities, ask targeted questions, update spec

**Usage**:
```bash
/dotnet-ai.clarify                                   # Clarify current feature spec
/dotnet-ai.clarify 001                               # Clarify specific feature by ID
```

**Flow**:
1. Load spec.md
2. Scan against taxonomy:
   - Domain & data model
   - Event flow & boundaries
   - Service communication
   - Query patterns & filtering
   - UI requirements
   - Edge cases
3. Generate max 5 prioritized questions
4. Present ONE at a time
5. After each answer: update spec immediately
6. Track in `## Clarifications` section

**Validation**: No [NEEDS CLARIFICATION] markers remain, no contradictions

**Handoff to Plan**:
- Reports "X markers resolved, Y remaining" after each session
- If 0 remaining: spec is ready for `/dotnet-ai.plan`
- If markers remain: warns user but does not block — plan will note unresolved items

---

### `/dotnet-ai.plan` - Plan Implementation Across Services

**Inspired by**: spec-kit `/speckit.plan` + dotnet-claude-kit `/plan`

**Description**: Create implementation plan for a feature (single-repo or multi-repo)

**Usage**:
```bash
/dotnet-ai.plan                                      # Plan current feature
/dotnet-ai.plan --dry-run                            # Preview plan without writing
```

**Flow (Generic .NET — single repo)**:
1. Load spec.md and config
2. **Research** - Scan existing code for patterns, entities, handlers
3. **Layer Plan** - Map changes to layers:
   - Domain: entities, value objects, events
   - Application: commands, queries, handlers, validators
   - Infrastructure: repositories, services, configurations
   - API: endpoints, DTOs, mapping
4. **Output**: `plan.md`

**Flow (Microservices — multi-repo)**:
1. Load spec.md and config
2. **Phase 0: Research** - Check existing repos for similar patterns
3. **Phase 1: Service Map** - For each affected service: repo, changes, dependencies
4. **Phase 2: Event Design** - New events with data schemas, event flow
5. **Phase 3: Contracts** - Proto definitions, API contracts
6. **Output**: `plan.md`, `service-map.md`, `event-flow.md`, `contracts/`

---

### `/dotnet-ai.tasks` - Generate Tasks Per Repository

**Inspired by**: spec-kit `/speckit.tasks`

**Description**: Break plan into executable tasks, organized by repo and dependency order

**Usage**:
```bash
/dotnet-ai.tasks                                     # Generate tasks for current feature
/dotnet-ai.tasks --dry-run                           # Preview task list without writing
```

**Flow**:
1. Load plan.md, spec.md, service-map.md
2. Generate tasks organized by:
   - **Phase 1: Setup** - Clone repos, create branches
   - **Phase 2: Command Side** - Aggregates, events, outbox (must be first)
   - **Phase 3: Query Side** - Entities, event handlers, queries
   - **Phase 4: Processor** - Listeners, routing, handlers
   - **Phase 5: Gateway** - Endpoints, models, gRPC registration
   - **Phase 6: Control Panel** - Pages, filters, gateway facade
   - **Phase 7: Testing** - Tests for each service
   - **Phase 8: DevOps** - K8s manifests, GitHub Actions
3. Mark parallel tasks with [P]
4. Include exact file paths

**Task Format**:
```
- [ ] T001 [Repo:command] Create OrderAggregate with OrderCreated event
- [ ] T002 [Repo:command] Add OrderUpdated event to OrderAggregate
- [ ] T003 [P] [Repo:query] Create Order entity with event constructors
- [ ] T004 [P] [Repo:query] Add OrderCreatedHandler
```

**Dependency Notation**:
- `[P]` = can run in parallel with previous task
- `[depends: T003]` = blocked until T003 completes
- Tasks without notation depend on the previous task (sequential by default)

---

### `/dotnet-ai.analyze` - Consistency Check

**Inspired by**: spec-kit `/speckit.analyze`

**Description**: Read-only analysis of feature artifacts — catches issues before you implement

**Usage**:
```bash
/dotnet-ai.analyze                                   # Analyze current feature
/dotnet-ai.analyze --severity high                   # Show only HIGH+ findings
```

**Flow** (NEVER modifies files):
1. Load all artifacts (spec, plan, tasks)
2. Run analysis passes (auto-selected by mode):

**Generic .NET passes**:
   - **Architecture Consistency**: Layer boundaries respected (no Domain → Infrastructure)
   - **Naming Consistency**: Same entity name used everywhere
   - **Coverage Gaps**: Requirements with no tasks, tasks with no requirement
   - **Concurrency**: Row version and concurrency tokens configured for entities

**Microservice passes** (in addition to above):
   - **Event Consistency**: Events in command match handlers in query/processor
   - **Proto Consistency**: Request/Response match across gateway and services
   - **Cross-Repo Dependencies**: Correct service URLs, topic names
   - **Event Catalogue**: Each service has up-to-date event catalogue
   - **Event Version Compatibility**: Versioned event handlers match across services
   - **Sequence Gaps**: Event flow has missing links
   - **Idempotency**: Client-sent IDs for idempotency where applicable

3. Output report with severity (CRITICAL/HIGH/MEDIUM/LOW)

**Max 50 findings**. CRITICAL must be resolved before implement.

**When Critical Issues Found**:
- Report findings with file locations and suggested fixes
- User can fix manually or re-run `/dotnet-ai.plan` to revise the approach
- `/dotnet-ai.implement` warns but does NOT block — user decides whether to proceed
- Critical findings are logged in `features/NNN/analysis.md` for review

---

### `/dotnet-ai.implement` - Execute Implementation Tasks

**Inspired by**: spec-kit `/speckit.implement` + multi-repo orchestration

**Description**: Execute implementation tasks — works for single-repo and multi-repo features

**Usage**:
```bash
/dotnet-ai.implement                                 # Implement current feature
/dotnet-ai.implement --resume                        # Resume from last failed/incomplete task
/dotnet-ai.implement --dry-run                       # Preview files without writing
```

**Flow (Generic .NET — single repo)**:
1. Check prerequisites (plan exists, optional analyze complete)
2. Create feature branch: `feature/{NNN}-{short-name}`
3. Execute tasks by layer (Domain → Application → Infrastructure → API)
4. Run `dotnet build` after each layer
5. Run `dotnet test` after all tasks
6. Mark tasks complete in tasks.md

**Flow (Microservices — multi-repo)**:
1. Check prerequisites (checklists complete, no CRITICAL analyze findings)
2. **For each repo in dependency order**:
   a. Clone via `gh repo clone` (or open if local)
   b. Create feature branch: `feature/{NNN}-{short-name}`
   c. Execute tasks for this repo (phase by phase)
   d. Run `dotnet build` after each task group
   e. Run `dotnet test` after all tasks
   f. Mark tasks complete in tasks.md
3. Track progress across repos
4. If task fails: stop, report, suggest fix

**Multi-Repo Coordination** (microservice mode only):
- Command side MUST be implemented first (events define everything)
- Query/Processor can be parallel after command
- Gateway after query (needs proto from query)
- ControlPanel after gateway (needs API endpoints)

**Resume Support**:
- Progress tracked in `features/NNN/tasks.md` with status per task
- `--resume` flag continues from last incomplete/failed task
- Already-completed tasks are skipped (verified by checking file existence + git status)
- Failed task error is shown, user can fix and resume again

**Prerequisites**:
- If no `config.yml` exists: prompts user to run `/dotnet-ai.configure` first
- If no feature spec exists: prompts user to run `/dotnet-ai.specify` first
- Commands can be run independently, but the full lifecycle is recommended

**Existing vs New**:
- If repo exists: clone, detect version, detect patterns, extend
- If repo doesn't exist: ask for repo URL, scaffold from template, then implement

**Preview Mode**:
- `--dry-run`: Show all files that would be created/modified, without writing anything
- Reports per repo: "Would create 12 files, modify 3 files"
- Shows task list with estimated file paths
- No git operations, no file writes

---

### `/dotnet-ai.review` - Review Against Standards

**New command** (not in references)

**Description**: Review changes against company coding standards with optional CodeRabbit CLI integration

**Usage**:
```bash
/dotnet-ai.review                                    # Review current feature changes
/dotnet-ai.review --auto-fix                         # Apply safe auto-fixes
/dotnet-ai.review --skip-coderabbit                  # Skip CodeRabbit integration
```

**Flow**:
1. **Detect changes** - `git diff` in each affected repo
2. **Standards Review** (always):
   - Naming conventions compliance
   - Architecture boundary violations
   - Localization (no plain strings)
   - Error handling patterns
   - Event structure consistency
   - Test coverage
   - Security (no hardcoded secrets)
   - Performance (CancellationToken, pagination)
3. **CodeRabbit Integration** (optional):
   - Check if `coderabbit` CLI is installed
   - If yes: run `coderabbit review` on each repo
   - Merge CodeRabbit findings with standards review
   - If no: skip, inform user how to install
4. **Output structured report**:
   ```
   ## Review: feature/001-orders

   ### Command Repo (PASS)
   - Standards: 0 violations
   - CodeRabbit: 2 suggestions (non-blocking)

   ### Query Repo (NEEDS FIXES)
   - Standards: 1 violation (missing Phrases resource)
   - CodeRabbit: 1 warning (N+1 query)

   ### Fix suggestions for each finding
   ```
5. **Auto-fix option**: Ask user if they want auto-fix for non-breaking issues

**Auto-Fix Safety Rules**:
- **Safe** (auto-fixable): formatting, unused usings, missing `sealed`, file-scoped namespaces, missing XML doc tags
- **Unsafe** (requires user approval): logic changes, error handling modifications, architecture changes, dependency additions
- Auto-fix is always opt-in — user is asked before applying

---

### `/dotnet-ai.verify` - Verification Pipeline

**Inspired by**: dotnet-claude-kit `/verify`

**Description**: Run build + test + format verification per repo

**Usage**:
```bash
/dotnet-ai.verify                                    # Run full verification pipeline
/dotnet-ai.verify --skip-tests                       # Skip test suite (build + format only)
```

**Flow** (per affected repo):
1. `dotnet build` - Compilation check
2. `dotnet test` - Test suite
3. Resource check - Missing translations in Phrases.resx/en.resx
4. Proto check - Request/response consistency
5. K8s check - All required env vars in manifests
6. Format check - `dotnet format --verify-no-changes`

- Proto consistency check: client proto files match server proto files across repos (microservice mode only)

**Output**: Summary table per repo with PASS/FAIL/WARN

**Mode Adaptation**:
- Resource check: only runs if project uses `Phrases.resx` pattern (detected, not assumed)
- Proto check: only runs for microservice projects with `.proto` files
- K8s check: only runs if K8s manifests exist
- Format check: uses project's `.editorconfig` if present

---

### `/dotnet-ai.pr` - Create Pull Requests

**New command**

**Description**: Create PRs in all affected repos with linked descriptions

**Usage**:
```bash
/dotnet-ai.pr                                        # Create PRs in all affected repos
/dotnet-ai.pr --update                               # Update existing PRs (revision loop)
/dotnet-ai.pr --draft                                # Create as draft PRs
```

**Flow**:
1. For each affected repo:
   a. Push feature branch
   b. Create PR via `gh pr create`
   c. PR description includes:
      - Feature spec summary
      - Changes in this repo
      - Related PRs in other repos (cross-links)
      - Test results
      - Review findings
2. Output all PR URLs
3. Optionally notify (if configured)

**Note**: Related PRs are listed as text links in the PR body. GitHub does not automatically link PRs across repositories. Use labels or project boards for cross-repo tracking.

---

## B. PROJECT MANAGEMENT COMMANDS

### `/dotnet-ai.init` - Initialize or Detect Project

**Inspired by**: dotnet-claude-kit init command

**Description**: Works with BOTH existing and new projects

**Usage**:
```bash
/dotnet-ai.init                                      # Detect existing project in current dir
/dotnet-ai.init . --ai claude                        # Initialize for Claude Code
/dotnet-ai.init . --ai claude --ai cursor            # Initialize for multiple AI tools
/dotnet-ai.init my-project --type command             # Create new command project
```

**Flow for Existing Project**:
1. Scan directory for .sln, .csproj files
2. Detect project type (Command/Query/Cosmos/Processor/Gateway/ControlPanel)
3. Detect .NET version from TargetFramework
4. Detect patterns:
   - Aggregate base class? → Command side
   - Event handlers with sequence? → Query side
   - IContainerDocument? → Cosmos
   - IHostedService listeners? → Processor
   - REST controllers + gRPC clients? → Gateway
   - Blazor components? → Control Panel
5. Learn naming conventions from existing code
6. Generate `.dotnet-ai-kit/project.yml` with detected config
7. **Visualize detected patterns** — generate architecture overview:
   - Mermaid diagram of project layers or service dependencies
   - Entity list with relationships
   - Event flow diagram (microservice mode)
   - Report summary with diagram saved to `.dotnet-ai-kit/project-map.md`
8. Report: "Detected {type} project, .NET {version}, ready to use"

**Flow for New Project**:
1. Ask project type
2. Ask company name (from config or ask)
3. Ask domain name
4. Ask .NET version (suggest latest, allow any 8+)
5. Scaffold from template
6. Initialize git repo
7. Report: "Created {name}, run /dotnet-ai.specify to start a feature"

---

### `/dotnet-ai.configure` - Configure Tool Settings

**Description**: Set company name, repos, permissions, integrations

**Usage**:
```bash
/dotnet-ai.configure                                 # Interactive setup (only asks relevant questions)
/dotnet-ai.configure --minimal                       # Quick setup: company name only
/dotnet-ai.configure --reset                         # Reset to defaults and reconfigure
```

**Flow (just-in-time — tool asks what it needs, when it needs it)**:

Most settings are configured automatically the first time a feature needs them:

| When | What's asked | Why |
|------|-------------|-----|
| `dotnet-ai init` | Company name (auto-detected, confirm) | Required for code generation |
| First multi-repo feature | GitHub org, repo URLs | Needed to clone repos |
| First `/dotnet-ai.review` with CodeRabbit | "Enable CodeRabbit?" | Optional integration |
| First `/dotnet-ai.pr` | Default branch | Needed for PR base |

Running `/dotnet-ai.configure` explicitly sets everything at once (for power users):
1. Company name, GitHub org, default branch
2. Repo paths (microservice mode)
3. Permission level, command style
4. CodeRabbit integration
5. Save to `.dotnet-ai-kit/config.yml`

**You never need to run `/dotnet-ai.configure` to start using the tool.** It will ask what it needs, when it needs it.

---

## C. CODE GENERATION COMMANDS

### `/dotnet-ai.add-aggregate` - Add Aggregate (Command Side)

**Description**: Create a new aggregate with initial event in a command project.

**Usage**:
```bash
/dotnet-ai.add-aggregate Order                       # Create Order aggregate + OrderCreated event
/dotnet-ai.add-aggregate Order --events "Created,Updated,Completed"  # With multiple events
/dotnet-ai.add-aggregate Order --preview             # Show generated code without writing
```

Detects .NET version and existing patterns. See `17-code-generation-flows.md` for full flow.

---

### `/dotnet-ai.add-entity` - Add Entity (Query Side)

**Description**: Create a new entity with event handlers in a query project.

**Usage**:
```bash
/dotnet-ai.add-entity Order                          # Create Order entity + handlers
/dotnet-ai.add-entity Order --cosmos                 # Force Cosmos mode (auto-detected by default)
/dotnet-ai.add-entity Order --preview                # Show generated code without writing
```

Detects SQL vs Cosmos automatically. See `17-code-generation-flows.md` for full flow.

---

### `/dotnet-ai.add-event` - Add Event to Existing Aggregate

**Description**: Add a new event to an existing aggregate with handlers.

**Usage**:
```bash
/dotnet-ai.add-event OrderShipped Order              # Add OrderShipped to Order aggregate
/dotnet-ai.add-event OrderShipped Order --fields "TrackingNumber:string,ShippedAt:DateTime"
/dotnet-ai.add-event OrderShipped Order --preview    # Show generated code without writing
```

Updates command side. Suggests handler additions in query/processor repos. See `17-code-generation-flows.md`.

---

### `/dotnet-ai.add-endpoint` - Add Gateway Endpoint

**Description**: Add a REST endpoint to a gateway project.

**Usage**:
```bash
/dotnet-ai.add-endpoint GetOrders                    # Add GET endpoint (name-based detection)
/dotnet-ai.add-endpoint "POST /api/v1/orders"        # Add with explicit method + path
/dotnet-ai.add-endpoint GetOrders --preview          # Show generated code without writing
```

Detects gateway type (management vs consumer). Respects existing controller patterns. See `17-code-generation-flows.md`.

---

### `/dotnet-ai.add-page` - Add Control Panel Page

**Description**: Add a Blazor page to the control panel.

**Usage**:
```bash
/dotnet-ai.add-page Orders                           # Create Orders page with table + filters
/dotnet-ai.add-page Orders --module Sales            # Specify module
/dotnet-ai.add-page Orders --preview                 # Show generated code without writing
```

Uses existing page patterns as reference. Respects existing MudBlazor version. See `17-code-generation-flows.md`.

### `/dotnet-ai.add-crud` - Full CRUD for Entity (Generic + Microservice)
Generates complete Create/Read/Update/Delete for an entity in one command.

**Generic mode**: Entity + repository + handler + endpoint + tests (within single project layers)
**Microservice mode**: Aggregate + events + entity + handlers + endpoint + page (suggests cross-repo tasks)

```bash
/dotnet-ai.add-crud Order                     # Full CRUD with defaults
/dotnet-ai.add-crud Order --fields "Name,Total,CustomerId"  # With fields
/dotnet-ai.add-crud Order --no-tests          # Skip test generation
/dotnet-ai.add-crud Order --preview           # Show what will be generated
```

Detects project type and generates the appropriate pattern:
- **VSA**: Feature folder with Create/Get/Update/Delete handlers
- **Clean Arch**: Domain entity + Application handlers + Infra repo + API endpoints
- **DDD**: Aggregate + domain events + application services + API
- **Microservice**: Command aggregate + Query entity + Gateway endpoints (current repo only, suggests others)

See `17-code-generation-flows.md` for detailed flow.

(Each command detects existing patterns and works with existing projects first)

**Note**: Detailed flows for code generation commands are specified in `17-code-generation-flows.md`. Each command detects existing project patterns, generates code following conventions, and runs build verification. These are built during Phase 11 of the build roadmap.

**Common Flags** (all code gen commands):
- `--preview`: Show generated code in terminal without writing to disk
- `--dry-run`: Show file list that would be created/modified
- `--no-tests`: Skip test file generation

---

### `/dotnet-ai.add-tests` - Generate Tests for Existing Untested Code

**Description**: Scan existing code and generate missing unit/integration tests. Works on any project.

**Usage**:
```bash
/dotnet-ai.add-tests                                 # Scan entire project, generate all missing tests
/dotnet-ai.add-tests OrderService                    # Generate tests for specific class
/dotnet-ai.add-tests --handlers                      # Generate tests for all MediatR handlers
/dotnet-ai.add-tests --coverage 80                   # Generate until ~80% coverage target
/dotnet-ai.add-tests --preview                       # Show what tests would be generated
```

**Flow**:
1. Scan project for classes/handlers/controllers without corresponding test files
2. Detect existing test patterns (xUnit/NUnit, Moq/NSubstitute, test naming, folder structure)
3. Generate test files following detected patterns:
   - Unit tests for handlers, services, validators
   - Integration tests for repositories, controllers
   - Uses existing fakers/builders if found (CustomConstructorFaker, Bogus)
4. Run `dotnet test` to verify generated tests pass
5. Report: "Generated {N} test files, {M} test methods. Coverage: {X}%"

**Smart Behavior**:
- Detects which test framework is used (xUnit, NUnit, MSTest)
- Detects mocking library (Moq, NSubstitute, FakeItEasy)
- Follows existing test naming conventions
- Generates arrange/act/assert structure matching project style
- Skips control panel projects (no tests required)

**Note**: This command generates tests for EXISTING code. For tests generated alongside new code, use the SDD lifecycle (`/dotnet-ai.implement` includes test tasks).

---

## D. SESSION MANAGEMENT COMMANDS

### `/dotnet-ai.checkpoint` - Save Progress (Mid-Session)

**Inspired by**: dotnet-claude-kit `/checkpoint`

**Description**: Quick save — commit progress and write minimal handoff. Use when pausing work but planning to continue soon.

**Usage**:
```bash
/dotnet-ai.checkpoint                                # Save progress in all repos
/dotnet-ai.checkpoint "Completed query side"         # Save with custom message
```

**Flow**:
1. For each repo with changes:
   - Stage relevant files
   - Create descriptive commit
2. Write `.dotnet-ai-kit/handoff.md` (session_type: checkpoint) with:
   - Completed tasks per repo
   - Pending tasks per repo
   - Blocked items
   - Current feature context

**When to use**: Mid-session saves, switching context, before risky operations.

---

### `/dotnet-ai.wrap-up` - End Session (Final)

**Inspired by**: dotnet-claude-kit `/wrap-up`

**Description**: Full session close — commit, write comprehensive handoff, extract learnings. Use when done for the day.

**Usage**:
```bash
/dotnet-ai.wrap-up                                   # End session, write handoff
/dotnet-ai.wrap-up --no-commit                       # Write handoff without committing
```

**Flow**:
1. Commit all pending changes (per repo)
2. Write comprehensive handoff (session_type: wrap-up) including decisions and deviations
3. Extract learnings to memory
4. Report session summary

---

## E. DOCUMENTATION COMMANDS

### `/dotnet-ai.docs` - Generate Project Documentation

**New command**

**Description**: Generate or update technical and business documentation for the project

**Usage**:
```
/dotnet-ai.docs                        # Auto-detect missing docs, report gaps
/dotnet-ai.docs readme                  # Generate/update README.md
/dotnet-ai.docs api                     # Generate API documentation from OpenAPI/controllers
/dotnet-ai.docs adr "Decision Title"    # Create new Architecture Decision Record
/dotnet-ai.docs deploy                  # Generate deployment guide per environment
/dotnet-ai.docs release                 # Generate release notes from git history
/dotnet-ai.docs service                 # Generate service documentation (microservice mode)
/dotnet-ai.docs code                    # Scan and add missing XML doc comments
/dotnet-ai.docs feature                 # Generate user-facing feature documentation
/dotnet-ai.docs all                     # Generate all documentation types
```

**Flow**:
1. Detect project mode (microservice vs generic) from config
2. If no subcommand: scan for missing documentation and report gaps
3. If subcommand provided: generate that specific documentation type
4. **For each documentation type**:
   a. Scan existing documentation (detect style, format, completeness)
   b. Analyze project code (endpoints, events, entities, services)
   c. Generate documentation following detected or default templates
   d. Place files in standard locations
5. Report what was generated/updated

**Multi-Repo Support** (microservice mode):
- Per-repo documentation (each service gets its own docs)
- Umbrella documentation (cross-service README, architecture overview)
- Service catalogue aggregation

**Output Locations**:
```
project-root/
├── README.md                           # Project/service README
├── CHANGELOG.md                        # Release changelog
├── docs/
│   ├── adr/                           # Architecture Decision Records
│   │   ├── README.md                  # ADR index
│   │   └── 0001-*.md                  # Individual ADRs
│   ├── api/                           # API reference (generated)
│   │   └── api-reference.md
│   ├── deployment/                    # Deployment guides
│   │   ├── dev.md
│   │   ├── staging.md
│   │   └── production.md
│   ├── architecture.md                # Architecture overview with Mermaid diagrams
│   └── service-catalogue.md           # Service catalogue entry (microservice)
```

**Syntax**: Subcommands are space-separated arguments: `/dotnet-ai.docs readme`, `/dotnet-ai.docs adr "Decision Title"`. Quoted strings are treated as a single argument.

**Handoffs**: Can be called standalone or as part of the lifecycle after `/dotnet-ai.implement`

---

## F. SMART COMMANDS

### `/dotnet-ai.do` - One Command Feature Builder

**Description**: Chains the full lifecycle automatically for simple-to-medium features. The fastest way to go from idea to PR.

**Usage**:
```
/dotnet-ai.do "Add order management"                    # Full auto
/dotnet-ai.do "Add order management" --dry-run          # Preview only
/dotnet-ai.do "Add search endpoint for products"        # Simple feature
```

**Flow**:
1. **Specify**: Generate feature spec from description
2. **Quick Clarify**: If ambiguities found, ask max 3 questions inline (no separate command)
3. **Plan**: Auto-generate plan (show summary, ask "Proceed? [Y/n]")
4. **Implement**: Execute tasks with build verification
5. **Review + Verify**: Run standards review and verification
6. **PR**: Create PR(s)
7. **Report**: Show summary of everything that was done

**Smart Behavior — when does it pause?**:
- **Never pauses** for simple features (1 repo, <10 tasks) — fully automatic start to finish
- **Pauses after plan** for complex features (multi-repo or >10 tasks) — shows plan summary, asks "Proceed? [Y/n]"
- **Pauses on ambiguity** — asks max 3 clarifying questions inline, then continues
- Detects project mode automatically (generic vs microservice)
- Skips clarify if spec has no ambiguities
- Skips analyze for single-repo projects
- Shows progress: "Step 3/6: Implementing... (T005/T012)"

**Recommendation**: Use `/dotnet-ai.do` for everything. It's smart enough to pause when needed. You only need the full lifecycle (`/dotnet-ai.specify` → `plan` → `implement`) if you want to manually edit the spec or plan before implementing.

**Flags**:
- `--dry-run`: Run specify + plan only, show what would happen, stop
- `--no-pr`: Do everything except create PR
- `--no-review`: Skip review and verify steps (for quick iterations)

---

### `/dotnet-ai.status` - Feature Status Dashboard

**Description**: Show current feature progress and what to do next.

**Usage**:
```
/dotnet-ai.status                    # Current feature
/dotnet-ai.status 001                # Specific feature by ID
/dotnet-ai.status --all              # All features
```

**Output Example**:
```
Feature: 001-order-management
Status:  IN PROGRESS (implementing)
Mode:    Microservice

Progress:
  [x] Specified  (spec.md)
  [x] Planned    (plan.md, service-map.md)
  [x] Tasks      (18 tasks generated)
  [>] Implement  (12/18 tasks complete, T013 in progress)
  [ ] Review
  [ ] Verify
  [ ] PR

Repos:
  command    ✓ 6/6 tasks done   branch: feature/001-orders
  query      ✓ 4/4 tasks done   branch: feature/001-orders
  processor  > 2/4 tasks done   branch: feature/001-orders  ← current
  gateway    · 0/3 tasks done   not started
  controlpanel · 0/1 tasks done not started

Next: /dotnet-ai.implement --resume    (continue from T013)
```

---

### `/dotnet-ai.undo` - Revert Last Action

**Description**: Safely revert the last implementation step or code generation.

**Usage**:
```
/dotnet-ai.undo                      # Undo last action
/dotnet-ai.undo T005                 # Undo specific task
/dotnet-ai.undo --list               # Show undo history
```

**Flow**:
1. Read last action from `.dotnet-ai-kit/features/NNN/undo-log.md`
2. Show what will be reverted: "Undo T005: Revert 3 files in command repo?"
3. On confirmation:
   - `git checkout -- {files}` for modified files
   - `rm {files}` for newly created files
   - Update tasks.md: mark task as pending again
4. Report: "T005 reverted. 3 files restored."

**Safety**:
- Only reverts files touched by the last task (not the entire branch)
- Shows diff preview before reverting
- Cannot undo across repos (one repo at a time)
- Cannot undo committed changes (only uncommitted work)
- For committed work: "Use `git revert` or `git reset` manually"

**Undo Log**: Each task records its file changes in `features/NNN/undo-log.md`:
```
## T005 - Create OrderController
- created: Controllers/OrderController.cs
- created: Models/CreateOrderRequest.cs
- modified: Program.cs (added service registration)
```

---

### `/dotnet-ai.explain` - Learn Patterns

**Description**: Explain architecture patterns, code patterns, or tool commands with examples.

**Usage**:
```bash
/dotnet-ai.explain aggregate           # What is an aggregate? When to use it?
/dotnet-ai.explain event-sourcing      # How event sourcing works in our stack
/dotnet-ai.explain outbox              # Outbox pattern explained
/dotnet-ai.explain vsa                 # Vertical Slice Architecture
/dotnet-ai.explain "clean architecture" # Clean Architecture pattern
/dotnet-ai.explain implement           # How /dotnet-ai.implement works
/dotnet-ai.explain --tutorial          # Interactive onboarding: build your first feature
/dotnet-ai.explain --mistakes          # Common mistakes and anti-patterns
```

**Flow**:
1. Match topic to knowledge docs, skills, or commands
2. Generate explanation with:
   - What it is (2-3 sentences)
   - When to use it (bullet list)
   - Code example from our patterns
   - Common mistakes for this pattern (what NOT to do)
   - How the tool supports it
3. For architecture topics: include a Mermaid diagram

**Interactive Tutorial** (`--tutorial`):
Guided hands-on walkthrough for new developers:
```
Step 1/5: Let's build a simple Order feature
  → Creating a minimal spec... (shows spec.md)
  → "Does this look right? [Y/edit/skip]"

Step 2/5: Planning the implementation
  → Shows plan with layers/services
  → Explains WHY each layer is needed

Step 3/5: Implementing (you watch, tool explains)
  → Generates code step by step
  → After each file: explains what it does and why

Step 4/5: Running tests
  → Shows test results, explains what was tested

Step 5/5: Creating a PR
  → Shows PR description, explains the review process

Tutorial complete! You just built a feature using the full lifecycle.
Run /dotnet-ai.do "your own feature" to try it yourself.
```
Uses `--dry-run` mode internally — no real changes to your project unless you opt in.

**Topics covered**:
- All architecture patterns (VSA, Clean Arch, DDD, Microservices, CQRS)
- All microservice patterns (aggregate, event, outbox, handler, listener, etc.)
- All tool commands (what each command does, when to use it)
- .NET patterns (DI, Options, Result pattern, Polly, etc.)
- Common mistakes per pattern (anti-patterns)

**Source**: Pulls from knowledge docs + skills, not generic AI knowledge. Explanations match the actual patterns used by the tool.

---

## Quick Reference

| Need | Command |
|------|---------|
| Build a feature fast | `/dotnet-ai.do "description"` |
| Check where I am | `/dotnet-ai.status` |
| Add CRUD endpoint | `/dotnet-ai.add-crud Entity` |
| Add tests to existing code | `/dotnet-ai.add-tests` |
| Undo last step | `/dotnet-ai.undo` |
| Learn a pattern | `/dotnet-ai.explain topic` |
| New to the tool? | `/dotnet-ai.explain --tutorial` |
| Preview before doing | Add `--dry-run` to any command |

---

## Command Chaining (Full Feature Lifecycle)

```
/dotnet-ai.configure           ← First time only
    ↓
/dotnet-ai.specify "Add order management"
    ↓
/dotnet-ai.clarify             ← Optional, recommended
    ↓
/dotnet-ai.plan                ← Plans across all repos
    ↓
/dotnet-ai.tasks               ← Tasks per repo
    ↓
/dotnet-ai.analyze             ← Cross-service check
    ↓
/dotnet-ai.implement           ← Clone → Branch → Code → Build → Test
    ↓
/dotnet-ai.docs                ← Generate/update documentation
    ↓
/dotnet-ai.review              ← Standards + CodeRabbit
    ↓
/dotnet-ai.verify              ← Final verification
    ↓
/dotnet-ai.pr                  ← PRs in all repos
    ↓
/dotnet-ai.wrap-up             ← Session handoff
```

### Revision Loop (when PR needs changes)

If a PR receives review feedback or is rejected:
```
/dotnet-ai.implement --resume     ← Resume from last checkpoint, apply PR feedback
    ↓
/dotnet-ai.docs                   ← Update documentation if needed
    ↓
/dotnet-ai.review                 ← Re-review changes
    ↓
/dotnet-ai.verify                 ← Re-verify build/test/format
    ↓
/dotnet-ai.pr --update            ← Push changes to existing PR
```

The tool detects existing feature branches and PRs, updating them rather than creating new ones.

### Single-Repo Flow (Generic .NET Projects)

For generic .NET projects (VSA, Clean Arch, DDD) with a single repository:

```
/dotnet-ai.configure               ← Set up company, project name
    ↓
/dotnet-ai.specify "Feature"       ← Feature spec (no service map needed)
    ↓
/dotnet-ai.clarify                 ← Resolve ambiguities
    ↓
/dotnet-ai.plan                    ← Plan within single repo (layers, not services)
    ↓
/dotnet-ai.tasks                   ← Tasks organized by layer (Domain → Application → Infrastructure → API)
    ↓
/dotnet-ai.analyze                 ← Architecture consistency (layer boundaries, naming, patterns)
    ↓
/dotnet-ai.implement               ← Implement in single repo
    ↓
/dotnet-ai.docs → review → verify → pr → wrap-up
```

Key differences from microservice flow:
- No service map — single project structure
- Tasks organized by architectural layer, not by service
- Analyze checks layer boundaries instead of cross-service consistency
- No multi-repo orchestration needed
- Single PR instead of linked PRs across repos

---

## G. COMMAND ALIAS SYSTEM

### How It Works

During `/dotnet-ai.configure` (or `dotnet-ai init`), the user chooses a command style:

| Style | Example | Files Created |
|-------|---------|---------------|
| **Full** (default) | `/dotnet-ai.specify` | `dotnet-ai.specify.md` only |
| **Short** | `/dai.spec` | `dai.spec.md` only |
| **Both** | Either works | Both files (short includes long) |

### Alias Mapping

| Full Name | Short Alias | Purpose |
|-----------|-------------|---------|
| `/dotnet-ai.do` | `/dai.do` | One-command feature builder |
| `/dotnet-ai.specify` | `/dai.spec` | Feature specification |
| `/dotnet-ai.clarify` | `/dai.clarify` | Resolve ambiguities |
| `/dotnet-ai.plan` | `/dai.plan` | Implementation plan |
| `/dotnet-ai.tasks` | `/dai.tasks` | Generate tasks |
| `/dotnet-ai.analyze` | `/dai.check` | Consistency analysis |
| `/dotnet-ai.implement` | `/dai.go` | Execute implementation |
| `/dotnet-ai.docs` | `/dai.docs` | Generate documentation |
| `/dotnet-ai.review` | `/dai.review` | Standards review |
| `/dotnet-ai.verify` | `/dai.verify` | Verification pipeline |
| `/dotnet-ai.pr` | `/dai.pr` | Create pull requests |
| `/dotnet-ai.status` | `/dai.status` | Feature status |
| `/dotnet-ai.init` | `/dai.init` | Initialize project |
| `/dotnet-ai.configure` | `/dai.config` | Configure settings |
| `/dotnet-ai.add-aggregate` | `/dai.agg` | Add aggregate |
| `/dotnet-ai.add-entity` | `/dai.entity` | Add entity |
| `/dotnet-ai.add-event` | `/dai.event` | Add event |
| `/dotnet-ai.add-endpoint` | `/dai.ep` | Add endpoint |
| `/dotnet-ai.add-page` | `/dai.page` | Add page |
| `/dotnet-ai.add-crud` | `/dai.crud` | Full CRUD |
| `/dotnet-ai.add-tests` | `/dai.tests` | Generate missing tests |
| `/dotnet-ai.checkpoint` | `/dai.save` | Save progress |
| `/dotnet-ai.wrap-up` | `/dai.done` | End session |
| `/dotnet-ai.undo` | `/dai.undo` | Revert last action |
| `/dotnet-ai.explain` | `/dai.explain` | Learn patterns |

### Implementation

Short alias command files contain a single include directive pointing to the full command:

```markdown
---
description: "Alias for /dotnet-ai.specify"
---
$INCLUDE dotnet-ai.specify.md
```

The CLI copies both files during `dotnet-ai init`. For AI tools that don't support includes (Cursor, Copilot), the short alias file contains the full command content (duplicated).

### Configuration

```yaml
# .dotnet-ai-kit/config.yml
command_style: "both"   # full | short | both
```

Changing style after init: run `dotnet-ai upgrade --style short` to switch.
