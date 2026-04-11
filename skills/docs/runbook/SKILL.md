---
name: runbook
description: >
  Use when creating deployment runbooks, troubleshooting guides, or rollback procedures.
metadata:
  category: docs
  agent: docs-engineer
  when-to-use: "When creating deployment runbooks, troubleshooting guides, or rollback procedures"
---

# Runbook — Deployment & Troubleshooting

## Core Principles

- Runbooks provide step-by-step deployment and operations procedures
- Per-environment variants: dev, staging, production
- Include prerequisites, steps, verification, and rollback
- Microservice mode: service deployment order and dependency checks
- Troubleshooting section covers common issues and resolutions

## Key Patterns

### Deployment Runbook Template

```markdown
# Deployment Runbook: {Service Name}

## Prerequisites
- [ ] Azure CLI authenticated (`az login`)
- [ ] kubectl configured for target cluster
- [ ] Docker image built and pushed to ACR
- [ ] Database migrations applied (if applicable)
- [ ] Service Bus topics/subscriptions created (if new)
- [ ] Environment secrets configured in K8s

## Pre-Deployment Checks
1. Verify current service health: `kubectl get pods -n {company}-{env}`
2. Check Service Bus dead letter queue is empty
3. Verify database migration status
4. Confirm no active deployments in progress

## Deployment Steps

### Step 1: Apply Database Migrations
```bash
dotnet ef database update \
  --project src/{Company}.{Domain}.Command \
  --connection "#{CONNECTION_STRING}#"
```

### Step 2: Deploy Command Service
```bash
kubectl apply -f deploy/{env}-manifest.yaml -n {company}-{env}
kubectl rollout status deployment/{domain}-command -n {company}-{env} --timeout=300s
```

### Step 3: Verify Command Service
```bash
kubectl get pods -l app={domain}-command -n {company}-{env}
curl -f http://{domain}-command:8080/health/ready
```

### Step 4: Deploy Query Service
```bash
kubectl apply -f deploy/{env}-manifest.yaml -n {company}-{env}
kubectl rollout status deployment/{domain}-query -n {company}-{env} --timeout=300s
```

### Step 5: Deploy Gateway
```bash
kubectl apply -f deploy/{env}-manifest.yaml -n {company}-{env}
kubectl rollout status deployment/{domain}-gateway -n {company}-{env} --timeout=300s
```

## Post-Deployment Verification
1. [ ] All pods running: `kubectl get pods -n {company}-{env}`
2. [ ] Health checks passing for all services
3. [ ] API responds correctly via gateway
4. [ ] Seq logs show no errors
5. [ ] Service Bus messages processing normally

## Rollback Procedure
```bash
# Rollback to previous version
kubectl rollout undo deployment/{domain}-command -n {company}-{env}
kubectl rollout undo deployment/{domain}-query -n {company}-{env}
kubectl rollout undo deployment/{domain}-gateway -n {company}-{env}

# Verify rollback
kubectl rollout status deployment/{domain}-command -n {company}-{env}
```
```

### Troubleshooting Guide

```markdown
## Common Issues

### Pod CrashLoopBackOff
**Symptoms**: Pod restarts repeatedly
**Check**: `kubectl logs {pod-name} -n {company}-{env} --previous`
**Common causes**:
- Missing environment variable or secret
- Database connection string incorrect
- Service Bus connection string expired
**Resolution**: Fix configuration and redeploy

### Service Bus Messages Stuck
**Symptoms**: Messages not being processed, dead letter queue growing
**Check**: Azure portal -> Service Bus -> Topic -> Subscription -> Messages
**Common causes**:
- Processor not running
- Event deserializer missing new event type
- Query database down
**Resolution**: Check processor logs, verify EventDeserializer, check DB

### gRPC Connection Refused
**Symptoms**: Gateway returns 502/503
**Check**: `kubectl get svc -n {company}-{env}` for service endpoints
**Common causes**:
- Target service not running
- Wrong service URL in ExternalServices configuration
- Port mismatch (8080 vs 8081)
**Resolution**: Verify service is running and URL matches K8s service name
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Undocumented deployment steps | Step-by-step runbook for every service |
| No rollback procedure | Always document how to rollback |
| Missing verification steps | Verify after each deployment step |
| Generic troubleshooting | Specific symptoms, checks, and resolutions |

## Detect Existing Patterns

```bash
# Find existing runbooks
find . -name "*runbook*" -o -name "*deployment*" | grep -i ".md"

# Find deployment scripts
find . -name "deploy*" -type f

# Find K8s manifests
find . -name "*manifest*" -name "*.yaml"
```

## Adding to Existing Project

1. **Check for existing runbooks** in `docs/` directory
2. **Follow existing deployment patterns** and tooling
3. **Include all affected services** in multi-service deployments
4. **Document environment-specific** configuration differences
5. **Update troubleshooting** section as new issues are discovered
