# {{ Company }}.ControlPanel.{{ Domain }}

Blazor WASM control panel module with MudBlazor components.

## Structure

- **Pages/** - Blazor page components
- **Components/** - Reusable Blazor components and dialogs
- **Gateways/** - HTTP gateway facade with ResponseResult pattern
- **Models/** - Filters, requests, and response models
- **Services/** - Menu provider and registration

## Getting Started

1. Configure `Gateway.cs` with management classes for each domain area
2. Create pages in `Pages/`
3. Define filter models in `Models/Filters/`
4. Add request/response models matching the gateway API
5. Configure `MenuItemsProvider` with navigation items
6. Set `GatewayBaseUrl` in configuration

## Key Patterns

- **ResponseResult**: Success/Failure pattern for HTTP responses
- **MudBlazor**: Material Design components for UI
- **Gateway Facade**: Typed HTTP client for REST API communication
