---
name: dotnet-ai-multi-repo-workflow
description: >
  Cross-repo coordination for microservice development. Covers dependency chains,
  deployment order, shared contracts, and parallel development strategies.
  Trigger: multi-repo, cross-repo, dependency chain, coordination.
category: workflow
agent: dotnet-architect
---

# Multi-Repo Workflow — Cross-Service Coordination

## Core Principles

- Each microservice lives in its own repository
- Shared contracts (proto files, event data types) need coordinated updates
- Deployment follows dependency order: command -> query -> processor -> gateway
- Changes spanning multiple repos need coordinated PRs
- Feature branches across repos share the same feature name

## Key Patterns

### Repository Structure

```
{company}-{domain}-command/        # Command-side event sourcing
{company}-{domain}-query/          # Query-side SQL projections
{company}-{domain}-cosmos-query/   # Query-side Cosmos projections
{company}-{domain}-processor/      # Event processor
{company}-{domain}-gateway/        # REST API gateway
{company}-{domain}-controlpanel/   # Blazor control panel
{company}-shared-contracts/        # Shared proto files, event types
```

### Dependency Chain

```
shared-contracts (proto files, event data types)
    ↓
command (produces events)
    ↓
query (consumes events, provides query API)
    ↓
processor (routes events, calls query/command via gRPC)
    ↓
gateway (calls command + query via gRPC)
    ↓
controlpanel (calls gateway via REST)
```

### Cross-Repo Feature Implementation Order

```
Step 1: shared-contracts
  - Add new event data types
  - Add new proto messages/RPCs
  - PR and merge

Step 2: command
  - Add aggregate behavior
  - Add command handler
  - Add event store configuration
  - PR and merge

Step 3: query
  - Add query entity
  - Add event handlers
  - Add query handlers
  - PR and merge

Step 4: processor (if needed)
  - Add event routing for new event types
  - Add cross-service handlers
  - PR and merge

Step 5: gateway
  - Add REST controller endpoint
  - Add gRPC client registration
  - PR and merge

Step 6: controlpanel (if needed)
  - Add gateway facade method
  - Add UI page/dialog
  - PR and merge
```

### Branch Naming Convention

```
Feature: feature/{feature-name}
Bugfix:  fix/{issue-description}
Hotfix:  hotfix/{issue-description}

Example across repos:
  {domain}-command:      feature/order-export
  {domain}-query:        feature/order-export
  {domain}-gateway:      feature/order-export
```

### Coordinated Deployment

```bash
# Deploy in order
kubectl apply -f {domain}-command/deploy/prod-manifest.yaml
# Wait for rollout
kubectl rollout status deployment/{domain}-command -n {company}-prod

kubectl apply -f {domain}-query/deploy/prod-manifest.yaml
kubectl rollout status deployment/{domain}-query -n {company}-prod

kubectl apply -f {domain}-gateway/deploy/prod-manifest.yaml
kubectl rollout status deployment/{domain}-gateway -n {company}-prod
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Deploying gateway before query | Follow dependency chain order |
| Breaking proto contracts | Additive changes only; never remove fields |
| Different branch names across repos | Use same feature name across all repos |
| Shared contracts as NuGet package | Copy proto files or use git submodule |

## Detect Existing Patterns

```bash
# Find shared contracts
find ../  -name "shared-contracts" -type d 2>/dev/null

# Find proto file references
grep -r "Protobuf Include" --include="*.csproj" .

# Check remote URLs
git remote -v
```

## Adding to Existing Project

1. **Identify all affected repositories** before starting
2. **Start with shared contracts** (proto files, event types)
3. **Follow the dependency chain** for implementation order
4. **Use consistent branch names** across all repos
5. **Deploy in dependency order** — command first, gateway last
