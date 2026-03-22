# Contract: Interactive Configure Prompts

**Type**: CLI interaction contract
**Consumers**: Users running `dotnet-ai configure`

## Prompt Sequence

### 1. Company Name (text input)

```
Company name (used in C# namespaces): [current_value]
> _
```

Validation: Must be a valid C# identifier. Shows inline error if invalid:
```
Error: "123Corp" is not a valid C# identifier. Must start with a letter or underscore.
> _
```

### 2. GitHub Organization (text input)

```
GitHub organization: [current_value]
> _
```

Validation: Must be a valid GitHub org name.

### 3. Default Branch (text input with default)

```
Default git branch [main]: _
```

### 4. Permission Level (single-select)

```
Permission level:
  > 1. Minimal   - Only dotnet build/test/restore
    2. Standard  - Common dev commands (recommended)
    3. Full      - All commands including Docker, deploy tools

Use arrow keys or type number [2]:
```

### 5. AI Tools (multi-select)

```
AI tools to configure (space to toggle, enter to confirm):
  [x] Claude Code
  [ ] Cursor
  [ ] GitHub Copilot
  [ ] Codex CLI
  [ ] Antigravity
```

### 6. Command Style (single-select)

```
Command style:
  > 1. Full names only    (e.g., /dotnet-ai.specify)
    2. Short aliases only  (e.g., /dai.spec)
    3. Both               (full + short aliases)

Use arrow keys or type number [3]:
```

## Non-Interactive Mode

When `--minimal` flag is used or no TTY is detected:

```
dotnet-ai configure --minimal
```

Only prompts for company name (required). All other options use defaults.

## Output on Completion

```
Configuration saved to .dotnet-ai-kit/config.yml
  Company: Contoso
  GitHub org: contoso-ltd
  Branch: main
  Permissions: standard
  AI tools: claude
  Style: both
```
