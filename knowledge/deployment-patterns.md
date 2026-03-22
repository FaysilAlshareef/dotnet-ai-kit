# Deployment Patterns

Docker multi-stage builds, Kubernetes manifests, GitHub Actions CI/CD, and environment configuration for .NET microservices.

---

## Docker Multi-Stage Build

### Standard .NET Dockerfile

```dockerfile
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy solution and project files first (layer caching)
COPY *.sln .
COPY Directory.Build.props .
COPY Directory.Packages.props .
COPY src/{Company}.{Domain}.Commands.Api/*.csproj src/{Company}.{Domain}.Commands.Api/
COPY src/{Company}.{Domain}.Commands.Domain/*.csproj src/{Company}.{Domain}.Commands.Domain/
COPY src/{Company}.{Domain}.Commands.Application/*.csproj src/{Company}.{Domain}.Commands.Application/
COPY src/{Company}.{Domain}.Commands.Infrastructure/*.csproj src/{Company}.{Domain}.Commands.Infrastructure/
RUN dotnet restore

# Copy everything else and build
COPY . .
RUN dotnet publish src/{Company}.{Domain}.Commands.Api \
    -c Release \
    -o /app/publish \
    --no-restore

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

COPY --from=build /app/publish .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health/live || exit 1

EXPOSE 8080
ENTRYPOINT ["dotnet", "{Company}.{Domain}.Commands.Api.dll"]
```

### .dockerignore

```
**/bin/
**/obj/
**/node_modules/
**/.git/
**/.vs/
**/Dockerfile*
**/.dockerignore
**/docker-compose*
*.md
.editorconfig
.gitignore
```

### Build and Tag

```bash
docker build -t {company}-{domain}-commands:latest .
docker tag {company}-{domain}-commands:latest {registry}.azurecr.io/{company}-{domain}-commands:#{IMAGE_TAG}#
```

---

## Kubernetes Manifests

### Manifest Structure

```
k8s/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── hpa.yaml
│   └── configmap.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patches/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── patches/
    └── prod/
        ├── kustomization.yaml
        └── patches/
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {company}-{domain}-commands
  namespace: {company}-{domain}
  labels:
    app: {company}-{domain}-commands
    version: "#{IMAGE_TAG}#"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {company}-{domain}-commands
  template:
    metadata:
      labels:
        app: {company}-{domain}-commands
    spec:
      serviceAccountName: {company}-{domain}-commands
      containers:
        - name: api
          image: #{ACR_REGISTRY}#/{company}-{domain}-commands:#{IMAGE_TAG}#
          ports:
            - containerPort: 8080
              name: http
            - containerPort: 8081
              name: grpc
          env:
            - name: ASPNETCORE_ENVIRONMENT
              value: "#{ENVIRONMENT}#"
            - name: ConnectionStrings__Database
              valueFrom:
                secretKeyRef:
                  name: {company}-{domain}-commands-secrets
                  key: database-connection
            - name: ServiceBus__ConnectionString
              valueFrom:
                secretKeyRef:
                  name: {company}-{domain}-commands-secrets
                  key: servicebus-connection
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
          startupProbe:
            httpGet:
              path: /health/live
              port: 8080
            failureThreshold: 30
            periodSeconds: 10
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {company}-{domain}-commands
  namespace: {company}-{domain}
spec:
  selector:
    app: {company}-{domain}-commands
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: grpc
      port: 8081
      targetPort: 8081
  type: ClusterIP
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {company}-{domain}-commands-hpa
  namespace: {company}-{domain}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {company}-{domain}-commands
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## Health Checks

Implement readiness and liveness endpoints:

```csharp
// Program.cs
builder.Services.AddHealthChecks()
    .AddSqlServer(
        connectionString,
        name: "database",
        tags: ["ready"])
    .AddAzureServiceBusTopic(
        serviceBusConnectionString,
        topicName: "{company}-order-commands",
        name: "servicebus",
        tags: ["ready"]);

app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false // Just checks the app is running
});

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready")
});
```

---

## GitHub Actions CI/CD

### Build and Test Workflow

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read

env:
  DOTNET_VERSION: "10.0.x"
  ACR_REGISTRY: "{company}acr.azurecr.io"
  IMAGE_NAME: "{company}-{domain}-commands"

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: ${{ env.DOTNET_VERSION }}

      - name: Restore
        run: dotnet restore

      - name: Build
        run: dotnet build --no-restore -c Release

      - name: Unit Tests
        run: dotnet test tests/*.UnitTests --no-build -c Release --logger "trx;LogFileName=unit-tests.trx"

      - name: Integration Tests
        run: dotnet test tests/*.IntegrationTests --no-build -c Release --logger "trx;LogFileName=integration-tests.trx"

      - name: Publish Test Results
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Test Results
          path: "**/*.trx"
          reporter: dotnet-trx

  docker-push:
    needs: build-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: ACR Login
        run: az acr login --name {company}acr

      - name: Build and Push
        run: |
          IMAGE_TAG=${{ github.sha }}
          docker build -t ${{ env.ACR_REGISTRY }}/${{ env.IMAGE_NAME }}:${IMAGE_TAG} .
          docker build -t ${{ env.ACR_REGISTRY }}/${{ env.IMAGE_NAME }}:latest .
          docker push ${{ env.ACR_REGISTRY }}/${{ env.IMAGE_NAME }}:${IMAGE_TAG}
          docker push ${{ env.ACR_REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy-dev:
    needs: docker-push
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Get AKS Credentials
        run: az aks get-credentials --resource-group {company}-rg --name {company}-aks

      - name: Replace Tokens in Manifests
        run: |
          sed -i "s|#{IMAGE_TAG}#|${{ github.sha }}|g" k8s/overlays/dev/*.yaml
          sed -i "s|#{ACR_REGISTRY}#|${{ env.ACR_REGISTRY }}|g" k8s/overlays/dev/*.yaml
          sed -i "s|#{ENVIRONMENT}#|Development|g" k8s/overlays/dev/*.yaml

      - name: Deploy to AKS
        run: kubectl apply -k k8s/overlays/dev/

      - name: Wait for Rollout
        run: kubectl rollout status deployment/{company}-{domain}-commands -n {company}-{domain} --timeout=300s

  deploy-prod:
    needs: deploy-dev
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: prod
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID_PROD }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID_PROD }}

      - name: Get AKS Credentials
        run: az aks get-credentials --resource-group {company}-prod-rg --name {company}-prod-aks

      - name: Replace Tokens
        run: |
          sed -i "s|#{IMAGE_TAG}#|${{ github.sha }}|g" k8s/overlays/prod/*.yaml
          sed -i "s|#{ACR_REGISTRY}#|${{ env.ACR_REGISTRY }}|g" k8s/overlays/prod/*.yaml
          sed -i "s|#{ENVIRONMENT}#|Production|g" k8s/overlays/prod/*.yaml

      - name: Deploy to AKS
        run: kubectl apply -k k8s/overlays/prod/

      - name: Wait for Rollout
        run: kubectl rollout status deployment/{company}-{domain}-commands -n {company}-{domain} --timeout=300s
```

---

## Environment Configuration

### appsettings per Environment

```
appsettings.json                    # Base settings
appsettings.Development.json        # Local dev overrides
appsettings.Testing.json            # Integration test overrides
appsettings.Staging.json            # Staging overrides (if not using K8s env vars)
appsettings.Production.json         # Production overrides (minimal — secrets via K8s)
```

### Configuration Priority (highest to lowest)

1. Environment variables (K8s ConfigMap/Secrets)
2. `appsettings.{Environment}.json`
3. `appsettings.json`
4. User secrets (Development only)

### Token Replacement Pattern

Use `#{TOKEN}#` placeholders in manifests, replaced during CI/CD:

```yaml
env:
  - name: ConnectionStrings__Database
    value: "#{DB_CONNECTION}#"
  - name: ServiceBus__TopicName
    value: "#{TOPIC_NAME}#"
```

---

## Secret Management

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {company}-{domain}-commands-secrets
  namespace: {company}-{domain}
type: Opaque
data:
  database-connection: <base64-encoded>
  servicebus-connection: <base64-encoded>
```

### Azure Key Vault Integration

```csharp
builder.Configuration.AddAzureKeyVault(
    new Uri($"https://{company}-{domain}-kv.vault.azure.net/"),
    new DefaultAzureCredential());
```

---

## Related Documents

- `knowledge/testing-patterns.md` — Tests integrated into CI
- `knowledge/service-bus-patterns.md` — Service Bus configuration
- `knowledge/documentation-standards.md` — ADR and docs standards
