---
name: github-actions
description: >
  GitHub Actions CI/CD workflows for .NET microservices. Covers build-test-deploy
  pipelines, Azure OIDC auth, ACR image push, and AKS deployment.
  Trigger: GitHub Actions, CI/CD, workflow, pipeline, deployment.
metadata:
  category: devops
  agent: devops-engineer
  when-to-use: "When creating or modifying GitHub Actions CI/CD workflows for .NET projects"
---

# GitHub Actions — CI/CD Pipelines

## Core Principles

- Two-job pipeline: `build-and-push` + `deploy`
- Azure OIDC authentication (no stored credentials)
- Build Docker image and push to Azure Container Registry (ACR)
- Token replacement in K8s manifests during deploy
- Environment secrets for connection strings and credentials
- PR triggers run build + test only; push to main triggers full deploy

## Key Patterns

### Build, Test, Deploy Workflow

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read

env:
  ACR_NAME: {company}acr
  IMAGE_NAME: {domain}-command

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '{version}.0.x'

      - name: Restore
        run: dotnet restore

      - name: Build
        run: dotnet build --no-restore -c Release

      - name: Test
        run: dotnet test --no-build -c Release --logger trx

  build-and-push:
    needs: build-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Build and Push to ACR
        run: |
          az acr build \
            --registry ${{ env.ACR_NAME }} \
            --image ${{ env.IMAGE_NAME }}:${{ github.sha }} \
            --image ${{ env.IMAGE_NAME }}:latest \
            .

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Get AKS Credentials
        run: |
          az aks get-credentials \
            --resource-group ${{ secrets.AKS_RESOURCE_GROUP }} \
            --name ${{ secrets.AKS_CLUSTER_NAME }}

      - name: Replace Tokens in Manifest
        run: |
          sed -i 's|#{IMAGE_TAG}#|${{ github.sha }}|g' deploy/prod-manifest.yaml
          sed -i 's|#{ACR_NAME}#|${{ env.ACR_NAME }}|g' deploy/prod-manifest.yaml
          sed -i 's|#{REPLICAS}#|2|g' deploy/prod-manifest.yaml
          sed -i 's|#{DB_CONNECTION_STRING}#|${{ secrets.DB_CONNECTION }}|g' deploy/prod-manifest.yaml

      - name: Deploy to AKS
        uses: azure/k8s-deploy@v5
        with:
          manifests: deploy/prod-manifest.yaml
          namespace: {company}-prod
```

### PR-Only Workflow (Build + Test)

```yaml
name: PR Checks

on:
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '{version}.0.x'
      - run: dotnet restore
      - run: dotnet build --no-restore -c Release
      - run: dotnet test --no-build -c Release
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Stored Azure credentials | Use OIDC with `id-token: write` permission |
| Deploy on PR | Only deploy on push to main |
| Secrets in workflow file | Use GitHub environment secrets |
| Missing test step | Always test before deploying |
| No token replacement | Use sed or dedicated token replacement action |

## Detect Existing Patterns

```bash
# Find GitHub Actions workflows
find .github/workflows -name "*.yml" -o -name "*.yaml"

# Find Azure login patterns
grep -r "azure/login" --include="*.yml" .github/

# Find ACR build
grep -r "az acr build" --include="*.yml" .github/
```

## Adding to Existing Project

1. **Follow existing workflow structure** — two-job vs single-job pattern
2. **Use existing Azure OIDC credentials** (same app registration)
3. **Match ACR name and AKS cluster** from existing workflows
4. **Add environment secrets** for new service connection strings
5. **Token replacement** must match placeholders in K8s manifests
