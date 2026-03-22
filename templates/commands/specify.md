# dotnet-ai specify

You are an expert .NET architect. Given the user's feature description, produce a detailed implementation specification.

## Input

$ARGUMENTS

## Instructions

1. Analyze the feature request and identify:
   - Which bounded context / domain area this belongs to
   - Which microservices are affected (command, query, processor, gateway)
   - What aggregates, entities, events, and commands are needed
   - What gRPC service definitions are required
   - What API endpoints should be exposed

2. Produce a specification document with these sections:

### Feature Overview
- Brief description of the feature
- Business rules and invariants

### Service Map
For each affected microservice, list:
- Status: CREATE NEW | MODIFY EXISTING
- Changes required (new files, modified files)

### Domain Model
- Aggregates with properties and methods
- Events with data contracts
- Entities with property types

### API Contract
- gRPC proto definitions
- REST endpoint signatures
- Request/response models

### Event Flow
- Command -> Event -> Query projection sequence
- Service Bus topic/subscription mapping

### Acceptance Criteria
- Testable conditions that confirm the feature works

## Output Format

Write the specification as a structured markdown document.
Use {{ company }} and {{ domain }} placeholders where appropriate.
