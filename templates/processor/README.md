# {{ Company }}.{{ Domain }}.Processor

Background event processor microservice template.

## Structure

- **Domain/** - Event definitions for processing
- **Application/** - Event handlers via MediatR
- **Infra/** - Service Bus listeners, gRPC clients for external services
- **Host/** - Worker host with Serilog

## Getting Started

1. Create Service Bus listeners in `Infra/Listeners/`
2. Add event handlers in `Application/Handlers/`
3. Register gRPC clients for external services in `InfraServiceExtensions`
4. Configure `appsettings.json` with Service Bus and external service URLs

## Key Patterns

- **Session Processing**: ServiceBusSessionProcessor for ordered message handling
- **Event Routing**: Switch-based routing by event type (Subject header)
- **Cross-Service Calls**: gRPC clients for calling command/query services
