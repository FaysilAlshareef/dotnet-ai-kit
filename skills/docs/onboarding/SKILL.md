---
name: onboarding
description: >
  Developer onboarding documentation generation. Covers setup guides, architecture
  overview, development workflow, and common tasks for new team members.
  Trigger: onboarding, developer guide, setup guide, getting started.
metadata:
  category: docs
  agent: docs-engineer
---

# Onboarding — Developer Documentation

## Core Principles

- Onboarding docs get new developers productive quickly
- Cover environment setup, architecture overview, and daily workflow
- Include common tasks with step-by-step instructions
- Reference existing ADRs and architecture docs
- Keep updated as the project evolves

## Key Patterns

### Onboarding Document Template

```markdown
# Developer Onboarding Guide

## Welcome
Welcome to the {Domain} team! This guide will help you set up your
development environment and understand our architecture.

## Prerequisites
- [ ] .NET SDK {version} installed (`dotnet --version`)
- [ ] Docker Desktop installed
- [ ] Azure CLI installed (`az --version`)
- [ ] Git configured with SSH keys
- [ ] IDE: Visual Studio 2022+ or JetBrains Rider
- [ ] Access to Azure subscription (request from team lead)

## Repository Setup

### Clone Repositories
```bash
# All service repos
git clone git@github.com:{company}/{domain}-command.git
git clone git@github.com:{company}/{domain}-query.git
git clone git@github.com:{company}/{domain}-processor.git
git clone git@github.com:{company}/{domain}-gateway.git
git clone git@github.com:{company}/{domain}-controlpanel.git
git clone git@github.com:{company}/shared-contracts.git
```

### Local Development
```bash
# Option 1: .NET Aspire (recommended)
cd {domain}-apphost
dotnet run

# Option 2: Manual
# Start SQL Server
docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=YourPass!123' -p 1433:1433 mcr.microsoft.com/mssql/server:2022-latest

# Run each service
cd {domain}-command && dotnet run
cd {domain}-query && dotnet run
cd {domain}-gateway && dotnet run
```

## Architecture Overview
See [Architecture Documentation](./architecture.md) for:
- Service topology diagram
- Event flow diagrams
- Database schema overview

### Key Concepts
1. **CQRS**: Commands and queries are separate services
2. **Event Sourcing**: State changes are events, not updates
3. **Outbox Pattern**: Reliable event publishing via outbox table
4. **Session Processing**: Service Bus sessions for ordered delivery

## Daily Development Workflow

### Adding a New Feature
1. Read the SDD lifecycle guide
2. Create feature branch: `feature/{feature-name}`
3. Implement command side first (events, aggregate, handler)
4. Implement query side (entity, event handler, query handler)
5. Add gateway endpoint
6. Write tests
7. Create PR and request review

### Running Tests
```bash
# Unit tests
dotnet test tests/{Domain}.Tests.Unit

# Integration tests
dotnet test tests/{Domain}.Tests.Integration

# All tests
dotnet test
```

### Common Tasks
- **Add new event type**: See event-design skill
- **Add query endpoint**: See query-handler skill
- **Add gateway endpoint**: See gateway-endpoint skill
- **Debug Service Bus**: Check Seq logs filtered by SessionId

## Key Contacts
| Role | Person | Responsibility |
|---|---|---|
| Tech Lead | {name} | Architecture decisions |
| DevOps | {name} | Deployment, infrastructure |
```

### Architecture Quick Reference

```markdown
## Service Communication Map

| From | To | Protocol | Purpose |
|---|---|---|---|
| Gateway | Command | gRPC | Send commands |
| Gateway | Query | gRPC | Read data |
| Command | Service Bus | AMQP | Publish events |
| Service Bus | Query | AMQP | Deliver events |
| Service Bus | Processor | AMQP | Deliver events |
| Processor | Query | gRPC | Cross-service sync |
| Control Panel | Gateway | REST | Admin operations |
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Outdated setup instructions | Verify and update quarterly |
| Missing prerequisites | List every required tool with version |
| No architecture overview | Include diagrams and key concepts |
| Tribal knowledge not documented | Write down common tasks and gotchas |

## Detect Existing Patterns

```bash
# Find existing onboarding docs
find . -name "*onboarding*" -o -name "*getting-started*" | grep -i ".md"

# Find README with setup instructions
find . -name "README.md" -maxdepth 2
```

## Adding to Existing Project

1. **Check for existing onboarding docs** before creating new ones
2. **Verify all setup steps** actually work on a clean machine
3. **Include architecture diagrams** from architecture-docs skill
4. **Reference ADRs** for key design decisions
5. **Update regularly** as tools and processes change
