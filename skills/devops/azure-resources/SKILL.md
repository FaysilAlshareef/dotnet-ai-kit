---
name: azure-resources
description: >
  Azure resource provisioning for microservices. Covers Service Bus topics/subscriptions,
  Cosmos DB accounts, SQL Server databases, and resource organization.
  Trigger: Azure Service Bus, Cosmos DB, SQL Server, Azure resources, provisioning.
metadata:
  category: devops
  agent: devops-engineer
  when-to-use: "When provisioning Azure resources like Service Bus, Cosmos DB, or SQL Server"
---

# Azure Resources — Service Bus, Cosmos DB, SQL Server

## Core Principles

- Service Bus topics follow naming: `{company}-{domain}-{side}`
- Subscriptions per consumer: `query-subscription`, `processor-subscription`
- Cosmos DB with hierarchical partition keys and direct mode
- SQL Server for command and query databases (separate DBs)
- Resource groups per environment: `{company}-{env}-rg`

## Key Patterns

### Service Bus Topic + Subscription (Azure CLI)

```bash
# Create topic
az servicebus topic create \
  --resource-group {company}-{env}-rg \
  --namespace-name {company}-servicebus \
  --name {company}-{domain}-commands \
  --enable-partitioning false \
  --default-message-time-to-live P7D

# Create subscription with session support
az servicebus topic subscription create \
  --resource-group {company}-{env}-rg \
  --namespace-name {company}-servicebus \
  --topic-name {company}-{domain}-commands \
  --name query-subscription \
  --requires-session true \
  --max-delivery-count 10

az servicebus topic subscription create \
  --resource-group {company}-{env}-rg \
  --namespace-name {company}-servicebus \
  --topic-name {company}-{domain}-commands \
  --name processor-subscription \
  --requires-session true \
  --max-delivery-count 10
```

### Cosmos DB Account + Database

```bash
# Create Cosmos DB account
az cosmosdb create \
  --name {company}-cosmos \
  --resource-group {company}-{env}-rg \
  --default-consistency-level Session \
  --enable-analytical-storage false

# Create database
az cosmosdb sql database create \
  --account-name {company}-cosmos \
  --resource-group {company}-{env}-rg \
  --name {domain}-db

# Create container with hierarchical partition key
az cosmosdb sql container create \
  --account-name {company}-cosmos \
  --resource-group {company}-{env}-rg \
  --database-name {domain}-db \
  --name invoices \
  --partition-key-path "/merchantId" "/reportMonth" "/discriminator" \
  --throughput 400
```

### SQL Server Database

```bash
# Create SQL Database
az sql db create \
  --resource-group {company}-{env}-rg \
  --server {company}-sql-{env} \
  --name {domain}-command-db \
  --service-objective S1

az sql db create \
  --resource-group {company}-{env}-rg \
  --server {company}-sql-{env} \
  --name {domain}-query-db \
  --service-objective S1
```

### Connection String Configuration

```json
{
  "ConnectionStrings": {
    "CommandDb": "Server={company}-sql-{env}.database.windows.net;Database={domain}-command-db;Authentication=Active Directory Default;",
    "QueryDb": "Server={company}-sql-{env}.database.windows.net;Database={domain}-query-db;Authentication=Active Directory Default;"
  },
  "ServiceBus": {
    "ConnectionString": "{company}-servicebus.servicebus.windows.net"
  },
  "CosmosDb": {
    "Endpoint": "https://{company}-cosmos.documents.azure.com:443/",
    "DatabaseName": "{domain}-db"
  }
}
```

### Resource Naming Convention

```
Resource Type    | Naming Pattern                      | Example
---------------- | ----------------------------------- | -------
Resource Group   | {company}-{env}-rg                  | acme-prod-rg
Service Bus      | {company}-servicebus                | acme-servicebus
Topic            | {company}-{domain}-{side}           | acme-order-commands
Subscription     | {consumer}-subscription             | query-subscription
SQL Server       | {company}-sql-{env}                 | acme-sql-prod
SQL Database     | {domain}-{side}-db                  | order-command-db
Cosmos Account   | {company}-cosmos                    | acme-cosmos
Cosmos Database  | {domain}-db                         | order-db
ACR              | {company}acr                        | acmeacr
AKS              | {company}-aks-{env}                 | acme-aks-prod
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Shared database across services | Separate DB per service (command/query) |
| Missing session support | Enable sessions for ordered processing |
| Unlimited delivery count | Set max-delivery-count (e.g., 10) |
| Production resources without backup | Enable geo-redundancy and backups |

## Detect Existing Patterns

```bash
# Find connection strings
grep -r "ConnectionString\|ServiceBus\|CosmosDb" --include="*.json" src/

# Find Azure CLI scripts
find . -name "*.sh" -o -name "*.ps1" | head -10

# Find resource naming
grep -r "{company}" --include="*.yaml" deploy/
```

## Adding to Existing Project

1. **Follow existing naming conventions** for Azure resources
2. **Create topic + subscriptions** before deploying new services
3. **Use Managed Identity** (Active Directory Default) for production
4. **Match Service Bus session support** requirement (always true for ordered processing)
5. **Document resource provisioning** in deployment runbook
