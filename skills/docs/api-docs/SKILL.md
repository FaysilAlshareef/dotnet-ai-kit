---
name: api-docs
description: >
  OpenAPI enrichment and Markdown API reference generation. Covers operation
  summaries, request/response examples, and gateway documentation patterns.
  Trigger: API documentation, OpenAPI, API reference, endpoint docs.
metadata:
  category: docs
  agent: docs-engineer
---

# API Docs — OpenAPI Enrichment & Reference

## Core Principles

- Enrich OpenAPI spec with summaries, descriptions, and examples
- Generate Markdown API reference from endpoint metadata
- Microservice mode: gateway API docs with gRPC-to-REST mapping notes
- Generic mode: standard REST API reference
- Detect missing documentation and suggest improvements

## Key Patterns

### OpenAPI Enrichment via Attributes

```csharp
[HttpGet]
[EndpointSummary("List orders with filtering and pagination")]
[EndpointDescription("Returns a paginated list of orders. Supports search by customer name and status filtering.")]
[ProducesResponseType(typeof(Paginated<OrderSummaryResponse>), 200)]
[ProducesResponseType(typeof(ProblemDetails), 400)]
public async Task<ActionResult<Paginated<OrderSummaryResponse>>> GetAll(
    [Description("Page number (1-based)")] [FromQuery] int page = 1,
    [Description("Items per page (max 100)")] [FromQuery] int pageSize = 20,
    [Description("Search by customer name")] [FromQuery] string? search = null)
```

### Document Transformer for Global Info

```csharp
options.AddDocumentTransformer((document, context, ct) =>
{
    document.Info = new OpenApiInfo
    {
        Title = "{Company} {Domain} API",
        Version = "v1",
        Description = """
            REST API for the {Domain} service.

            ## Authentication
            All endpoints require a Bearer JWT token.

            ## Pagination
            List endpoints return `Paginated<T>` with `items`, `totalCount`, `page`, `pageSize`.

            ## Error Handling
            Errors return RFC 9457 ProblemDetails.
            """,
    };
    return Task.CompletedTask;
});
```

### Markdown API Reference Template

```markdown
# {Domain} API Reference

## Authentication
All endpoints require a Bearer JWT token in the Authorization header.

## Endpoints

### Orders

#### List Orders
`GET /api/v1/orders`

| Parameter | Type | Required | Description |
|---|---|---|---|
| page | int | No | Page number (default: 1) |
| pageSize | int | No | Items per page (default: 20, max: 100) |
| search | string | No | Search by customer name |

**Response** `200 OK`
```json
{
  "items": [{ "id": "...", "customerName": "...", "total": 100.00 }],
  "totalCount": 42,
  "page": 1,
  "pageSize": 20
}
```

#### Create Order
`POST /api/v1/orders`

**Request Body**
```json
{
  "customerName": "string",
  "total": 100.00,
  "items": [{ "productId": "guid", "quantity": 1, "unitPrice": 50.00 }]
}
```

**Response** `201 Created`
```

### Scanning for Missing Docs

```bash
# Find endpoints missing summaries
grep -rn "HttpGet\|HttpPost\|HttpPut\|HttpDelete" --include="*.cs" src/ | \
  while read line; do
    file=$(echo $line | cut -d: -f1)
    grep -q "EndpointSummary\|Summary\|WithSummary" "$file" || echo "Missing docs: $line"
  done

# Find controllers missing ProducesResponseType
grep -rn "\[Http" --include="*.cs" src/Controllers/ | \
  while read line; do
    file=$(echo $line | cut -d: -f1)
    grep -q "ProducesResponseType" "$file" || echo "Missing response types: $line"
  done
```

## Anti-Patterns

| Anti-Pattern | Correct Approach |
|---|---|
| No endpoint descriptions | Add EndpointSummary and Description |
| Missing response type annotations | Add ProducesResponseType for each status |
| No error response documentation | Document ProblemDetails responses |
| Outdated API reference | Generate from OpenAPI spec, not manually |

## Detect Existing Patterns

```bash
# Find OpenAPI configuration
grep -r "AddOpenApi\|MapOpenApi" --include="*.cs" src/

# Find endpoint documentation
grep -r "EndpointSummary\|WithSummary\|ProducesResponseType" --include="*.cs" src/

# Find existing API docs
find . -name "*api*" -path "*/docs/*" -name "*.md"
```

## Adding to Existing Project

1. **Scan existing endpoints** for missing OpenAPI metadata
2. **Add summaries and descriptions** to undocumented endpoints
3. **Add ProducesResponseType** for all possible status codes
4. **Generate Markdown reference** from OpenAPI spec
5. **Keep docs in sync** by generating from code, not writing manually
