---
description: "Add a REST endpoint to a gateway project with gRPC client integration"
---

# Add Endpoint

Create a REST endpoint in a gateway project with controller action, gRPC client call, request/response models, and mapping extensions.

## Usage

```
/dotnet-ai.add-endpoint $ARGUMENTS
```

**Examples:**
- `GetOrders` -- Add GET endpoint (HTTP method inferred from name)
- `"POST /api/v1/orders"` -- Explicit HTTP method and path
- `Order --operations "list,get,create,update,delete"` -- Full CRUD endpoints
- `Order --preview` -- Show code without writing
- `Order --dry-run` -- Show file list only
- `Order --verbose` -- Show detection details

## Flags

| Flag | Description |
|------|-------------|
| `--operations "op1,op2,..."` | Which CRUD operations to generate (default: inferred) |
| `--version v{N}` | API version (default: detected from existing endpoints) |
| `--preview` | Display generated code without writing to disk |
| `--dry-run` | List files that would be created/modified |
| `--verbose` | Show detection steps and pattern matching details |

## Pre-Generation

1. **Detect project type** -- scan for gateway markers: REST controllers + `AddGrpcClient<T>`.
   - If not a gateway project: report error and stop.
2. **Detect gateway variant** -- management gateway vs consumer gateway:
   - Management: typically has admin-level endpoints, broader auth policies
   - Consumer: public-facing, more restrictive auth
3. **Detect .NET version** -- read `<TargetFramework>`.
4. **Learn patterns from existing controllers:**
   - API versioning scheme (`v1`, `v2`, etc.)
   - Authorization policies (`[Authorize(Policy = "...")]`)
   - Response format (`ActionResult<T>`, `Paginated<T>`, result wrappers)
   - Controller base class, route conventions
   - Existing gRPC client registrations
5. **Load config** -- read `.dotnet-ai-kit/config.yml`.
6. **Check uniqueness** -- ensure no existing controller/action conflicts.

## Load Specialist Agent

Read `agents/gateway-architect.md` for gateway patterns. Also read `agents/api-designer.md` for REST API design. Load all skills listed in each agent's Skills Loaded section.

## Skills to Read

- `skills/microservice/gateway/gateway-endpoint` -- controller structure, action methods
- `skills/microservice/gateway/endpoint-registration` -- gRPC client registration, DI setup

## Generation Flow

Parse `$ARGUMENTS`: if input looks like `"METHOD /path"`, extract method and route. If single name, infer method from prefix (`Get` = GET, `Create`/`Add` = POST, `Update` = PUT, `Delete` = DELETE).

### Step 1: Generate Controller
- Path: `Controllers/V{N}/{Name}Controller.cs`
- `[ApiController]`, `[Route("api/v{N}/[controller]")]`
- `[Authorize(Policy = "...")]` matching existing patterns
- Inject gRPC client via constructor
- Generate action methods based on `--operations` or inferred operation:
  - List: `[HttpGet]` returning `Paginated<{Name}Response>`
  - Get: `[HttpGet("{id}")]` returning `{Name}Response`
  - Create: `[HttpPost]` accepting `Create{Name}Request`
  - Update: `[HttpPut("{id}")]` accepting `Update{Name}Request`
  - Delete: `[HttpDelete("{id}")]`

### Step 2: Generate Request/Response Models
- Path: `Models/Requests/Create{Name}Request.cs`
- Path: `Models/Requests/Update{Name}Request.cs`
- Path: `Models/Responses/{Name}Response.cs`
- Match existing model patterns (records vs classes, validation attributes)

### Step 3: Generate Mapping Extensions
- Path: `Extensions/{Name}MappingExtensions.cs`
- Request -> gRPC message mappings
- gRPC response -> Response DTO mappings
- Follow existing extension method patterns

### Step 4: Register gRPC Client
- Modify `Infra/GrpcRegistration.cs` or equivalent to add new gRPC client
- Add service URL to `ServicesUrlsOptions` if needed

## Post-Generation

1. **Run `dotnet build`** -- verify compilation.
2. **Report generated files.**
3. **Suggest next steps:**
   ```
   Endpoint '{Name}' added to gateway.
   Next: Test with: GET /api/v{N}/{name}s
   ```

## Preview / Dry-Run Behavior

- `--preview`: Show all generated code with file path headers. No writes.
- `--dry-run`: List files only. No code output, no writes.
