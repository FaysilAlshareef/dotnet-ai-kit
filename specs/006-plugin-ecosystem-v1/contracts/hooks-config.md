# Contract: Hook Configuration

**Location**: Hooks are defined in the plugin and configured via Claude Code's settings.

## 4 Hooks

### pre-bash-guard

- **Event**: PreToolUse
- **Matcher**: Tool = `Bash`
- **Behavior**: Parse command, check first verb of each pipeline segment against blocklist. If match → block with warning message.
- **Mode**: block
- **Default blocklist** (20+ patterns):
  - `rm -rf /`, `rm -r /`, `rmdir /s`, `del /s /q`
  - `format C:`, `mkfs`
  - `DROP DATABASE`, `DROP TABLE`, `TRUNCATE TABLE`
  - `DELETE FROM` (without WHERE clause)
  - `shutdown`, `reboot`
  - `dd if=`, `> /dev/sda`
  - `chmod -R 777`, `chown -R`
  - `wget | sh`, `curl | bash`, `curl | sh`
  - Fork bomb patterns

### post-edit-format

- **Event**: PostToolUse
- **Matcher**: Tool = `Edit` or `Write`, file matches `*.cs`
- **Behavior**: Run `dotnet format <file>` on the edited file. If `dotnet` not on PATH → skip silently.
- **Mode**: warn (non-blocking)

### post-scaffold-restore

- **Event**: PostToolUse
- **Matcher**: Tool = `Bash`, command contains `dotnet new`
- **Behavior**: Run `dotnet restore` in the project directory. If `dotnet` not on PATH → skip silently.
- **Mode**: warn (non-blocking)

### pre-commit-lint

- **Event**: PreToolUse
- **Matcher**: Tool = `Bash`, command contains `git commit`
- **Behavior**: Run `dotnet format --verify-no-changes`. If formatting issues found → block commit. If `dotnet` not on PATH → skip silently.
- **Mode**: block

## User Settings

Users toggle hooks and extend the blocklist via Claude Code settings:

```json
{
  "hooks": {
    "pre-bash-guard": { "enabled": true, "extra_patterns": [] },
    "post-edit-format": { "enabled": true },
    "post-scaffold-restore": { "enabled": true },
    "pre-commit-lint": { "enabled": true }
  }
}
```
