---
name: diagram-gen
description: >
  Use when creating Mermaid diagrams for architecture, event flows, or sequence diagrams.
metadata:
  category: docs
  agent: docs-engineer
  when-to-use: "When generating Mermaid diagrams for service topology, event flows, or class structures"
---

# Diagram Generation — Mermaid Patterns

## Core Principles

- Mermaid diagrams are code-based, version-controlled, and render in GitHub
- Use for service topology, event flows, data flows, and sequence diagrams
- Generate from project analysis where possible
- Keep diagrams focused — one concept per diagram
- Update diagrams when architecture changes

## Key Patterns

### Service Topology (Graph)

```mermaid
graph LR
    subgraph "External"
        CLIENT[Client App]
        ADMIN[Admin Panel]
    end

    subgraph "Gateway Layer"
        GW[API Gateway]
    end

    subgraph "Services"
        CMD[Command Service]
        QRY[Query Service]
        PROC[Processor]
    end

    subgraph "Infrastructure"
        SB[Service Bus]
        SQL[(SQL Server)]
        COSMOS[(Cosmos DB)]
    end

    CLIENT -->|REST| GW
    ADMIN -->|REST| GW
    GW -->|gRPC| CMD
    GW -->|gRPC| QRY
    CMD -->|Events| SB
    SB --> PROC
    SB --> QRY
    PROC -->|gRPC| QRY
    CMD --> SQL
    QRY --> SQL
    QRY --> COSMOS
```

### Event Flow (Sequence Diagram)

```mermaid
sequenceDiagram
    actor User
    participant GW as Gateway
    participant CMD as Command
    participant DB as Event Store
    participant OB as Outbox
    participant SB as Service Bus
    participant QRY as Query

    User->>GW: Create Order
    GW->>CMD: gRPC CreateOrder
    CMD->>CMD: Order.Create()
    CMD->>DB: Save Events
    CMD->>OB: Save Outbox
    CMD-->>GW: OrderOutput
    GW-->>User: 201 Created

    Note over OB,SB: Background Publisher
    OB->>SB: Publish Events
    SB->>QRY: OrderCreated
    QRY->>QRY: Create Projection
```

### Entity Relationship (ER Diagram)

```mermaid
erDiagram
    ORDER {
        guid Id PK
        string CustomerName
        decimal Total
        string Status
        int Sequence
        byte[] RowVersion
    }
    ORDER_ITEM {
        guid Id PK
        guid OrderId FK
        guid ProductId
        string ProductName
        int Quantity
        decimal UnitPrice
    }
    ORDER ||--o{ ORDER_ITEM : contains
```

### State Machine (State Diagram)

```mermaid
stateDiagram-v2
    [*] --> Pending: OrderCreated
    Pending --> Processing: OrderAccepted
    Processing --> Shipped: OrderShipped
    Shipped --> Delivered: OrderDelivered
    Pending --> Cancelled: OrderCancelled
    Processing --> Cancelled: OrderCancelled
    Delivered --> [*]
    Cancelled --> [*]
```

### Class Diagram (Simplified)

```mermaid
classDiagram
    class Aggregate~T~ {
        +Guid Id
        +int Sequence
        +LoadFromHistory(events)
        +ApplyChange(event)
        #Apply(event)*
    }

    class Order {
        +string CustomerName
        +decimal Total
        +OrderStatus Status
        +Create(command)$ Order
        +UpdateDetails(command)
        #Apply(event)
    }

    Aggregate~T~ <|-- Order

    class Event~TData~ {
        +Guid AggregateId
        +int Sequence
        +string Type
        +DateTime DateTime
        +TData Data
    }
```

### Deployment Diagram

```mermaid
graph TB
    subgraph "AKS Cluster"
        subgraph "Namespace: company-prod"
            CMD[Command x2]
            QRY[Query x2]
            PROC[Processor x1]
            GW[Gateway x2]
        end
    end

    subgraph "Azure PaaS"
        SQL[(SQL Server S2)]
        SB[Service Bus Standard]
        COSMOS[(Cosmos DB 400 RU)]
        ACR[Container Registry]
    end

    GH[GitHub Actions] -->|push| ACR
    ACR -->|pull| CMD & QRY & PROC & GW
```

## Diagram Selection Guide

| Purpose | Diagram Type | Mermaid Syntax |
|---|---|---|
| Service communication | Graph/Flowchart | `graph LR/TB` |
| Request flow | Sequence Diagram | `sequenceDiagram` |
| Data model | ER Diagram | `erDiagram` |
| Entity lifecycle | State Diagram | `stateDiagram-v2` |
| Class hierarchy | Class Diagram | `classDiagram` |
| Deployment topology | Graph | `graph TB` with subgraphs |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Image-based diagrams in repo | Use Mermaid for version control |
| Overly complex single diagram | Split into focused diagrams |
| Diagrams without context | Add title and brief description |
| Stale diagrams | Update when architecture changes |

## Detect Existing Patterns

```bash
# Find Mermaid diagrams
grep -rl "```mermaid" --include="*.md" .

# Find diagram files
find . -name "*diagram*" -o -name "*flow*" | grep -i ".md"
```

## Adding to Existing Project

1. **Use Mermaid** for all new diagrams (renders in GitHub/GitLab)
2. **One diagram per concept** — don't combine too many ideas
3. **Place in `docs/` directory** alongside architecture docs
4. **Reference from README** and onboarding docs
5. **Update on architecture changes** as part of the PR
