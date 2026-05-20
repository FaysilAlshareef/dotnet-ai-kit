# Extension Development Guide

Extensions let you ship custom slash commands and convention rules that work
alongside the built-in dotnet-ai-kit content. Install from a local directory;
catalog-based installs are planned for v1.1.

---

## Quick start

```bash
# Create your extension directory
mkdir my-extension && cd my-extension

# Create the manifest
cat > extension.yml << 'EOF'
extension:
  id: my-extension
  name: My Extension
  version: 1.0.0
  min_cli_version: 1.0.0

provides:
  commands:
    - name: dotnet-ai.myext.run
      file: commands/run.md
      description: Run my extension command

hooks:
  after_install:
    - dotnet restore
EOF

# Create a command file
mkdir commands
echo "# My command" > commands/run.md

# Install into your project
dotnet-ai extension-add --dev ./my-extension

# Verify
dotnet-ai extension-list
```

---

## `extension.yml` reference

```yaml
extension:
  id: <string>              # Required. Unique identifier. Used in the registry.
  name: <string>            # Required. Human-readable display name.
  version: <string>         # Required. Semantic version (e.g., "1.2.0").
  min_cli_version: <string> # Optional. Minimum dotnet-ai CLI version required.
                            # Default: "1.0.0". Install is rejected if CLI is older.

provides:
  commands:
    - name: <string>        # Full command name (must be unique across all extensions).
      file: <path>          # Path relative to extension root (e.g., "commands/run.md").
      description: <string> # One-line description shown in listings.

  rules:
    - file: <path>          # Path relative to extension root (e.g., "rules/my-rule.md").
                            # Basename must be unique across all installed extensions.

hooks:
  after_install:            # Run after successful install. Failure blocks the install.
    - <shell command>
  after_remove:             # Run after removal. Failure raises an error with cleanup instructions.
    - <shell command>
```

### Validation rules

| Field | Validation |
|-------|-----------|
| `id` | Non-empty string; must be unique in the registry |
| `name` | Non-empty string |
| `version` | Non-empty string |
| `min_cli_version` | Compared against installed CLI via semantic version; install rejected if CLI is older |
| `provides.commands[].name` | Must be unique across ALL installed extensions (name collision blocks install) |
| `provides.rules[].file` | Basename must be unique across ALL installed extensions (collision blocks install) |
| `hooks` keys | Only `after_install` and `after_remove` are valid |
| Hook values | Must be lists of strings — not nested objects |

---

## Adding commands

Create a Markdown file for each command (max 200 lines):

```markdown
---
description: One-line description shown in the commands list
---

# My Command

Brief description of what this command does.

## Usage

Describe when and how to use it.

## Examples

**Example 1:**
```
/dotnet-ai.myext.run --option value
```
```

Command names must be globally unique across all installed extensions.
Use a namespace prefix to avoid collisions: `dotnet-ai.{vendor}.{command}`.

---

## Adding rules

Rules extend the convention enforcement that the AI applies while writing code.
Create a Markdown file (max 100 lines):

```markdown
---
description: One-line description
paths:               # Optional: only load when these glob patterns match
  - "src/**/MyArea/**/*.cs"
---

# My Convention Rule

## Rules

- ALWAYS do X when Y
- NEVER do Z in this codebase
```

Rule filenames must be unique across all installed extensions. Use a prefix:
`my-vendor-my-rule.md`.

---

## Lifecycle hooks

Hooks run shell commands at install and remove time. They run synchronously
with `cwd` set to your project root.

```yaml
hooks:
  after_install:
    - dotnet restore                   # runs after successful install
    - dotnet build --no-restore        # second command runs only if first succeeds

  after_remove:
    - dotnet clean                     # runs after removal
```

### Platform behaviour

| Platform | Command parsing |
|----------|----------------|
| Windows | `hook_cmd.split()` |
| POSIX (macOS, Linux) | `shlex.split(hook_cmd)` |

If `after_install` fails, the install is rolled back and the extension is not
registered. If `after_remove` fails, an error is raised with cleanup instructions.

---

## Installing and testing locally

```bash
# Install from a local directory
dotnet-ai extension-add --dev ./my-extension

# List installed extensions
dotnet-ai extension-list

# Remove
dotnet-ai extension-remove my-extension
```

`dotnet-ai extension-add <name>` without `--dev` shows a user-friendly message
directing to `--dev`; catalog-based installs are planned for v1.1.

---

## Extension registry

Installed extensions are tracked in `.dotnet-ai-kit/extensions.yml`:

```yaml
- id: my-extension
  version: 1.0.0
  source: local:./my-extension
  installed: "2026-05-20"
  commands:
    - dotnet-ai.myext.run
  rules:
    - my-vendor-my-rule.md
  hooks:
    after_install:
      - dotnet restore
```

The registry file is locked during install and remove operations to prevent
concurrent corruption.

---

## Conflict detection

The install is rejected with a clear error when any of the following conflicts
are detected:

| Conflict | Example error |
|---------|---------------|
| Duplicate command name | `"dotnet-ai.myext.run" is already registered by extension "other-ext"` |
| Duplicate rule filename | `"my-rule.md" is already registered by extension "other-ext"` |
| Extension ID already registered | `"my-extension" is already installed; use extension-remove first` |
| CLI version too old | `Extension requires dotnet-ai >= 1.2.0; installed is 1.0.0` |

---

## Checklist before publishing

- [ ] `extension.yml` has `id`, `name`, `version` filled
- [ ] `min_cli_version` set to the oldest CLI that supports your command syntax
- [ ] Command names are namespaced (`dotnet-ai.{vendor}.{command}`)
- [ ] Rule filenames are prefixed to avoid collisions
- [ ] `after_install` hooks are idempotent (safe to run more than once)
- [ ] Tested with `dotnet-ai extension-add --dev .` and `dotnet-ai extension-list`
- [ ] Tested removal with `dotnet-ai extension-remove <id>`
