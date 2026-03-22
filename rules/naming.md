---
alwaysApply: true
description: Enforces naming conventions using configured company name and detected project patterns.
---

# Naming Conventions

Use `{Company}` and `{Domain}` placeholders resolved from project config.
If an existing project has different naming conventions, FOLLOW the existing ones.
Only apply these conventions for new files and projects.

## Microservice Mode

- Solution: `{Company}.{Domain}.{Side}.sln` (e.g., `Acme.Order.Commands.sln`)
- Projects: `{Company}.{Domain}.{Side}.{Layer}` (e.g., `Acme.Order.Commands.Domain`)
- Layers: Domain, Application, Infra, Grpc, Test, Test.Live
- Service Bus Topics: `{company}-{domain}-{side}` (lowercase, hyphenated)
- K8s manifests: `{environment}-manifest.yaml`

## Generic Mode

- Solution: `{Company}.{ProjectName}.sln` or `{ProjectName}.sln`
- Projects: Follow detected convention or `{Company}.{ProjectName}.{Layer}`
- Layers depend on architecture:
  - VSA: Features/
  - Clean Architecture: Domain/Application/Infrastructure/API

## Both Modes

### Domain Objects
- Aggregates: PascalCase singular (`Order`, `Invoice`, `Product`)
- Events: `{Aggregate}{Action}` (`OrderCreated`, `InvoiceApproved`)
- Event Data: `{EventName}Data` record (`OrderCreatedData`)

### Handlers and Operations
- Handlers: `{EventName}Handler` or `{CommandName}Handler`
- Commands: `{Action}{Aggregate}Command` (`CreateOrderCommand`)
- Queries: `Get{Entities}Query` (`GetOrdersQuery`)

### DTOs and Contracts
- Output DTOs: `{Entity}Output` or `Get{Entities}Output`
- Proto services: `{Domain}{Side}` (`OrderCommands`, `OrderQueries`)
- Proto files: `snake_case.proto` (`order_commands.proto`)

### Infrastructure and Testing
- Repositories: `I{Entity}Repository` / `{Entity}Repository`
- Fakers: `{Entity}Faker`, `{Event}Faker`
- Asserts: `{Entity}Assert` or `{Entity}sAssert`
- Extensions: `{Entity}{Side}Extensions` (`OrderCommandExtensions`)

### Resources
- Resource files: `Phrases.resx` / `Phrases.en.resx`

## Detection Instructions

Before creating any new file:
1. Scan existing project for naming patterns in namespaces, classes, and file names
2. If existing patterns differ from these conventions, use the existing patterns
3. Only apply these conventions when no existing pattern is detected
4. Check that the `{Company}` and `{Domain}` values match the config
