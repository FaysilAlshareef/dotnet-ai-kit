---
alwaysApply: true
description: Rules for working with existing codebases - detect, respect, extend.
---

# Existing Project Rules

Core principle: Detect before generate. Respect before change. Check docs before using.

## Detection -- Always Scan First

Before generating any code, scan the project for:
- .NET version (`<TargetFramework>` in .csproj)
- Architecture pattern (folder structure, layer names)
- Naming conventions (existing classes, namespaces)
- NuGet packages (what is already used)
- Existing patterns (DI registration style, error handling, logging)

## Respect What Exists

- Use the same .NET version as the project
- Follow the same naming conventions, even if different from defaults
- Use the same packages -- do not introduce competing libraries
- Match the same code style (formatting, spacing, patterns)
- Do not change the project structure

## Extend, Don't Refactor

- Add new files following existing patterns
- Register new services the same way existing ones are registered
- Use the same base classes and interfaces the project already uses
- Match the same test structure and patterns

## Never During Implementation

- Never change .NET version
- Never refactor existing code while adding features
- Never introduce new architectural patterns alongside existing ones
- Never switch libraries (e.g., do not add Dapper if the project uses EF Core)
- Never reorganize folder structure
- Never guess package/framework APIs -- always check official documentation first
- Never deploy -- AI must never deploy to any environment
- Rollback strategies are documented but executed by the deployment pipeline, not by AI

## When No Project Exists

- Use defaults from config (company name, naming pattern)
- Use latest stable .NET version -- currently .NET 10 (or as configured)
- Follow the architecture recommended by the plan
- Apply full conventions from all other rules
