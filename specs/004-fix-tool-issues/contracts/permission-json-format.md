# Contract: Permission JSON Format

**Type**: Configuration file contract
**Consumers**: Claude Code settings.json, AI tool permission systems

## Claude Code Permission Format (Official)

Permission files are installed into `.claude/settings.json` under the `permissions` object.

### Correct Format (space syntax, not colon)

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(dotnet build *)",
      "Bash(dotnet test *)",
      "Bash(dotnet restore *)",
      "Bash(dotnet format *)",
      "Bash(dotnet new *)",
      "Bash(git checkout *)",
      "Bash(git branch *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git push *)",
      "Bash(git status *)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git stash *)",
      "Bash(gh pr *)",
      "Bash(gh repo *)",
      "Bash(gh issue *)",
      "Bash(ls *)",
      "Bash(dir *)",
      "Bash(tree *)",
      "Bash(mkdir *)",
      "Bash(cat *)",
      "Bash(cd *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  }
}
```

### Key Rules (from Claude Code docs)

- **Syntax**: `Tool(specifier)` where specifier uses `*` as wildcard
- **Bash pattern**: `Bash(npm run *)` matches commands starting with `npm run`
- **Evaluation order**: deny first → ask → allow (first match wins)
- **WRONG**: `Bash(dotnet build:*)` — colon is treated as literal character, won't match
- **RIGHT**: `Bash(dotnet build *)` — space separator, `*` matches the rest
- **`$schema`**: Include for editor autocomplete and validation in VS Code/Cursor

### Compound Command Handling

Claude Code matches the FULL command string against patterns. For `cd path && gh pr create`:
- Pattern `Bash(cd *)` matches because the string starts with `cd`
- Pattern `Bash(gh pr *)` does NOT match because the string starts with `cd`

**Solution**: AI guidance rules instruct assistants to use sequential tool calls instead of `&&` chains. Each command gets its own `Bash()` call so each pattern matches independently.

### Pre-flight Validation

When permissions are installed, the tool checks that referenced commands exist:

```
Validating tool availability:
  dotnet ... found (v8.0.300)
  git    ... found (v2.43.0)
  gh     ... not found
         Install: https://cli.github.com
         Or: winget install GitHub.cli
```

Warn but do not block installation if optional tools are missing.
