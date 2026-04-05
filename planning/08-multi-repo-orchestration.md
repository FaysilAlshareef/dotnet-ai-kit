# dotnet-ai-kit - Multi-Repo Orchestration

## The Core Problem

A single feature like "Add Order Management" requires changes across:
- **Command repo**: OrderAggregate, OrderCreated/Updated events, outbox
- **Query repo**: Order entity, event handlers, queries, gRPC service
- **Processor repo**: Order event listener, routing to other services
- **Gateway repo**: Order REST endpoints, gRPC client, models
- **Control Panel**: Order management page, filters, gateway facade

These repos have **dependency order**: Command → Query/Processor → Gateway → ControlPanel

**Note**: This document describes multi-repo orchestration for microservice features. For single-repo generic .NET projects, the SDD lifecycle works within a single repository — see Command Chaining in `04-commands-design.md` for the single-repo flow.

## Multi-Repo Workspace Model

### Workspace Structure
```
workspace/                        # User's working directory
├── .dotnet-ai-kit/
│   ├── config.yml                # Company, repos, permissions
│   ├── features/
│   │   └── 001-order-management/
│   │       ├── spec.md
│   │       ├── plan.md
│   │       ├── service-map.md
│   │       ├── event-flow.md
│   │       ├── tasks.md
│   │       ├── contracts/
│   │       └── checklists/
│   └── handoff.md
# See 13-handoff-schemas.md for formal schemas of all feature files
│
├── repos/                        # Cloned repos (or symlinks to existing)
│   ├── {company}.{domain}.commands/
│   ├── {company}.{domain}.queries/
│   ├── {company}.{domain}.processor/
│   ├── {company}.gateways.{domain}.management/  # New projects use Scalar (Swagger is legacy only)
│   └── {company}-control-panel/
```

### Workspace Coordination Model

The tool does NOT require a central workspace directory. Repos can live anywhere on the developer's machine.

**How it works:**
- Repo paths are stored in `.dotnet-ai-kit/config.yml` (absolute paths or GitHub URLs)
- Feature files (spec, plan, tasks) live in the CURRENT working directory's `.dotnet-ai-kit/features/`
- The tool navigates to each repo path to execute tasks, then returns to the workspace
- If a repo is a GitHub URL and not cloned locally, the tool clones it to `./repos/` under the workspace

**No symlinks, no submodules, no monorepo required.** Each repo remains independent — the tool just knows where they are.

### Repo Discovery

**Option 1: Existing local repos (most common)**
```yaml
# .dotnet-ai-kit/config.yml
repos:
  command: C:\Users\user\source\repos\Company.Order.Commands
  query: C:\Users\user\source\repos\Company.Order.Queries
  processor: C:\Users\user\source\repos\Company.Order.Processor
  gateway: C:\Users\user\source\repos\Company.Gateways.Order.Management
  controlpanel: C:\Users\user\source\repos\Company-control-panel
```

**Option 2: GitHub repos (cloned on demand)**
```yaml
repos:
  command: github:org/company-order-commands
  query: github:org/company-order-queries
  processor: github:org/company-order-processor
  gateway: null  # Will be created
  controlpanel: github:org/company-control-panel
```

**Option 3: Per-feature override**
The `/dotnet-ai.specify` and `/dotnet-ai.plan` commands can ask for repo paths if not configured.

### Config Precedence

When repo paths conflict, the following order applies:
1. **Per-feature override** (specified in `/dotnet-ai.plan`) — highest priority
2. **Command-line argument** (passed to implement) — overrides config
3. **config.yml repos section** — default, lowest priority

If a repo is `null` in config, the tool asks the user during `/dotnet-ai.plan`.

Per-feature overrides are stored in `features/NNN/plan.md` alongside the service map. They apply only to that feature and do not modify `config.yml`.

---

## Implementation Order (Dependency Chain)

```
Phase 1: COMMAND SIDE (must be first - events define everything)
  │
  ├─── Create/update aggregates
  ├─── Define events with data schemas
  ├─── Implement handlers
  ├─── Configure outbox + service bus publisher
  ├─── Add proto definitions (server)
  └─── Tests
  │
Phase 2: QUERY SIDE + PROCESSOR (can be parallel)
  │
  ├─── Query: Create entities from event constructors
  ├─── Query: Implement event handlers with sequence
  ├─── Query: Add query handlers + gRPC services
  ├─── Query: Add proto definitions (server)
  ├─── Processor: Add listeners for new events
  ├─── Processor: Implement routing handlers
  └─── Tests for both
  │
Phase 3: GATEWAY (needs query protos)
  │
  ├─── Add query/command proto files (client)
  ├─── Register gRPC clients
  ├─── Create controllers with endpoints
  ├─── Add request/response models
  ├─── Add mapping extensions
  └─── Tests (if applicable)
  │
Phase 4: CONTROL PANEL (needs gateway endpoints)
  │
  ├─── Add gateway management class
  ├─── Add endpoint methods
  ├─── Create filter model (QueryStringBindable)
  ├─── Create Blazor page with MudDataGrid
  ├─── Register in menu items
  └─── Register service in WebApp
```

### Partial Failure Recovery

If implementation fails mid-feature (e.g., Phase 2 fails after Phase 1 succeeds):

1. **Changes stay on feature branches** — nothing is merged until all PRs are approved
2. **Task status updated** in `features/NNN/tasks.md` — completed tasks marked, failed task logged with error
3. **Next session**: `/dotnet-ai.implement --resume` picks up from the failed task
4. **Already-completed repos**: skipped (verified by git status on feature branch)
5. **Failed repo**: error context preserved in handoff.md for debugging

No rollback needed — feature branches are isolated until PR merge.

---

## Repo Operations (via GitHub MCP + CLI)

### Cloning
```bash
# Clone via gh CLI
gh repo clone {org}/{repo} repos/{local-name}
```

### Branch Management
```bash
# Create feature branch in each repo
cd repos/{repo}
git checkout -b feature/{NNN}-{feature-name}
```

### Implementation
- Open each repo directory
- Detect project type and .NET version
- Load appropriate agent and skills
- Execute tasks using existing patterns
- Build and test after each task group

### Pull Request Creation
```bash
# Create PR in each repo
cd repos/{repo}
git push -u origin feature/{NNN}-{feature-name}
gh pr create \
  --title "feat: {feature-name}" \
  --body "$(cat <<'EOF'
## Summary
{auto-generated from spec}

## Changes
{auto-generated from tasks}

## Related PRs
- Command: {pr-url}
- Query: {pr-url}
- Processor: {pr-url}
- Gateway: {pr-url}
- ControlPanel: {pr-url}

## Test Results
{auto-generated from verify}
EOF
)"
```

---

## Existing Project Detection

When working with an existing repo, the tool:

### 1. Detects .NET Version
```xml
<!-- Reads from .csproj -->
<TargetFramework>net9.0</TargetFramework>  → .NET 9
<TargetFramework>net8.0</TargetFramework>  → .NET 8
```

### 2. Detects Project Type
| Pattern Found | Project Type |
|--------------|-------------|
| `Aggregate<T>` base class, `Event<T>`, OutboxMessage | Command |
| Entity with private setters, `IRequestHandler<Event<T>, bool>` | Query (SQL) |
| `IContainerDocument`, `PartitionKeys` | Query (Cosmos) — same folder name as SQL query (`{company}.{domain}.queries`), detected by code patterns |
| `IHostedService`, `ServiceBusSessionProcessor` | Processor |
| REST Controllers + `AddGrpcClient<T>` | Gateway (Scalar = current, Swagger = legacy) |
| Blazor components + `ResponseResult<T>` | Control Panel |

### 3. Learns Existing Conventions
- Namespace format
- Folder structure
- Naming patterns
- .NET version-specific syntax (e.g., primary constructors only in .NET 8+)
- Existing service bus topic names
- Existing gRPC service names

### 4. Respects What Exists
- Does NOT upgrade .NET version
- Does NOT refactor existing code
- Does NOT change naming patterns
- DOES follow existing patterns for new code
- DOES suggest improvements in review (not in implement)

---

## Service Map Example

Generated by `/dotnet-ai.plan`:

```markdown
## Service Map: Order Management Feature

| Service | Repo | Status | Changes |
|---------|------|--------|---------|
| Command | company-order-commands | EXISTS | + OrderAggregate, + 3 events |
| Query | company-order-queries | EXISTS | + Order entity, + 3 handlers, + 2 queries |
| Processor | company-order-processor | EXISTS | + OrderListener, + 2 routing handlers |
| Gateway | company-gateways-order-management | CREATE NEW | Full project scaffold |
| ControlPanel | company-control-panel | EXISTS | + Orders module (API + Presentation) |

### Event Flow
```
OrderCreated (Command)
  → OrderCreatedHandler (Query) → creates Order entity
  → OrderListener (Processor) → routes to external services

OrderUpdated (Command)
  → OrderUpdatedHandler (Query) → updates Order entity

OrderCompleted (Command)
  → OrderCompletedHandler (Query) → marks complete
  → OrderListener (Processor) → triggers notification
```

### New Proto Definitions
- `order_commands.proto` (Command - server)
- `order_queries.proto` (Query - server, Gateway - client)
```

---

## Event Catalogue

Each service maintains an event catalogue documenting all events it produces and consumes.

### Catalogue Structure (per service)
```
.dotnet-ai-kit/features/NNN-feature-name/
├── ...
└── event-catalogue/
    ├── command-events.md      # Events produced by command side
    ├── query-handlers.md      # Events consumed by query side
    └── processor-routing.md   # Events routed by processor
```

### Catalogue Entry Format
```markdown
## Event: OrderCreated
- **Producer**: Command (OrderAggregate)
- **Consumers**: Query (OrderCreatedHandler), Processor (OrderListener)
- **Version**: 1
- **Data Schema**: OrderCreatedData { OrderId, CustomerId, Items[], CreatedAt }
- **Topic**: {company}-order-commands
- **Idempotency**: Sequence-based (query), client-sent ID (command)
```

The `/dotnet-ai.analyze` command validates event catalogue consistency across all services.

---

## Creating New Projects

When service-map shows "CREATE NEW":

1. Ask user for GitHub repo URL (or create new)
2. Scaffold from template:
   - Use company name from config
   - Use domain name from feature
   - Use configured .NET version (or latest)
3. Initialize with correct patterns
4. Push to GitHub
5. Continue with feature implementation

```
/dotnet-ai.implement detects:
  Gateway repo: null (not configured)

  "The gateway project doesn't exist yet. Options:"
  1. Create new repo on GitHub: {org}/company-gateways-order-management
  2. Add to existing repo: {provide-path}
  3. Skip gateway for now

  > 1

  Creating repo... Scaffolding gateway project...
  Company: {from config}
  Domain: Order
  Type: Management Gateway
  .NET: 10.0

  Created and pushed. Continuing with implementation...
```

---

## Tooling Deployment to Secondary Repos

When `dotnet-ai configure` or `deploy_to_linked_repos()` runs for a multi-repo project, the tool automatically deploys its full tooling stack to each configured secondary repository. This ensures every repo has consistent commands, rules, skills, and enforcement.

### `deploy_to_linked_repos()` Function

Called by `configure` when local secondary repos are detected. For each secondary repo:

1. **Version check** — skip if secondary has a newer CLI version
2. **Dirty check** — skip if secondary has uncommitted changes
3. **Branch creation** — creates/checks out `chore/brief-deploy-{version}` branch
4. **Full tooling deploy**:
   - Commands (using secondary's own `command_style` from its `config.yml`)
   - Rules
   - Architecture profile via `copy_profile()` (based on secondary's `project_type`)
   - Skills with token resolution for secondary's `detected_paths`
   - Agents
   - PreToolUse enforcement hook via `copy_hook()` (Claude only)
5. **Write `linked_from`** — records primary repo path in secondary's `config.yml`
6. **Atomic commit** — stages tool directories and commits with `chore: deploy dotnet-ai-kit tooling`

### Key Design Points

- **Secondary `ai_tools`**: Deployment targets the secondary repo's own configured `ai_tools`, not the primary's. If secondary uses `cursor`, cursor files are deployed.
- **Secondary `command_style`**: Commands are deployed in the style configured for the secondary repo (full/short/both).
- **`linked_from` field**: Marks secondary repos as linked, enabling cross-repo status reporting in `check`.

### Architecture Profile (`copy_profile()`)

Deploys an architecture-specific guidance file to the AI tool's rules directory:

```
{rules_dir}/architecture-profile.md
```

The profile is selected based on `project_type` from `project.yml`. For example:
- `command` → `profiles/microservice/command.md`
- `query-sql` → `profiles/microservice/query-sql.md`
- `clean-arch` → `profiles/generic/clean-arch.md`

### Enforcement Hook (`copy_hook()`)

Injects a `PreToolUse` hook into `.claude/settings.json` that runs a Haiku model check before every Write/Edit operation:

```json
{
  "_source": "dotnet-ai-kit-arch",
  "type": "prompt",
  "matcher": "Write|Edit",
  "prompt": "{architecture-profile-content}",
  "model": "claude-haiku-4-5-20251001",
  "timeout": 15000
}
```

The `_source` tag allows safe removal/replacement on subsequent deploys.

### `FeatureBrief` Model

During `/dai.specify`, a `feature-brief.md` is written to each affected secondary repo at `.dotnet-ai-kit/features/{NNN}-{name}/feature-brief.md`. Fields:
- `feature_id` — NNN-short-name (matches primary feature ID)
- `feature_name` — human-readable name
- `phase` — current lifecycle phase (Specified, Planned, etc.)
- `source_repo` — primary repo name/path
- `this_repo_role` — this repo's role in the service map
- `projected_date` — expected delivery date
- `required_changes` — filtered change list for this repo
- `events_produced` / `events_consumed` — cross-service event contracts

### Branch Safety

All SDD lifecycle commands that touch secondary repos (specify, clarify, plan, tasks, implement) include a "Secondary Repo Branch Safety" section ensuring:
- If on main/master/develop: create `chore/brief-{NNN}-{name}` branch
- If branch already exists: check out existing branch
- If dirty working directory: warn and skip that repo
