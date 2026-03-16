---
name: architecture-docs
description: >
  Architecture overview documentation with Mermaid diagrams. Covers service
  topology, event flows, data flows, and system architecture documentation.
  Trigger: architecture docs, Mermaid diagram, system overview, service map.
category: docs
agent: docs-engineer
---

# Architecture Docs — Overview & Diagrams

## Core Principles

- Architecture docs provide high-level system understanding
- Mermaid diagrams are code-based and version-controlled
- Service topology shows how services communicate
- Event flow diagrams show event production and consumption
- Data flow diagrams show information movement through the system

## Key Patterns

### System Architecture Overview

```markdown
# {Domain} System Architecture

## Overview
The {Domain} system follows a CQRS + Event Sourcing microservice architecture.
Commands produce events that are projected to read models.

## Services
| Service | Purpose | Database | Communication |
|---|---|---|---|
| {domain}-command | Event sourcing, business logic | SQL Server | gRPC (server) |
| {domain}-query | Read projections | SQL Server | gRPC (server) |
| {domain}-cosmos-query | NoSQL projections | Cosmos DB | gRPC (server) |
| {domain}-processor | Event routing | None | gRPC (client), Service Bus |
| {domain}-gateway | REST API | None | gRPC (client) |
| {domain}-controlpanel | Admin UI | None | REST (client) |
```

### Service Topology Diagram

```mermaid
graph LR
    CP[Control Panel] -->|REST| GW[Gateway]
    GW -->|gRPC| CMD[Command Service]
    GW -->|gRPC| QRY[Query Service]
    CMD -->|Events| SB[Service Bus]
    SB -->|Events| PROC[Processor]
    PROC -->|gRPC| QRY
    SB -->|Events| QRY
    CMD -->|SQL| CMDDB[(Command DB)]
    QRY -->|SQL| QRYDB[(Query DB)]
```

### Event Flow Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Command
    participant ServiceBus
    participant Processor
    participant Query

    Client->>Gateway: POST /api/v1/orders
    Gateway->>Command: gRPC CreateOrder
    Command->>Command: Aggregate.Create()
    Command->>Command: Save Events + Outbox
    Command-->>Gateway: OrderOutput
    Gateway-->>Client: 201 Created

    Command->>ServiceBus: Publish Events (background)
    ServiceBus->>Query: OrderCreated event
    Query->>Query: Create Order projection
    ServiceBus->>Processor: OrderCreated event
    Processor->>Query: gRPC SyncOrder
```

### Data Flow Diagram

```mermaid
graph TB
    subgraph "Command Side"
        CMD_AGG[Aggregate] --> CMD_EVT[Event Store]
        CMD_EVT --> CMD_OUT[Outbox]
    end

    subgraph "Service Bus"
        CMD_OUT --> TOPIC[Topic]
        TOPIC --> SUB_Q[Query Subscription]
        TOPIC --> SUB_P[Processor Subscription]
    end

    subgraph "Query Side"
        SUB_Q --> QRY_H[Event Handler]
        QRY_H --> QRY_DB[(Query DB)]
    end

    subgraph "Processor"
        SUB_P --> PROC_R[Event Router]
        PROC_R --> GRPC[gRPC Calls]
    end
```

### Infrastructure Diagram

```mermaid
graph TB
    subgraph "Azure Kubernetes Service"
        CMD[Command Pod]
        QRY[Query Pod]
        PROC[Processor Pod]
        GW[Gateway Pod]
    end

    subgraph "Azure Resources"
        SQL[(SQL Server)]
        COSMOS[(Cosmos DB)]
        SB[Service Bus]
        ACR[Container Registry]
    end

    CMD --> SQL
    QRY --> SQL
    QRY --> COSMOS
    CMD --> SB
    PROC --> SB
    ACR --> CMD & QRY & PROC & GW
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Image-based diagrams | Use Mermaid (version-controlled, editable) |
| Outdated architecture docs | Generate/update from project analysis |
| Missing service dependencies | Document all communication paths |
| No data flow documentation | Show how data moves through the system |

## Detect Existing Patterns

```bash
# Find existing architecture docs
find . -name "*architecture*" -o -name "*overview*" | grep -i ".md"

# Find Mermaid diagrams
grep -r "```mermaid" --include="*.md" docs/

# Find service references
grep -r "AddGrpcClient\|ServiceBusClient" --include="*.cs" src/
```

## Adding to Existing Project

1. **Check for existing architecture docs** in `docs/` directory
2. **Update diagrams** when adding new services or changing communication
3. **Use Mermaid** syntax for all diagrams (renders in GitHub)
4. **Document event flows** for each major feature
5. **Keep service table** updated with current services and their purposes
