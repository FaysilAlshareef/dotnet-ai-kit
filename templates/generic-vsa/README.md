# {{ Company }}.{{ ProjectName }}

Vertical Slice Architecture project template.

## Structure

- **Features/** - One file per operation (command + validator + handler + endpoint)
- **Common/** - Cross-cutting behaviors, models, and extensions
- **Data/** - EF Core DbContext and migrations

## Getting Started

1. Create feature files in `Features/` following the CreateOrder pattern
2. Register feature endpoints via `MapFeatureEndpoints()`
3. Run `dotnet ef migrations add Initial`
4. Access Scalar API docs at `/scalar/v1`

## Key Patterns

- **Feature per File**: Each operation is self-contained (command, validator, handler)
- **MediatR Pipeline**: Validation and logging behaviors
- **Minimal API**: Endpoints registered via IEndpointGroup discovery
