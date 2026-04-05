---
name: kubernetes
description: >
  Kubernetes manifests for .NET microservices. Covers Deployment, Service, ConfigMap,
  Secret, health probes, and token placeholders for CI/CD pipelines.
  Trigger: Kubernetes, K8s, deployment, service, manifest, pod.
metadata:
  category: devops
  agent: devops-engineer
  when-to-use: "When creating or modifying Kubernetes deployment manifests or service configurations"
---

# Kubernetes — Deployment Manifests

## Core Principles

- Per-environment manifests: `dev-manifest.yaml`, `staging-manifest.yaml`, `prod-manifest.yaml`
- Token placeholders (`#{TOKEN}#`) replaced during CI/CD deployment
- Health check probes: `/health/ready` (readiness), `/health/live` (liveness)
- RollingUpdate strategy with `maxUnavailable: 0, maxSurge: 1`
- Environment variables from Secrets and ConfigMaps
- Service Bus topics/subscriptions configured via environment

## Key Patterns

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {domain}-command
  namespace: {company}-{env}
spec:
  replicas: #{REPLICAS}#
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: {domain}-command
  template:
    metadata:
      labels:
        app: {domain}-command
    spec:
      containers:
        - name: {domain}-command
          image: #{ACR_NAME}#.azurecr.io/{domain}-command:#{IMAGE_TAG}#
          ports:
            - containerPort: 8080
            - containerPort: 8081
          env:
            - name: ASPNETCORE_ENVIRONMENT
              value: "#{ENVIRONMENT}#"
            - name: ConnectionStrings__DefaultConnection
              valueFrom:
                secretKeyRef:
                  name: {domain}-secrets
                  key: db-connection-string
            - name: ServiceBus__ConnectionString
              valueFrom:
                secretKeyRef:
                  name: {domain}-secrets
                  key: servicebus-connection
            - name: ExternalServices__QueryServiceUrl
              value: "http://{domain}-query:8081"
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 15
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 30
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {domain}-command
  namespace: {company}-{env}
spec:
  selector:
    app: {domain}-command
  ports:
    - name: http
      port: 8080
      targetPort: 8080
    - name: grpc
      port: 8081
      targetPort: 8081
  type: ClusterIP
```

### Secret (Template)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {domain}-secrets
  namespace: {company}-{env}
type: Opaque
stringData:
  db-connection-string: "#{DB_CONNECTION_STRING}#"
  servicebus-connection: "#{SERVICEBUS_CONNECTION}#"
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {domain}-config
  namespace: {company}-{env}
data:
  Serilog__SeqUrl: "http://seq:5341"
  Serilog__WriteToConsole: "true"
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Secrets in ConfigMap | Use Secret for sensitive data |
| No resource limits | Set requests and limits for stability |
| Missing health probes | Add readiness and liveness probes |
| Hardcoded image tags | Use token placeholders for CI/CD |
| maxUnavailable > 0 | Zero downtime: maxUnavailable=0, maxSurge=1 |

## Detect Existing Patterns

```bash
# Find K8s manifests
find . -name "*-manifest.yaml" -o -name "*.k8s.yaml" | head -10

# Find token placeholders
grep -r "#{.*}#" --include="*.yaml" .

# Find health check endpoints
grep -r "/health" --include="*.cs" src/
```

## Adding to Existing Project

1. **Follow existing manifest naming** — `{env}-manifest.yaml`
2. **Match namespace convention** — `{company}-{env}`
3. **Use existing secret names** for shared resources
4. **Add inter-service URLs** via environment variables
5. **Configure health probes** matching the application health endpoints
