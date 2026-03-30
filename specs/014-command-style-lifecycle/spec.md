# Feature Specification: Fix Command Style Lifecycle

**Feature Branch**: `014-command-style-lifecycle`
**Created**: 2026-03-30
**Status**: Draft
**Input**: User description: "Fix Command Style Lifecycle: Cleanup on Style Change, Plugin Mode Awareness, and Short Alias Content"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Style Change Cleans Up Stale Files (Priority: P1)

As a tool user, when I change my command style preference (e.g., from `both` to `short`), I expect only the commands matching my new style to exist in the commands directory. Currently, old command files from the previous style remain, causing duplicate commands to appear in the command list.

**Why this priority**: This is the most impactful issue affecting all users. Every style change leaves behind stale files that confuse command discovery and pollute the command list. Users see duplicate entries and don't know which to use.

**Independent Test**: Change `command_style` from `both` to `short` in config, run the tool's configure/upgrade command, and verify only `dai.*.md` files exist in the commands directory with zero `dotnet-ai.*.md` files remaining.

**Acceptance Scenarios**:

1. **Given** a project initialized with `command_style: both` (54 command files), **When** the user changes to `command_style: short` and runs configure/upgrade, **Then** only 27 `dai.*.md` files exist in the commands directory and all 27 `dotnet-ai.*.md` files are removed.
2. **Given** a project initialized with `command_style: full`, **When** the user changes to `command_style: both`, **Then** both `dotnet-ai.*.md` and `dai.*.md` files exist and no stale files from a previous style remain.
3. **Given** a project with `command_style: short`, **When** the user changes to `command_style: full`, **Then** only `dotnet-ai.*.md` files exist and all `dai.*.md` files are removed.
4. **Given** a commands directory containing user-created custom command files (not matching managed patterns), **When** a style change cleanup runs, **Then** custom files are preserved and only managed command files are affected.

---

### User Story 2 - Short Aliases Contain Full Command Content (Priority: P1)

As a tool user using `command_style: both`, when I invoke a short alias command like `/dai.specify`, I expect it to execute the full command behavior. Currently, short alias files contain only a redirect stub ("See /dotnet-ai.specify") that doesn't provide the actual instructions, making them non-functional.

**Why this priority**: Equally critical as cleanup since short aliases in `both` mode are effectively broken. Users who prefer short aliases get no value from them when both styles are enabled.

**Independent Test**: Initialize with `command_style: both`, read any `dai.*.md` file, and verify it contains the full command instructions (not a redirect stub).

**Acceptance Scenarios**:

1. **Given** `command_style: both`, **When** command files are generated, **Then** every `dai.*.md` file contains the complete command content identical to its `dotnet-ai.*.md` counterpart.
2. **Given** `command_style: short`, **When** command files are generated, **Then** `dai.*.md` files contain the complete command content (unchanged behavior).
3. **Given** `command_style: both`, **When** a user invokes `/dai.specify`, **Then** the full specification workflow executes without needing to reference or redirect to `/dotnet-ai.specify`.

---

### User Story 3 - Plugin Mode Prevents Command Duplication (Priority: P2)

As a plugin user, when dotnet-ai-kit is installed as a Claude Code plugin, I should not see duplicate commands from both the plugin system (`dotnet-ai-kit:do`) and copied files (`/dotnet-ai.do`). The tool should detect plugin mode and only copy short alias files, since the plugin system already serves the full-prefix commands.

**Why this priority**: Affects the growing subset of users installing via the plugin system. While functional, the duplication creates confusion about which command variant to use and clutters the command list.

**Independent Test**: Install the tool as a plugin, run init, and verify that no `dotnet-ai.*.md` files are copied to `.claude/commands/` while `dai.*.md` short aliases are still available.

**Acceptance Scenarios**:

1. **Given** the tool is installed as a plugin and `command_style: both`, **When** init runs, **Then** only `dai.*.md` files are written to the commands directory (no `dotnet-ai.*.md` files).
2. **Given** the tool is installed as a plugin and `command_style: full`, **When** init runs, **Then** no command files are written (the plugin system serves full commands natively).
3. **Given** the tool is installed as a plugin and `command_style: short`, **When** init runs, **Then** only `dai.*.md` files are written with full content.
4. **Given** the tool is NOT installed as a plugin (standalone mode), **When** init runs, **Then** behavior is identical to current: files are written according to style selection (backward compatible).

---

### Edge Cases

- What happens when the commands directory does not yet exist during cleanup? (Cleanup should be a no-op; directory creation proceeds normally.)
- What happens when the user has manually renamed or modified a managed command file? (Cleanup deletes files matching `dotnet-ai.*.md` and `dai.*.md` patterns regardless of content modifications.)
- What happens during upgrade when no config.yml exists? (Existing behavior applies; the tool uses default style.)
- What happens if the plugin detection check encounters a corrupted or missing `plugin.json`? (Treat as standalone mode — default to `is_plugin=False`.)
- What happens when style is set to `both` in plugin mode and a user later uninstalls the plugin? (The `dai.*.md` files continue to work independently since they have full content. User can then change style to `both` or `full` to restore `dotnet-ai.*.md` files.)

## Requirements *(mandatory)*

### Functional Requirements

**Cleanup on Style Change**:
- **FR-001**: The system MUST delete all existing managed command files (`dotnet-ai.*.md` and `dai.*.md`) from the target commands directory before writing new files for the selected style.
- **FR-002**: The cleanup MUST only delete files matching the managed command patterns (`dotnet-ai.*.md` and `dai.*.md`). User-created command files MUST be preserved.
- **FR-003**: The cleanup MUST execute on every command copy operation (init, upgrade, configure style change).

**Short Alias Content**:
- **FR-004**: Short alias files (`dai.*.md`) MUST always contain the complete command content, never redirect stubs.
- **FR-005**: The content of a `dai.*.md` file MUST be functionally equivalent to its corresponding `dotnet-ai.*.md` file (same instructions, same behavior).

**Plugin Mode Detection**:
- **FR-006**: The system MUST detect whether it is running in plugin mode by checking for the presence of the plugin manifest file in the package source directory.
- **FR-007**: In plugin mode, the system MUST NOT write `dotnet-ai.*.md` files to the commands directory, since the plugin system already serves equivalent commands.
- **FR-008**: In plugin mode with `command_style: full`, the system MUST write zero command files (plugin handles everything).
- **FR-009**: In plugin mode with `command_style: short` or `both`, the system MUST write only `dai.*.md` files with full content.
- **FR-010**: In standalone mode (not a plugin), the system MUST behave identically to the current implementation for backward compatibility, except that cleanup and full-content short aliases apply.

**Style × Mode Matrix**:
- **FR-011**: The system MUST follow this behavior matrix:

  | Style | Standalone Mode | Plugin Mode |
  |-------|-----------------|-------------|
  | `full` | Write `dotnet-ai.*.md` only | Write nothing (plugin serves) |
  | `short` | Write `dai.*.md` only | Write `dai.*.md` only |
  | `both` | Write `dotnet-ai.*.md` + `dai.*.md` | Write `dai.*.md` only |

**Integration Points**:
- **FR-012**: The init command MUST pass plugin mode status to the command copy operation.
- **FR-013**: The upgrade command MUST pass plugin mode status to the command copy operation.
- **FR-014**: The configure CLI command MUST re-copy command files (with cleanup) after saving configuration, so style changes take effect immediately without requiring a separate `upgrade --force`.
- **FR-015**: The configure slash command documentation MUST describe plugin mode behavior under the command style section.
- **FR-016**: The init slash command documentation MUST note the difference between plugin and standalone command file behavior.
- **FR-017**: The configure command MUST pass plugin mode status to the command re-copy operation, consistent with init and upgrade.

### Key Entities

- **Managed Command File**: A file in the commands directory matching `dotnet-ai.*.md` or `dai.*.md` patterns. These are created and managed by the tool and safe to delete during cleanup.
- **Command Style**: A configuration value (`full`, `short`, or `both`) that determines which prefix patterns of command files to generate.
- **Plugin Mode**: A runtime-detected boolean indicating whether the tool is installed as a Claude Code plugin (the plugin system serves `dotnet-ai-kit:*` commands natively).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After any style change, 100% of command files in the commands directory match the selected style with zero stale files from a previous style.
- **SC-002**: 100% of `dai.*.md` files contain complete command content (zero redirect stubs) regardless of the active command style.
- **SC-003**: In plugin mode, zero `dotnet-ai.*.md` files are written to the commands directory.
- **SC-004**: In standalone mode, all existing test cases continue to pass (backward compatibility).
- **SC-005**: Users see exactly one invocable variant per command per naming convention (no duplicate entries from overlapping plugin + copied files).

## Assumptions

- The plugin manifest file (`plugin.json`) is always located in a `.claude-plugin/` directory within the package source directory, not in the user's project directory.
- The two managed file patterns (`dotnet-ai.*.md` and `dai.*.md`) are sufficient to identify all tool-managed command files. No other naming patterns are used.
- The `upgrade --force` code path calls the same command copy function as `init`, ensuring consistent behavior.
- The configure command's CLI implementation calls the command copy function when style changes, ensuring cleanup runs through all entry points.
