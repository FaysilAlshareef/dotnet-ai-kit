# {{ Company }}.Gateways.{{ Domain }}.Management

Management REST gateway with Scalar API documentation.

## Structure

- **Controllers/** - REST API controllers calling backing gRPC services
- **Models/** - Request/response models for the REST API
- **GrpcClients/** - Typed gRPC client wrappers
- **Extensions/** - gRPC registration and JWT auth setup
- **Protos/** - Proto files from backing services (GrpcServices="Client")

## Getting Started

1. Add proto files from backing services in `Protos/`
2. Configure gRPC client registration in `GrpcRegistrationExtensions`
3. Define authorization policies in `AuthExtensions`
4. Create controllers for each domain resource
5. Access Scalar API docs at `/scalar/v1`

## Key Patterns

- **REST-to-gRPC**: Controllers translate REST requests to gRPC calls
- **JWT Auth**: Policy-based authorization for management roles
- **Scalar Docs**: Interactive API documentation with BluePlanet theme
