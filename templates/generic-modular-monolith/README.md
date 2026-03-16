# {{ Company }}.{{ ProjectName }}

Modular Monolith project template.

## Structure

- **Host/** - Web host that discovers and registers all modules
- **Modules/** - Independent modules with their own Domain/Application/Infrastructure
- **Shared/** - Cross-module contracts, common models, integration events

## Getting Started

1. Copy the SampleModule to create new modules
2. Implement `IModuleInitializer` in each module
3. Define integration events in `Shared/Events/`
4. Use `INotification` for cross-module communication (not direct references)
5. Each module has its own DbContext and connection string

## Key Patterns

- **Module Isolation**: Each module has its own DbContext and data store
- **Integration Events**: Cross-module communication via MediatR INotification
- **Auto-Discovery**: Host discovers and registers modules at startup
- **Shared Contracts**: Common interfaces and models in Shared project
