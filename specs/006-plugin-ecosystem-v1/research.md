# Research: Plugin Ecosystem v1.0

**Phase**: 0 — Outline & Research
**Date**: 2026-03-22

## R1: Claude Code Plugin Manifest Format

**Decision**: Use `.claude-plugin/plugin.json` with the standard manifest schema.

**Rationale**: This is the official format documented at code.claude.com/docs/en/plugins. All 9,000+ plugins use this structure. The manifest declares name, version, description, author, and lists component directories.

**Alternatives considered**:
- Custom manifest format → Rejected: would not be recognized by `/plugin install`
- No manifest (rely on directory conventions only) → Rejected: marketplace requires plugin.json

**Key findings**:
- plugin.json goes INSIDE `.claude-plugin/` directory
- commands/, skills/, agents/, hooks/ go at repo ROOT (not inside .claude-plugin/)
- Skills are auto-namespaced with plugin name (e.g., `dotnet-ai-kit:skill-name`)
- Hooks are defined as entries in the hooks configuration, not as standalone scripts in some cases — Claude Code uses a `settings.json` hooks array OR standalone script files in `hooks/`

## R2: Agent Skills Specification Compliance

**Decision**: Migrate all 104 SKILL.md files to add `dotnet-ai-` prefix to existing `name` fields. No structural changes needed — current frontmatter already has `name` and `description`.

**Rationale**: The Agent Skills spec (agentskills.io) requires only `name` and `description` in YAML frontmatter. Our files already have both. The only change is prefixing `name` values with `dotnet-ai-` per the clarification decision.

**Alternatives considered**:
- Full rewrite of frontmatter → Rejected: current format already compliant, only prefix needed
- No prefix (rely on plugin namespacing) → Rejected: cross-agent tools outside Claude Code don't namespace

**Key findings**:
- Required fields: `name` (string), `description` (string)
- Optional fields: anything else (our `category`, `agent` fields are fine)
- Progressive disclosure: tools load only name+description at startup (~30-50 tokens per skill)
- The spec is backward-compatible: extra fields are ignored by non-supporting tools

## R3: Claude Code Hooks System

**Decision**: Use Claude Code's native hooks configuration format with 4 hooks defined in the plugin's settings.

**Rationale**: Claude Code hooks fire on 9 event types (PreToolUse, PostToolUse, SessionStart, SessionEnd, PreCompact, UserPromptSubmit, Notification, Stop, SubagentStop). Our 4 hooks map to PreToolUse (bash-guard, commit-lint) and PostToolUse (edit-format, scaffold-restore).

**Alternatives considered**:
- Standalone shell scripts only → Rejected: Claude Code plugins define hooks via configuration, not just scripts
- Git hooks (pre-commit, post-commit) → Rejected: these are separate from Claude Code hooks; our hooks are AI-workflow hooks, not git hooks

**Key findings**:
- Hook configuration format: JSON array in settings with `event`, `pattern` (regex matcher), `command` (shell command to run)
- Hooks can `block` (prevent action) or `warn` (log and continue)
- bash-guard: PreToolUse event, matches Bash tool calls, checks command against blocklist
- edit-format: PostToolUse event, matches Edit/Write tool calls on .cs files
- scaffold-restore: PostToolUse event, matches Bash tool calls containing `dotnet new`
- commit-lint: PreToolUse event, matches Bash tool calls containing `git commit`
- Cross-platform: Claude Code handles bash vs PowerShell selection based on OS

## R4: MCP Configuration for csharp-ls

**Decision**: Include `.mcp.json` at repo root pointing to `csharp-ls` via stdio transport.

**Rationale**: The csharp-ls MCP server provides C# language intelligence (go-to-definition, find references, diagnostics) via the Language Server Protocol over stdio. It's the most widely-used open-source C# LSP for AI tools.

**Alternatives considered**:
- OmniSharp → Rejected: heavier, requires more setup, csharp-ls is lighter and MCP-native
- Roslyn Navigator (dotnet-claude-kit's custom MCP) → Rejected: proprietary, would create dependency on competitor
- No MCP at all → Rejected: 10x token efficiency improvement is too valuable to skip

**Key findings**:
- Install: `dotnet tool install -g csharp-ls`
- Transport: stdio (launch as subprocess)
- The `.mcp.json` format declares server name, command, args, and available tools
- Graceful degradation: if csharp-ls not installed, MCP server simply doesn't start — no errors

## R5: Bash-Guard Pattern Matching

**Decision**: Use command-verb matching (not substring matching) for the blocklist. Match the first command in a pipeline/chain.

**Rationale**: Substring matching produces false positives (e.g., `grep "DROP" file.sql` would be blocked). Verb matching checks the actual command being executed.

**Alternatives considered**:
- Full regex on entire command string → Rejected: too many false positives
- AST-level command parsing → Rejected: over-engineered for a safety guard
- Allowlist instead of blocklist → Rejected: too restrictive, breaks normal workflows

**Key findings**:
- Default blocklist (20+ patterns): `rm -rf`, `rm -r /`, `rmdir /s`, `del /s`, `format C:`, `DROP DATABASE`, `DROP TABLE`, `TRUNCATE TABLE`, `DELETE FROM` (without WHERE), `shutdown`, `reboot`, `mkfs`, `dd if=`, `:(){ :|:& };:` (fork bomb), `chmod -R 777`, `chown -R`, `> /dev/sda`, `wget | sh`, `curl | bash`
- Match strategy: split command on pipes/chains, check first token of each segment against blocklist
- Users extend via settings file with additional patterns in same format
