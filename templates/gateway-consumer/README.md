# {{ Company }}.Gateways.{{ Domain }}.Consumers

Consumer-facing REST gateway with API versioning and Scalar documentation.

## Structure

- **Controllers/V1/** - Version 1 REST API controllers
- **Controllers/V2/** - Version 2 REST API controllers
- **Models/V1/** - V1 request/response models
- **Models/V2/** - V2 request/response models
- **Extensions/** - gRPC registration and JWT auth setup
- **Protos/** - Proto files from backing services (GrpcServices="Client")

## Getting Started

1. Add proto files from backing services in `Protos/`
2. Configure gRPC client registration in `GrpcRegistrationExtensions`
3. Create V1 controllers and models
4. Define consumer-facing auth policies in `AuthExtensions`
5. Access Scalar API docs at `/scalar/v1`

## Key Patterns

- **API Versioning**: URL-based versioning (v1, v2) with Asp.Versioning
- **REST-to-gRPC**: Controllers translate REST requests to gRPC calls
- **Consumer Auth**: Token-based JWT authorization
