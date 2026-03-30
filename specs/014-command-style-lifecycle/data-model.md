# Data Model: Fix Command Style Lifecycle

## Entities

### Managed Command File (filesystem)

Files created and managed by `copy_commands()` in the target commands directory.

| Attribute | Description |
|-----------|-------------|
| prefix | Either `dotnet-ai` (full) or `dai` (short) |
| command_name | The command identifier (e.g., `specify`, `plan`, `implement`) |
| extension | `.md` (from agent_config) |
| full_path | `{commands_dir}/{prefix}.{command_name}{extension}` |
| content | Full command content (never a redirect stub) |

**Identity**: Uniquely identified by `{prefix}.{command_name}{extension}` filename.

**Managed patterns** (for cleanup):
- `dotnet-ai.*.md` — full-prefix commands
- `dai.*.md` — short-prefix aliases

### copy_commands() Parameters

Updated function signature:

| Parameter | Type | Description |
|-----------|------|-------------|
| source_dir | Path | Directory containing command template .md files |
| target_dir | Path | Root of the user's project |
| agent_config | dict | Configuration for the target AI tool |
| config | DotnetAiConfig | The dotnet-ai-kit configuration |
| is_plugin | bool (default: False) | Whether the tool is running in plugin mode |

### Style × Mode Behavior Matrix

| command_style | is_plugin=False (standalone) | is_plugin=True (plugin) |
|---------------|----------------------------|------------------------|
| `full` | Write `dotnet-ai.*.md` | Write nothing (return 0) |
| `short` | Write `dai.*.md` | Write `dai.*.md` |
| `both` | Write `dotnet-ai.*.md` + `dai.*.md` | Write `dai.*.md` only |

**Invariant**: Cleanup always runs first, regardless of mode. All `dotnet-ai.*.md` and `dai.*.md` files are deleted before writing.

## State Transitions

```
Style Change Flow:
  [Previous Files Exist] → cleanup() → [Empty of managed files] → write() → [New Files Only]

Plugin Detection:
  _get_package_dir() / ".claude-plugin" / "plugin.json" exists? → is_plugin=True
  Otherwise → is_plugin=False (standalone)
```

## Relationships

- `DotnetAiConfig.command_style` determines which file prefixes to write
- `DotnetAiConfig.ai_tools` determines which `agent_config` to load (affects `commands_dir`, `command_prefix`)
- `_detect_plugin_mode()` (new in cli.py) reads package directory to determine `is_plugin`
- `_clean_managed_commands()` (new in copier.py) deletes files before `copy_commands()` writes
- `copy_commands()` is called from 3 entry points: `init()`, `upgrade()`, and `configure()` — all pass `is_plugin`
