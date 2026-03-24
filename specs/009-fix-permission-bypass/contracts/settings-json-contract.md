# Contract: Claude Code Settings JSON

**Feature**: 009-fix-permission-bypass
**Format**: JSON (`.claude/settings.json`)

## Schema

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "bypassPermissions",
    "allow": [
      "Bash(dotnet build *)",
      "Bash(git status)",
      "Bash(git status *)"
    ],
    "deny": [],
    "ask": []
  }
}
```

## Tool-Managed Fields

The tool writes to these fields:
- `permissions.allow`: Adds/removes entries from the permission template
- `permissions.defaultMode`: Sets to `"bypassPermissions"` for full level; removes key for minimal/standard

## Preserved Fields (never modified)

- `permissions.deny`: User-defined deny rules
- `permissions.ask`: User-defined ask rules
- `$schema`: Preserved if present
- All other top-level keys (`hooks`, `env`, `autoMode`, etc.)

## Permission Entry Format

```
Bash(<command>)           # Exact command match (no args)
Bash(<command> *)         # Command with any arguments
WebSearch                 # Tool-level permission
WebFetch(domain:<host>)   # Domain-scoped web fetch
Edit(<glob-pattern>)      # File edit by pattern
```

## Example: Full Level Output

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "bypassPermissions",
    "allow": [
      "Bash(cd *)",
      "Bash(ls)",
      "Bash(ls *)",
      "Bash(dotnet build *)",
      "Bash(dotnet test *)",
      "Bash(git *)",
      "Bash(npm *)",
      "Bash(docker *)",
      "WebSearch",
      "WebFetch(domain:github.com)"
    ]
  }
}
```

## Example: Standard Level Output

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(cd *)",
      "Bash(ls)",
      "Bash(ls *)",
      "Bash(dotnet build *)",
      "Bash(dotnet test *)",
      "Bash(git status)",
      "Bash(git status *)",
      "Bash(git add *)",
      "Bash(git commit *)"
    ]
  }
}
```

Note: Standard level does NOT set `defaultMode` — Claude Code uses its default prompting behavior with the allow-list as pre-approved exceptions.
