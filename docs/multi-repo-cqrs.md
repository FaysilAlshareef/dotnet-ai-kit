# Multi-Repo CQRS Setup Walkthrough

dotnet-ai-kit treats CQRS microservices across multiple repositories as a
first-class scenario. Features that span services get a coordinated spec,
per-service implementation plans, filtered feature briefs in each repo, and
linked Pull Requests — all from a single `/dai.do` invocation.

---

## Repository structure

A typical CQRS microservice system has five service roles:

| Role | `--type` value | Owns | Architecture profile |
|------|---------------|------|---------------------|
| Command | `command` | Aggregates, events, outbox | `command` |
| Query (SQL) | `query-sql` | SQL Server read models, event handlers | `query-sql` |
| Query (Cosmos) | `query-cosmos` | Cosmos DB projections | `query-cosmos` |
| Processor | `processor` | Service Bus consumers, side effects | `processor` |
| Gateway | `gateway` | REST endpoints, gRPC clients | `gateway` |
| Control Panel | `controlpanel` | Blazor WASM UI | `controlpanel` |

Each repo lives as a sibling directory on disk:

```
workspace/
├── my-command-service/
├── my-query-service/
├── my-processor-service/
├── my-gateway-service/
└── my-controlpanel/
```

---

## Initial setup

### 1. Initialize the primary repo

Choose one repo as the primary (typically the command service):

```bash
cd my-command-service
dotnet-ai init . --ai claude --type command
```

### 2. Configure linked secondary repos

Tell dotnet-ai-kit about the other repos using `--repos`:

```bash
dotnet-ai configure \
  --company Acme \
  --repos "command=../my-command-service,query=../my-query-service,processor=../my-processor-service,gateway=../my-gateway-service,controlpanel=../my-controlpanel"
```

Or interactively (omit flags to get prompts):

```bash
dotnet-ai configure
```

Repo paths can be local (relative or absolute) or GitHub references:

```bash
# Local paths
--repos "command=../cmd,query=../qry"

# GitHub references (remote — skipped by deploy, used for documentation only)
--repos "command=github:Acme/cmd-service,query=github:Acme/qry-service"
```

### 3. Deploy tooling to secondary repos

After `configure`, dotnet-ai-kit automatically deploys the plugin-native
tooling to every local secondary repo:

```bash
# Preview first
dotnet-ai configure --dry-run --repos "command=../cmd,query=../qry"

# Apply (runs deploy_to_linked_repos internally)
dotnet-ai configure --repos "command=../cmd,query=../qry"
```

For each reachable local secondary repo, the deploy:
1. Auto-initializes `.dotnet-ai-kit/config.yml` and `project.yml` if missing
2. Writes the correct architecture profile based on the repo's role
3. Records `linked_from: /path/to/primary` in the secondary's `config.yml`
4. Creates a `chore/dotnet-ai-kit-setup` branch and commits the tooling files
5. Skips repos with a newer installed version

---

## Config file reference

### Primary repo — `config.yml`

```yaml
company:
  name: Acme
  github_org: AcmeCorp

repos:
  command: ../my-command-service
  query: ../my-query-service
  processor: ../my-processor-service
  gateway: ../my-gateway-service
  controlpanel: ../my-controlpanel

enabled_hosts:
  - claude

permission_profile: standard
```

### Secondary repo — `config.yml`

```yaml
company:
  name: Acme

linked_from: /absolute/path/to/primary

enabled_hosts:
  - claude

permission_profile: standard
```

---

## Building a cross-repo feature

Once all repos are configured, `/dai.do` (or the manual lifecycle) handles
the multi-repo coordination automatically.

```bash
# In the primary repo (Claude Code)
/dai.do "Add order management with tracking"
```

### What happens automatically

**`/dai.specify`** — generates the primary spec and writes a
`feature-brief.md` to every secondary repo:

```
.dotnet-ai-kit/briefs/{primary-repo}/{NNN}-{name}/feature-brief.md
```

Each brief contains a filtered view for that repo:

| Field | Content |
|-------|---------|
| `role` | This repo's role in the feature (e.g., "owns OrderAggregate") |
| `required_changes` | Changes scoped to this repo only |
| `events_produces` | Events this repo will publish |
| `events_consumes` | Events this repo will handle |
| `blocked_by` | Upstream repos that must complete first |
| `blocks` | Downstream repos waiting on this repo |
| `implementation_approach` | Architecture decisions relevant to this repo |

**`/dai.plan`** and **`/dai.implement`** — route to the correct specialist
agent per repo type:

| Repo type | Agent |
|-----------|-------|
| `command` | `command-architect` |
| `query-sql` | `query-architect` |
| `query-cosmos` | `cosmos-architect` |
| `processor` | `processor-architect` |
| `gateway` | `gateway-architect` |
| `controlpanel` | `controlpanel-architect` |

**Branch safety** — lifecycle commands automatically protect secondary repos:

```
If on main/master/develop → create feat/{brief-NNN}-{name} branch
If branch already exists  → check it out
If dirty working directory → warn and skip that repo
```

---

## Branch naming convention

All cross-repo branches follow the same pattern (enforced by the `multi-repo` rule):

| Branch type | Format | Example |
|-------------|--------|---------|
| Feature | `feat/{brief-NNN}-{short-name}` | `feat/001-order-management` |
| Tooling | `chore/brief-{NNN}-{name}` | `chore/brief-001-dotnet-ai-kit-setup` |
| Hotfix | `fix/{brief-NNN}-{short-name}` | `fix/001-order-event-schema` |

Rules: lowercase kebab-case only, no spaces, no underscores.

---

## Deploy order

**Always deploy in this order.** The `multi-repo` rule enforces it — do not
merge PRs in a different order.

```
1. Command     — aggregate & event contract changes first
2. Processor   — event handler changes after Command is deployed
3. Query       — read model changes after events are publishing
4. Gateway     — API route changes after query/command are stable
5. ControlPanel — UI changes last, after all backend services are ready
```

Why: each layer depends on the previous one's contracts. Deploying out of
order causes missing events, broken sequences, or 404 errors in the UI.

---

## Event contract ownership

| Rule | Rationale |
|------|-----------|
| Command service is the **sole owner** of its domain events | Prevents conflicting event definitions across repos |
| Other services (Query, Processor, Gateway) must NOT publish events they don't own | Maintains a clear publisher → subscriber relationship |
| Event contracts are shared via NuGet package or a contracts repo | Single source of truth for event schema |
| **Never** remove or rename fields on existing events | Consumers may be at different deployed versions |
| Use versioned records (`OrderCreatedV2`) for breaking changes | Allows gradual migration without downtime |

---

## Circular dependency rules

```
Gateway  → may call Command and Query
Command  → must NOT call Gateway
Query    → must NOT call Command (directly)
         → use events for cross-service communication
         → never share databases or synchronous HTTP calls between services
```

---

## Checking multi-repo status

```bash
# From the primary repo
dotnet-ai check --verbose    # shows linked repos and their deploy status
dotnet-ai check --json       # includes linked_repos[] in output
```

The `check` output includes a linked repos panel showing each secondary's
`linked_from`, installed version, and whether it needs a re-deploy.

---

## Updating all repos after a plugin upgrade

For plugin-native hosts (Claude Code, Codex CLI, Cursor), updates propagate
automatically — no action needed. For Copilot render files:

```bash
# Primary repo
dotnet-ai upgrade --copilot

# Then repeat in each secondary repo
cd ../my-query-service && dotnet-ai upgrade --copilot
cd ../my-processor-service && dotnet-ai upgrade --copilot
# etc.
```

---

## Troubleshooting

**Secondary repo not found**

```
status: "skipped", reason: "path does not exist"
```

Check that the path in `--repos` is correct relative to the primary repo's
directory, not the current working directory.

**Secondary repo has newer version**

```
status: "skipped", reason: "secondary has newer version"
```

Update the primary repo's CLI (`pip install --upgrade dotnet-ai-kit`) or
pass `--force` to override the version check.

**Repo on main branch**

```
warning: secondary my-query-service is on main — creating feat/001-order-management
```

Normal behaviour. The lifecycle commands automatically create the feature branch.
If you want to work on an existing branch, check it out in the secondary repo
before running the lifecycle command.

**Remote GitHub repos**

```
status: "skipped", reason: "remote URL — cannot deploy locally"
```

GitHub-referenced repos (`github:org/repo`) are skipped for local deployment.
They appear in service maps and feature briefs for documentation purposes only.
Clone the repo locally and use a local path if you want tooling deployed to it.
