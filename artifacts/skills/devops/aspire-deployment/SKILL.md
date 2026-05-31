---
name: aspire-deployment
description: "Publishes a .NET Aspire 13.1 app graph with aspire deploy, configures publishers and container-registry resources, and promotes to Azure Container Apps via azd. Use when turning a running AppHost into deployable container artifacts and shipping them to a cloud target. Do NOT use for adding integration resources or WithReference wiring (use aspire-integrations), local orchestration (use aspire-orchestration), or hand-written Kubernetes manifests (use kubernetes)."
metadata:
  category: "devops"
  agent: "aspire-architect"
---
# Aspire Deployment

The same AppHost that orchestrates locally produces the deployment manifest. `aspire deploy` runs the registered publisher to build images, push them to a registry, and apply infrastructure to the target environment.

## Conventions
- Model the registry as a resource in the AppHost and attach it so images publish to the right place: `builder.AddDockerfile(...)` / `builder.AddContainer(...)` resources inherit the configured registry.
- Pick a publisher per target. **Azure Container Apps (ACA)** via `azd` is the default cloud path; keep it opt-in — local dev never needs a publisher.
- Drive cloud deploys with `azd`: `azd init` (detects the AppHost), `azd up` (provision + deploy), `azd deploy` (code-only redeploy). `azd` reads the Aspire manifest, so resources map to ACA apps automatically.
- Mark only the public entry point with `.WithExternalHttpEndpoints()`; everything else stays internal to the environment.
- Keep secrets out of the manifest — use `builder.AddParameter("name", secret: true)` and supply values via `azd env set` or the platform's secret store.
- Generate the manifest for inspection/CI with `aspire publish` (or `dotnet run --project AppHost -- --publisher manifest`) before deploying.

## Example
```csharp
// AppHost/Program.cs
var builder = DistributedApplication.CreateBuilder(args);

var dbPassword = builder.AddParameter("db-password", secret: true);
var db = builder.AddPostgres("pg", password: dbPassword).AddDatabase("orders-db");

builder.AddProject<Projects.Orders_Api>("orders-api")
    .WithReference(db)
    .WithExternalHttpEndpoints();   // only the gateway/API is public

builder.Build().Run();
```
```bash
# Provision Azure resources + deploy the whole graph to Azure Container Apps
azd init        # detects the AppHost and generates azure.yaml
azd up          # build images, push to registry, provision ACA, deploy
azd env set DB_PASSWORD <value>   # supply the secret parameter
```

## Anti-Patterns
- Marking internal services with `WithExternalHttpEndpoints()` (over-exposes the surface).
- Baking secrets into the manifest instead of `AddParameter(secret: true)`.
- Hand-writing K8s/ACA YAML that duplicates what the publisher emits.
- Building/pushing images manually instead of letting `aspire deploy` / `azd` do it.

## References
- https://learn.microsoft.com/en-us/dotnet/aspire/deployment/overview
- https://learn.microsoft.com/en-us/dotnet/aspire/deployment/azure/aca-deployment-azd-in-depth
