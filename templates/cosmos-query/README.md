# {{ Company }}.{{ Domain }}.Queries (Cosmos DB)

Cosmos DB query microservice template.

## Structure

- **Domain/** - IContainerDocument implementations, events
- **Application/** - Event handlers and query handlers via MediatR
- **Infra/** - Cosmos repository, unit of work, Service Bus listeners
- **Grpc/** - gRPC host with interceptors

## Getting Started

1. Define documents implementing IContainerDocument in `Domain/Documents/`
2. Configure partition key strategy per document type
3. Create event handlers in `Application/EventHandlers/`
4. Create a Service Bus listener in `Infra/Listeners/`
5. Add proto definitions in `Grpc/Protos/`

## Key Patterns

- **Hierarchical Partition Keys**: 3-level partition key for Cosmos DB
- **Transactional Batch**: Multiple operations committed atomically
- **ETag Concurrency**: Optimistic concurrency via ETag checking
