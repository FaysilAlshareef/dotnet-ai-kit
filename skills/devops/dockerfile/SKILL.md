---
name: dockerfile
description: >
  Use when writing or optimizing Dockerfiles for .NET applications.
metadata:
  category: devops
  agent: devops-engineer
  when-to-use: "When creating or modifying Dockerfiles for .NET application containers"
---

# Dockerfile — Multi-Stage .NET Builds

## Core Principles

- Multi-stage build: `base` -> `build` -> `publish` -> `final`
- Copy `.csproj` files first for layer caching (restore step)
- Non-root user for security (`USER app` or numeric UID)
- Expose ports 8080 (HTTP) and 8081 (HTTPS/gRPC)
- Health check endpoint for container orchestration
- Version-aware base images: `mcr.microsoft.com/dotnet/aspnet:{version}`

## Key Patterns

### Standard ASP.NET Dockerfile

```dockerfile
# Base runtime image
FROM mcr.microsoft.com/dotnet/aspnet:{version}-alpine AS base
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

# Build stage
FROM mcr.microsoft.com/dotnet/sdk:{version}-alpine AS build
WORKDIR /src

# Copy csproj files first for layer caching
COPY ["src/{Company}.{Domain}.Command/{Company}.{Domain}.Command.csproj", "src/{Company}.{Domain}.Command/"]
COPY ["src/{Company}.{Domain}.Shared/{Company}.{Domain}.Shared.csproj", "src/{Company}.{Domain}.Shared/"]
COPY ["Directory.Build.props", "."]
COPY ["Directory.Packages.props", "."]

RUN dotnet restore "src/{Company}.{Domain}.Command/{Company}.{Domain}.Command.csproj"

# Copy everything and build
COPY . .
WORKDIR "/src/src/{Company}.{Domain}.Command"
RUN dotnet build -c Release -o /app/build

# Publish stage
FROM build AS publish
RUN dotnet publish -c Release -o /app/publish /p:UseAppHost=false

# Final stage
FROM base AS final
WORKDIR /app

# Non-root user
USER app

COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "{Company}.{Domain}.Command.dll"]
```

### With Health Check

```dockerfile
FROM base AS final
WORKDIR /app
USER app
COPY --from=publish /app/publish .

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

ENTRYPOINT ["dotnet", "{Company}.{Domain}.Command.dll"]
```

### Processor Service (No HTTP)

```dockerfile
FROM mcr.microsoft.com/dotnet/runtime:{version}-alpine AS base
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:{version}-alpine AS build
WORKDIR /src
# ... same build pattern ...

FROM base AS final
WORKDIR /app
USER app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "{Company}.{Domain}.Processor.dll"]
```

### .dockerignore

```
**/.git
**/.vs
**/bin
**/obj
**/node_modules
**/.env
**/Dockerfile*
**/.dockerignore
**/docker-compose*
**/*.md
**/tests
```

## Version-Aware Image Tags

| .NET Version | SDK Image | Runtime Image |
|---|---|---|
| .NET 8 | `sdk:8.0-alpine` | `aspnet:8.0-alpine` |
| .NET 9 | `sdk:9.0-alpine` | `aspnet:9.0-alpine` |
| .NET 10 | `sdk:10.0-alpine` | `aspnet:10.0-alpine` |

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| Single-stage build (bloated image) | Multi-stage: separate build and runtime |
| Copying all files before restore | Copy csproj first for layer caching |
| Running as root | Use `USER app` or numeric UID |
| Missing .dockerignore | Exclude bin, obj, .git, tests |
| Hardcoded .NET version | Match project TargetFramework |

## Detect Existing Patterns

```bash
# Find existing Dockerfiles
find . -name "Dockerfile*" -type f

# Check .NET version
grep -r "TargetFramework" --include="*.csproj" src/ | head -5

# Find .dockerignore
find . -name ".dockerignore" -type f
```

## Adding to Existing Project

1. **Match the .NET version** from `Directory.Build.props` or `.csproj`
2. **Follow existing Dockerfile structure** if one exists
3. **Use Alpine images** for smaller container size
4. **Add health check** if the service exposes HTTP endpoints
5. **Update .dockerignore** to exclude new test or doc directories
