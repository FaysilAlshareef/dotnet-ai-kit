# Feature Specification: Fix Permission System - Bypass Mode & Auto-Apply

**Feature Branch**: `009-fix-permission-bypass`
**Created**: 2026-03-24
**Status**: Draft
**Input**: User description: "Fix permission system: apply bypass mode for full level, copy permissions to target projects, expand command coverage, add global install support"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Permission-Free Workflow with Full Mode (Priority: P1)

A developer initializes dotnet-ai-kit in their .NET project and selects "full" permission level. When they start an AI coding session, they can work without any permission prompts interrupting their flow. The tool automatically configures the AI assistant to operate in full bypass mode, allowing all operations (file reads, edits, bash commands, web searches) without manual approval.

**Why this priority**: This is the core pain point. Developers are currently interrupted by permission prompts despite selecting "full" mode, breaking their workflow and making the tool frustrating to use. Without this fix, the permission setting is effectively non-functional.

**Independent Test**: Can be fully tested by running `dotnet-ai init` with full permissions in a fresh project and verifying the AI assistant starts without any permission prompts for standard development operations.

**Acceptance Scenarios**:

1. **Given** a developer runs the initialization command with "full" permission level, **When** the initialization completes, **Then** the AI assistant's settings file in the project contains the bypass permission mode configuration, and no permission prompts appear during standard development operations (file editing, running builds, running tests, git operations).

2. **Given** a developer has an existing project with "standard" permission level, **When** they reconfigure to "full" permission level, **Then** the AI assistant's settings file is updated to include bypass mode, preserving any existing custom settings.

3. **Given** a developer selects "full" permission level, **When** they perform operations like searching code, listing files, running builds, and editing files, **Then** zero permission prompts appear for any of these operations.

---

### User Story 2 - Automatic Permission Application on Init/Configure (Priority: P1)

A developer runs the initialization or configuration command and selects a permission level (minimal, standard, or full). The tool automatically writes the corresponding permission rules into the AI assistant's project-level settings file, so the permissions take effect immediately without any manual file editing.

**Why this priority**: Currently, selecting a permission level only saves a label to the config file but never applies the actual permissions. This is the fundamental bug causing all permission issues. Tied with Story 1 as the core fix.

**Independent Test**: Can be fully tested by running the configure command, selecting any permission level, and then inspecting the AI assistant's settings file to verify the permission rules are present and correctly structured.

**Acceptance Scenarios**:

1. **Given** a developer runs initialization for the first time, **When** they select "standard" permission level, **Then** the tool creates/updates the AI assistant's project settings file with the corresponding permission allow-list entries.

2. **Given** a developer runs initialization and an AI assistant settings file already exists with custom permissions, **When** the tool applies the new permission level, **Then** existing user-defined permissions are preserved and the tool's permissions are merged in without duplicates.

3. **Given** a developer changes their permission level from "minimal" to "full", **When** the configuration update completes, **Then** the old minimal permissions are replaced with the full permissions, and bypass mode is enabled.

4. **Given** a developer changes their permission level from "full" to "standard", **When** the configuration update completes, **Then** bypass mode is removed and the standard allow-list replaces the full allow-list.

---

### User Story 3 - Comprehensive Command Coverage (Priority: P2)

When a developer selects "full" permissions, the permission set covers all common development commands they would use during a typical .NET/web development session. This includes file system operations, search tools, build tools, package managers, version control, container tools, and editor utilities. Developers should not encounter permission prompts for any standard development command.

**Why this priority**: Even with permissions applied, an incomplete command list causes unexpected prompts. Expanding coverage eliminates the "whack-a-mole" experience of approving commands one by one.

**Independent Test**: Can be tested by running a comprehensive set of common development commands (build, test, search, file operations, git, npm/node, docker) and verifying none trigger permission prompts.

**Acceptance Scenarios**:

1. **Given** a project with "full" permissions applied, **When** the developer uses file system commands (list, find, search, read, copy, move, remove), **Then** no permission prompts appear.

2. **Given** a project with "full" permissions applied, **When** the developer uses .NET commands (build, test, run, publish, format, ef migrations, new), **Then** no permission prompts appear.

3. **Given** a project with "full" permissions applied, **When** the developer uses web development commands (npm, node, ng, yarn, pnpm), **Then** no permission prompts appear.

4. **Given** a project with "full" permissions applied, **When** the developer uses search and analysis commands (grep, ripgrep, find, wc, head, tail), **Then** no permission prompts appear.

---

### User Story 4 - Global Permission Installation (Priority: P2)

A developer wants their permission settings to apply across all repositories on their machine, not just the current project. They can run a command with a "global" flag that installs permissions to the user-level settings location, so every project they open benefits from the same permission level without needing to run init in each one.

**Why this priority**: Developers working across multiple repos (e.g., microservice architectures with separate command/query/gateway projects) need consistent behavior everywhere. Without global support, they must configure each repo individually.

**Independent Test**: Can be tested by running the global install command, then opening the AI assistant in a completely different project directory and verifying the permissions are active.

**Acceptance Scenarios**:

1. **Given** a developer runs the permission installation with the global flag and "full" level, **When** they open the AI assistant in any project on their machine, **Then** the full permissions (including bypass mode) are active without project-level configuration.

2. **Given** a developer has global "full" permissions installed, **When** a specific project has a project-level "minimal" configuration, **Then** the project-level configuration takes precedence over the global settings for that project.

3. **Given** a developer has previously installed global permissions, **When** they run the global install command again with a different level, **Then** the global settings are updated to reflect the new level.

---

### User Story 5 - Upgrade Existing Projects (Priority: P3)

A developer who previously initialized dotnet-ai-kit (before this fix) runs the upgrade command. The tool detects that permissions were configured but never applied, and automatically applies the correct permission rules to the AI assistant's settings file based on their existing `permissions_level` setting.

**Why this priority**: Important for existing users who already have the tool configured but are experiencing the bug. Lower priority because it affects only the transition period after the fix is released.

**Independent Test**: Can be tested by creating a project with the old configuration (permissions_level set but no settings file entries), running upgrade, and verifying permissions are now applied.

**Acceptance Scenarios**:

1. **Given** a project initialized with the old version that has `permissions_level: full` in config but no permissions in the AI settings file, **When** the developer runs the upgrade command, **Then** the full permissions and bypass mode are applied to the AI settings file.

2. **Given** a project initialized with the old version, **When** the upgrade detects the permission gap, **Then** it reports what was applied in the upgrade summary output.

---

### Edge Cases

- What happens when the AI assistant settings file has invalid JSON? The tool should report the error clearly and not overwrite the corrupted file.
- What happens when the developer has no write access to the global settings directory? The tool should fail gracefully with an actionable error message.
- What happens when the AI assistant settings file has been customized with deny rules? Deny rules must be preserved as-is during permission merging.
- What happens when running init in a project that already has up-to-date permissions? The tool should detect no changes are needed and skip the write, reporting "permissions already up to date."
- What happens when the permission template file is missing from the tool's installation? The tool should report the missing file and suggest reinstalling.
- What happens when multiple developers on the same repo run configure with different permission levels? Since `.claude/settings.json` is committed, standard git merge conflict handling applies. The last committed version wins; conflicts are resolved through normal git workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST write permission rules to the AI assistant's project settings file (`.claude/settings.json`, committed to version control) when initialization or configuration runs with any permission level selected, creating the file if it does not exist.
- **FR-002**: When "full" permission level is selected, the tool MUST configure the AI assistant to use its built-in bypass permission mode, which skips all permission prompts.
- **FR-003**: When "minimal" or "standard" permission level is selected, the tool MUST write only the specific allow-list rules from the corresponding template, without enabling bypass mode.
- **FR-004**: The tool MUST merge permissions into existing AI assistant settings files without destroying user-defined custom rules (allow, ask, or deny entries).
- **FR-005**: The tool MUST support a global installation flag that writes permissions to the user-level settings location (applies to all projects on the machine).
- **FR-006**: The "full" permission template MUST include allow-list entries for all common development commands: file system operations (ls, dir, find, grep, cat, head, tail, wc, cp, mv, rm, mkdir, echo, pwd, touch, chmod), .NET operations (dotnet build/test/run/publish/format/new/ef/restore/watch/clean/add/remove/list/tool), version control (all git and gh subcommands), web development (npm, node, ng, yarn, pnpm, npx), container tools (docker, docker-compose), search tools (rg, grep, find, ag), and general utilities (curl, wget, which, where, env, set, export, sed, awk, sort, uniq, xargs, tee).
- **FR-007**: When a developer changes their permission level (e.g., from standard to full, or full to minimal), the tool MUST replace the previous level's rules with the new level's rules, while preserving any user-defined custom entries. The tool tracks its managed entries in its own config file (`config.yml`) and diffs against the AI assistant settings file to identify which entries are tool-managed vs. user-added.
- **FR-008**: The upgrade command MUST detect projects with a configured permission level but missing permission rules in the AI settings file, and automatically apply the correct rules.
- **FR-009**: The tool MUST provide clear feedback (console output) showing what permissions were applied, the target settings file path, and the active permission mode.
- **FR-010**: When "full" permission level is selected, the tool MUST display a one-time security warning during init/configure explaining that bypass mode disables all permission prompts. No recurring warnings on subsequent AI assistant sessions.
- **FR-011**: The permission application MUST support a dry-run mode that previews what permissions would be written without modifying any files, consistent with the tool's `--dry-run` convention.
- **FR-012**: Before modifying the AI assistant settings file, the tool MUST create a backup of the existing file to enable reversal via the undo command.

### Key Entities

- **Permission Level**: One of three tiers (minimal, standard, full) that determines the scope of allowed operations. Each level is a superset of the previous.
- **Permission Template**: A predefined set of allow-list rules corresponding to each permission level. Templates define which operations the AI assistant can perform without prompting.
- **AI Assistant Settings File**: The project settings file (`.claude/settings.json`, committed to version control) at project level, or the user-level global settings file (`~/.claude/settings.json`). The project file is committed so permissions are shared with all team members working on the repository.
- **Permission Mode**: The AI assistant's built-in operating mode (default, acceptEdits, bypassPermissions) that controls how broadly permissions are granted. "Full" level maps to bypass mode.
- **Permission Merge**: The process of combining tool-managed permission entries with user-defined custom entries, preserving both without duplication. The tool's own config (`config.yml`) serves as the source of truth for which entries it manages, enabling clean diffs during level changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After selecting "full" permission level and initializing, 100% of standard development operations (build, test, edit, search, git) execute without any permission prompts.
- **SC-002**: Permission application takes less than 2 seconds as part of the init/configure workflow.
- **SC-003**: Existing user-defined permission rules survive all permission level changes with 0 entries lost.
- **SC-004**: Developers working across multiple repositories can apply permissions globally in a single command, eliminating the need to configure each project individually.
- **SC-005**: Developers upgrading from the previous version have their permissions automatically applied on the next upgrade run, with zero manual intervention required.
- **SC-006**: The tool correctly handles all edge cases (corrupted files, missing templates, no write access) with user-friendly error messages that include resolution steps.

## Clarifications

### Session 2026-03-24

- Q: Should the tool write project-level permissions to `.claude/settings.json` (shared/committed) or `.claude/settings.local.json` (gitignored/per-developer)? → A: ~~Originally: `.claude/settings.local.json`~~ **Revised**: Write to `.claude/settings.json` (committed to version control, shared with team). Permissions should never be gitignored and should always be committable.
- Q: How should the tool distinguish its managed permission entries from user-added custom entries during merges and level changes? → A: Track managed entries in the tool's own config (`config.yml`) and diff against the settings file during level changes. Avoids polluting AI assistant settings with non-standard fields.
- Q: What warning behavior should apply when a developer selects "full" (bypass) mode? → A: Show a one-time warning during init/configure when "full" is selected. No warning on subsequent sessions. The developer has made a deliberate choice; recurring warnings defeat the purpose.

## Assumptions

- The AI assistant (Claude Code) is the primary target. Other AI tools (Cursor, Copilot, Codex) are not affected by this change since they do not use the same settings file format.
- The settings file format follows the established schema (`https://json.schemastore.org/claude-code-settings.json`).
- Bypass permission mode is an acceptable security posture for developers who explicitly choose "full" permissions. A one-time warning is displayed at configuration time; no recurring warnings during sessions.
- Global settings use the standard user-level settings directory (`~/.claude/settings.json`).
- Project-level settings take precedence over global settings, consistent with the AI assistant's documented behavior.
- The tool tracks its managed permission entries in its own config file (`config.yml`), using a diff-based approach to distinguish managed from user-defined entries during merges and level changes.

## Out of Scope

- Changing permission behavior for AI tools other than Claude Code (Cursor, Copilot, Codex use different mechanisms).
- Adding new permission levels beyond the existing three (minimal, standard, full).
- Network sandboxing or filesystem sandboxing configuration.
- MCP server permission management (handled separately via `mcp-permissions.json`).
- Enterprise/managed settings support (requires admin-level deployment, not a single-developer feature).
