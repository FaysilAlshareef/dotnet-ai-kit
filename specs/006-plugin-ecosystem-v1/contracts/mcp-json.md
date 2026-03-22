# Contract: .mcp.json

**Location**: `.mcp.json` (repository root)

## Schema

```json
{
  "mcpServers": {
    "csharp-ls": {
      "command": "csharp-ls",
      "args": ["--solution", "."],
      "transport": "stdio"
    }
  }
}
```

## Behavior

- If `csharp-ls` is not found on PATH, the server entry is silently skipped
- No startup errors or warnings that block plugin loading
- When available, provides: go-to-definition, find references, diagnostics, hover info
- Install instruction: `dotnet tool install -g csharp-ls`
