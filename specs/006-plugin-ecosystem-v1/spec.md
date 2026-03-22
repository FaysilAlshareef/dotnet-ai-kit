# Feature Specification: Plugin Ecosystem v1.0

**Feature Branch**: `006-plugin-ecosystem-v1`
**Created**: 2026-03-22
**Status**: Draft
**Input**: Add Claude Code plugin format, Agent Skills spec compliance, hooks, C# LSP MCP config, marketplace publishing, and competitive differentiation for v1.0. Roslyn MCP tools deferred to v1.1+.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install via Claude Code Plugin Marketplace (Priority: P1)

A developer discovers dotnet-ai-kit in the Claude Code plugin marketplace and installs it with a single command. All 26 slash commands, 104 skills, 13 agents, 6 rules, and hooks are available immediately without `pip install` or running `dotnet-ai init`.

**Why this priority**: Without plugin format support, the tool is invisible to the 9,000+ plugin ecosystem. This is the primary distribution channel for Claude Code extensions in 2026.

**Independent Test**: Can be fully tested by creating the `.claude-plugin/plugin.json` manifest, verifying the directory structure matches Claude Code's plugin spec, and confirming `/plugin install` resolves all components.

**Acceptance Scenarios**:

1. **Given** dotnet-ai-kit is published as a Claude Code plugin, **When** a user runs `/plugin marketplace add FaysilAlshareef/dotnet-ai-kit`, **Then** the plugin is registered and available for installation.
2. **Given** the plugin is in a marketplace, **When** a user runs `/plugin install dotnet-ai-kit`, **Then** all commands, skills, agents, rules, and hooks are deployed to the correct directories.
3. **Given** the plugin is installed, **When** a user types `/dotnet-ai.`, **Then** all 26 commands appear in autocomplete with their descriptions.
4. **Given** the plugin is installed, **When** Claude encounters a .NET project, **Then** relevant skills are loaded automatically via progressive disclosure (name+description at startup, full content on trigger).

---

### User Story 2 - Skills Work Across 16+ AI Tools (Priority: P1)

A developer using Codex CLI, Gemini CLI, or any Agent Skills-compatible tool can use the same dotnet-ai-kit skills. The SKILL.md files conform to the Agent Skills specification (agentskills.io) and load correctly in any compliant tool.

**Why this priority**: The Agent Skills specification is an open standard adopted by Anthropic, OpenAI, Microsoft, and 16+ tools. Non-compliance means skills only work in Claude Code, missing the entire cross-agent market.

**Independent Test**: Can be tested by validating each SKILL.md file against the Agent Skills schema (required: `name`, `description` in frontmatter; markdown body with instructions) and verifying progressive disclosure behavior.

**Acceptance Scenarios**:

1. **Given** a SKILL.md file, **When** parsed by any Agent Skills-compliant tool, **Then** the `name` and `description` fields are present in YAML frontmatter and correctly extracted.
2. **Given** 104 skill files, **When** an agent loads the skill index, **Then** only name+description are consumed at startup (~30-50 tokens per skill), and the full body loads only when triggered.
3. **Given** existing skill frontmatter with fields like `category` and `agent`, **When** migrated to Agent Skills spec, **Then** existing metadata is preserved as additional optional fields alongside the required `name` and `description`.

---

### User Story 3 - Hooks Guard Against Dangerous Actions (Priority: P2)

When working in a .NET project, hooks automatically prevent dangerous bash commands (e.g., `rm -rf`, `DROP TABLE`), auto-format code after edits, run `dotnet restore` after scaffolding, and lint before commits. The developer does not need to configure these; they are active by default after plugin installation.

**Why this priority**: Hooks are a key safety feature that competitors (claude-forge, dotnet-claude-kit) already provide. They prevent costly mistakes and enforce quality without manual intervention.

**Independent Test**: Can be tested by triggering each hook event (PreToolUse with a dangerous command, PostToolUse after file edit, PostToolUse after scaffold, PreToolUse before commit) and verifying the correct behavior (block, format, restore, lint).

**Acceptance Scenarios**:

1. **Given** the plugin is installed with hooks, **When** a user attempts to run a dangerous bash command (e.g., `rm -rf /`, `DROP DATABASE`), **Then** the pre-bash-guard hook blocks execution and warns the user.
2. **Given** a .cs file was edited, **When** the edit completes, **Then** the post-edit-format hook runs `dotnet format` on the changed file.
3. **Given** a `dotnet new` or scaffold command completes, **When** new project files are created, **Then** the post-scaffold-restore hook runs `dotnet restore` automatically.
4. **Given** a user is about to commit, **When** the pre-commit hook triggers, **Then** `dotnet format --verify-no-changes` runs and blocks the commit if formatting issues are found.

---

### User Story 4 - C# Language Intelligence via MCP (Priority: P2)

When working in a .NET project, Claude can use semantic code intelligence (go-to-definition, find references, diagnostics) via the C# LSP MCP server, instead of relying on grep-based file reading. This significantly reduces token usage and improves code navigation accuracy.

**Why this priority**: Semantic code intelligence is a 10x token efficiency improvement over grep-based analysis. Pointing to the existing csharp-ls MCP server is low effort with high impact.

**Independent Test**: Can be tested by configuring the `.mcp.json` file, installing the `csharp-ls` tool, and verifying that MCP tools (find_symbol, find_references, get_diagnostics) return correct results for a sample .NET project.

**Acceptance Scenarios**:

1. **Given** the plugin includes an `.mcp.json` config, **When** the user has `csharp-ls` installed, **Then** Claude can use C# language intelligence tools (go-to-definition, find references, diagnostics).
2. **Given** the `.mcp.json` points to `csharp-ls`, **When** a user asks Claude to find all usages of a class, **Then** results are returned via MCP in ~30-50 tokens instead of reading entire files.
3. **Given** the user does NOT have `csharp-ls` installed, **When** the plugin loads, **Then** the MCP server is skipped gracefully with a note suggesting installation.

---

### User Story 5 - Marketplace Discovery and Differentiation (Priority: P3)

A developer searching for .NET skills in Claude Code marketplace, PolySkill, or skills.sh can find dotnet-ai-kit and understand how it differs from Microsoft's dotnet/skills and dotnet-claude-kit. The plugin description, README, and metadata clearly communicate the unique value: full SDD lifecycle, 7 code generation commands, AI-powered project detection, and 12 project type support.

**Why this priority**: Without clear differentiation, users may choose Microsoft's official skills or dotnet-claude-kit instead. Clear positioning is essential for adoption.

**Independent Test**: Can be tested by verifying the plugin.json metadata, README marketplace section, and PolySkill listing contain differentiation messaging and correct feature counts.

**Acceptance Scenarios**:

1. **Given** dotnet-ai-kit is listed in a marketplace, **When** a user reads the description, **Then** the unique value proposition (SDD lifecycle, code gen commands, AI detection) is clearly stated.
2. **Given** a user has Microsoft's dotnet/skills installed, **When** they also install dotnet-ai-kit, **Then** there are no skill name conflicts (namespaced with `dotnet-ai` prefix).
3. **Given** dotnet-ai-kit is published on PolySkill, **When** a user searches for ".NET skills", **Then** the listing appears with correct category tags, skill count, and agent count.

---

### Edge Cases

- What happens when a user installs dotnet-ai-kit as both a pip package AND a Claude Code plugin? The plugin format takes precedence; the CLI remains available as a standalone tool for `init/check/upgrade/configure`.
- What happens when csharp-ls is not installed? The MCP config degrades gracefully — skills and commands still work, only MCP tools are unavailable.
- What happens when hooks encounter a project without .NET SDK installed? Hooks that depend on `dotnet` commands check for the tool first and skip with a warning if unavailable.
- What happens when a SKILL.md file has extra frontmatter fields beyond the Agent Skills spec? Extra fields are preserved as optional metadata and do not cause validation errors in any compliant tool.
- What happens when another plugin provides a command with the same name as a dotnet-ai-kit command? Claude Code's plugin namespacing prevents conflicts (commands become `dotnet-ai-kit:command-name`).
- What happens when the pre-bash-guard hook encounters a legitimate command that contains a blocked keyword (e.g., `grep "DROP" file.sql`)? The guard checks the command verb/structure, not arbitrary string matches in arguments.
- What happens when a user disables all hooks? The plugin continues to function normally with all commands, skills, and agents available — hooks are purely additive safety/quality features.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Project MUST include a `.claude-plugin/plugin.json` manifest file conforming to the Claude Code plugin specification, declaring all commands, skills, agents, rules, and hooks.
- **FR-002**: All 104 SKILL.md files MUST have `name` and `description` as required YAML frontmatter fields, conforming to the Agent Skills specification (agentskills.io). The `name` field MUST use the `dotnet-ai-` prefix (e.g., `dotnet-ai-clean-architecture`) to avoid conflicts with other .NET skill providers.
- **FR-003**: Existing SKILL.md optional frontmatter fields (`category`, `agent`, `version`, `language`, `framework`) MUST be preserved alongside the required Agent Skills fields.
- **FR-004**: Plugin MUST include a pre-bash-guard hook that blocks execution of dangerous commands. The plugin ships a default blocklist (including `rm -rf`, `DROP`, `TRUNCATE`, `format C:`, `del /s`). Users can extend this blocklist with additional patterns via the plugin settings file but cannot remove default patterns.
- **FR-005**: Plugin MUST include a post-edit-format hook that runs `dotnet format` on edited .cs files when the `dotnet` CLI is available.
- **FR-006**: Plugin MUST include a post-scaffold-restore hook that runs `dotnet restore` after scaffold/template commands create new project files.
- **FR-007**: Plugin MUST include a pre-commit-lint hook that runs `dotnet format --verify-no-changes` before git commits.
- **FR-008**: Plugin MUST include an `.mcp.json` configuration file pointing to the `csharp-ls` language server for C# code intelligence.
- **FR-009**: MCP configuration MUST degrade gracefully when `csharp-ls` is not installed — no errors, with a suggestion to install it.
- **FR-010**: Plugin MUST include marketplace metadata (README section, plugin.json fields) that clearly differentiates from Microsoft dotnet/skills and dotnet-claude-kit.
- **FR-011**: All slash commands MUST be namespaced with the plugin name to avoid conflicts with other plugins.
- **FR-012**: Hooks MUST check for prerequisite tools (dotnet CLI) before executing and skip gracefully if unavailable.
- **FR-013**: Each hook MUST be independently toggleable via a plugin settings file. All hooks are enabled by default. Disabling a hook prevents it from firing without requiring plugin removal.
- **FR-014**: The existing Python CLI (`dotnet-ai init/check/upgrade/configure`) MUST continue to work independently of the plugin format for users who prefer pip-based installation.
- **FR-015**: Plugin directory structure MUST follow Claude Code conventions: `.claude-plugin/` for manifest only, `commands/`, `skills/`, `agents/`, `hooks/` at root level.
- **FR-016**: Roslyn MCP tools (semantic analysis beyond LSP) are explicitly OUT OF SCOPE for v1.0 and deferred to v1.1+.

### Key Entities

- **Plugin Manifest** (`plugin.json`): Declares plugin identity (name, version, description, author), lists all included components (commands, skills, agents, hooks, MCP servers), and provides marketplace metadata (tags, category, homepage).
- **Hook**: A shell script or configuration entry that fires on specific Claude Code events (PreToolUse, PostToolUse, UserPromptSubmit). Each hook has a matcher (event + pattern), an action (command to run), and a failure mode (block or warn).
- **MCP Configuration** (`.mcp.json`): Declares external MCP servers the plugin depends on, including connection method (stdio/SSE), command to launch, and required tools.
- **Agent Skills Metadata**: The standardized YAML frontmatter in each SKILL.md — `name` (required), `description` (required), plus optional fields for categorization, versioning, and agent binding.

## Clarifications

### Session 2026-03-22

- Q: Can users toggle individual hooks on/off? → A: Yes, users can disable individual hooks via a settings file; all hooks are enabled by default.
- Q: What naming prefix for the `name` field in Agent Skills frontmatter? → A: Prefix all skill names with `dotnet-ai-` (e.g., `dotnet-ai-clean-architecture`, `dotnet-ai-cqrs`).
- Q: Should the bash-guard blocklist be fixed or user-extensible? → A: Ship a default blocklist; users can extend it with additional patterns via settings file but cannot remove default patterns.

## Assumptions

- Claude Code plugin format uses `.claude-plugin/plugin.json` as the manifest location. If Anthropic changes this, the manifest location will need updating.
- The Agent Skills specification at agentskills.io is stable and backward-compatible. Future spec versions will not break existing `name`/`description` frontmatter.
- The `csharp-ls` MCP server is installed separately by the user via `dotnet tool install -g csharp-ls`. The plugin does not bundle or auto-install it.
- Hook scripts use bash on macOS/Linux and PowerShell on Windows. Cross-platform hook compatibility follows Claude Code's built-in hook execution model.
- PolySkill and skills.sh accept submissions via GitHub repository links. No custom upload process is required.
- The existing Python CLI distribution via `pip install` continues to work alongside the plugin format. Users can choose either installation method.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Plugin can be installed via `/plugin install` in under 30 seconds with all 26 commands, 104 skills, 13 agents, 6 rules, and 4 hooks available immediately.
- **SC-002**: 100% of SKILL.md files pass Agent Skills specification validation (required `name` and `description` frontmatter).
- **SC-003**: Pre-bash-guard hook blocks at least 95% of common dangerous commands from a standard blocklist of 20+ patterns.
- **SC-004**: Post-edit-format hook successfully formats .cs files within 5 seconds of an edit when `dotnet` CLI is available.
- **SC-005**: Skill loading at session startup consumes less than 5,000 tokens total for all 104 skill index entries (progressive disclosure).
- **SC-006**: MCP-based symbol lookup returns results in under 2 seconds when `csharp-ls` is available, compared to 10+ seconds for grep-based search on a 50+ file project.
- **SC-007**: Zero namespace conflicts when installed alongside Microsoft dotnet/skills or dotnet-claude-kit.
- **SC-008**: Plugin passes Claude Code's plugin validation (`/plugin validate`) with no errors.
