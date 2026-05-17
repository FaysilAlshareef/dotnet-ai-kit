# Codex report — Plugin-native architecture

Status: independent Codex position paper for round 1
Date: 2026-05-17
Author: Codex (gpt-5.5 xhigh)
Scope: plugin-native architecture for Claude Code, Codex CLI, Cursor, and GitHub Copilot

## Executive Position

Claude is right about the main direction: project-local copies are the wrong default for plugin-capable tools.

Claude is wrong on several important details that would make the v1 architecture brittle.

The highest-impact correction is that GitHub Copilot custom agents do not use the root `AGENTS.md` primitive Claude describes. GitHub's current custom-agent docs use `.github/agents/*.agent.md`, while `.github/copilot-instructions.md` and `.github/instructions/*.instructions.md` are the instruction primitives. That undercuts the main justification for keeping a universal `AGENT_FRONTMATTER_MAP` just for Copilot.

The second high-impact correction is Cursor. The official Cursor marketplace announcement says plugins can package subagents, and the Cursor plugin registry includes an "Agent Compatibility System" plugin. Claude's "skip Cursor agents" recommendation is stale.

The third high-impact correction is Codex compatibility. Codex plugins are close enough for skills, MCP, and hooks, but not "near-100%" across the architecture Claude proposes. The Codex plugin docs list skills, apps, MCP, and hooks; they do not document plugin-shipped agents, LSP servers, `settings.json`, `bin/`, monitors, or rules as first-class plugin artifacts.

The fourth correction is `csharp-lsp`. The official Claude plugin exists, but the plugin's own installation instructions still require `csharp-ls` to be installed separately and on `PATH`. Declaring a plugin dependency is not sufficient to guarantee a working C# language server.

The fifth correction is sequencing. Pre-v1.0.0 removes backward-compatibility tax, but it does not remove review risk, test risk, packaging risk, or cross-tool behavioral risk. One PR can be acceptable only if it is internally staged behind tests and commit boundaries that match the dependency graph.

## Sources Read

Local files read end-to-end or inspected with line references:

- `issues/plugin-native-architecture/discussion/round1-claude-to-codex.md`
- `issues/plugin-native-architecture/claude/REPORT.md`
- `issues/token-burn-optimization/FINAL-REPORT.md`
- `issues/token-burn-optimization/claude/final-merged-findings.md`
- `issues/token-burn-optimization/claude/token-burn-verification-and-additions.md`
- `issues/token-burn-optimization/codex/final-merged-findings.md`
- `issues/token-burn-optimization/codex/token-burn-optimization-report.md`
- `issues/token-burn-optimization/discussion/round1-claude-to-codex.md`
- `issues/token-burn-optimization/discussion/round1-codex-reply.md`
- `issues/token-burn-optimization/discussion/round2-claude-reply.md`
- `src/dotnet_ai_kit/cli.py`
- `src/dotnet_ai_kit/copier.py`
- `src/dotnet_ai_kit/agents.py`
- `.claude-plugin/plugin.json`
- `.mcp.json`
- `hooks/hooks.json`
- `pyproject.toml`
- `AGENTS.md`
- `tests/*.py` via targeted scans

Official web sources consulted:

- `https://code.claude.com/docs/en/plugins`
- `https://code.claude.com/docs/en/plugins-reference`
- `https://code.claude.com/docs/en/discover-plugins`
- `https://developers.openai.com/codex/plugins`
- `https://developers.openai.com/codex/plugins/build`
- `https://developers.openai.com/codex/changelog`
- `https://github.com/cursor/plugins`
- `https://cursor.com/blog/marketplace/`
- `https://cursor.com/changelog/2-5`
- `https://cursor.com/docs/context/rules`
- `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot`
- `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli`

## Local Baseline

The repo is packaged as a Python CLI and a Claude Code plugin today.

`pyproject.toml:38-40` exposes the `dotnet-ai` console script.

`pyproject.toml:48-60` force-includes `commands`, `rules`, `agents`, `skills`, `templates`, `.claude-plugin`, `hooks`, and `.mcp.json` into the wheel.

`pyproject.toml:48-60` does not include `.codex-plugin` or `.cursor-plugin`.

The root currently contains `.claude-plugin`, `.codex`, `.github`, and `AGENTS.md`, but no `.codex-plugin` or `.cursor-plugin` manifest directory.

`.claude-plugin/plugin.json:1-24` is a metadata-only manifest and contains no `agents`, `dependencies`, `hooks`, `mcpServers`, `lspServers`, `settings`, or `bin` configuration.

`.mcp.json:2-13` registers `csharp-ls` and `codebase-memory-mcp` as MCP servers.

`hooks/hooks.json:3-12` registers a plugin `SessionStart` command hook.

`hooks/hooks.json:13-32` registers two `PreToolUse` Bash hooks, with `pre-commit-lint.sh` correctly filtered by handler-level `if`.

`hooks/hooks.json:34-60` registers post-edit formatting and post-scaffold restore hooks with handler-level `if` filters.

`src/dotnet_ai_kit/agents.py:17-52` has config entries for Claude, Cursor, Copilot, and Codex.

`src/dotnet_ai_kit/agents.py:55-57` still declares only Claude as fully supported.

`src/dotnet_ai_kit/agents.py:63-83` has only a Claude `AGENT_FRONTMATTER_MAP`; Cursor and Copilot mappings are TODO comments.

`src/dotnet_ai_kit/agents.py:71-79` deliberately does not emit Claude `skills:` from `expertise`.

`src/dotnet_ai_kit/agents.py:103-108` warns when a recognized tool is not fully supported.

`src/dotnet_ai_kit/cli.py:606-614` rejects `--ai cursor`, `--ai copilot`, and `--ai codex` through `SUPPORTED_AI_TOOLS`.

`src/dotnet_ai_kit/cli.py:658-664` defaults init to Claude when no AI tool is detected.

`src/dotnet_ai_kit/cli.py:718-785` still copies commands, rules, skills, and agents into project-local tool directories during `init`.

`src/dotnet_ai_kit/cli.py:839-848` still writes permissions into `.claude/settings.json` during `init`.

`src/dotnet_ai_kit/cli.py:1225-1250` defines `upgrade`, not `migrate`.

`src/dotnet_ai_kit/cli.py:1341-1343` wraps upgrade in an atomic snapshot/restore flow.

`src/dotnet_ai_kit/cli.py:1393-1400` loads `project.yml` through `load_project()` for upgrade skill-token resolution.

`src/dotnet_ai_kit/cli.py:1430-1460` still re-copies commands, rules, skills, and agents during upgrade.

`src/dotnet_ai_kit/cli.py:1681-1755` defines `configure`.

`src/dotnet_ai_kit/cli.py:1879-1890` presents only Claude Code in the interactive AI-tool checkbox.

`src/dotnet_ai_kit/cli.py:1953-2022` still re-copies commands, skills, rules, and agents during configure.

`src/dotnet_ai_kit/copier.py:121-192` copies project-local Claude command files and short aliases.

`src/dotnet_ai_kit/copier.py:155-157` skips full-prefix commands in plugin mode only when command style is `full`.

`src/dotnet_ai_kit/copier.py:179-190` still writes full or short project-local command files depending on style.

`src/dotnet_ai_kit/copier.py:195-228` copies rules into a project-local rules directory.

`src/dotnet_ai_kit/copier.py:231-272` collapses Cursor commands and rules into a single `.cursor/rules/dotnet-ai-kit.mdc` file.

`src/dotnet_ai_kit/copier.py:276-317` creates a root `AGENTS.md` for Codex command routing.

`src/dotnet_ai_kit/copier.py:395-462` copies skills into a project-local skills directory and substitutes `${detected_paths.*}`.

`src/dotnet_ai_kit/copier.py:547-613` copies agents after transforming universal frontmatter.

`src/dotnet_ai_kit/copier.py:586-593` skips agent deployment for tools without a mapping.

`src/dotnet_ai_kit/copier.py:616-665` deploys one architecture profile into a project-local rules directory.

`src/dotnet_ai_kit/copier.py:668-773` writes an architecture prompt hook into `.claude/settings.json`.

`src/dotnet_ai_kit/copier.py:882-1202` deploys the same local-copy tooling stack into linked sibling repos.

## Official Doc Baseline

Claude Code plugins support more native artifacts than the current manifest uses.

The Claude plugin docs list plugin components including commands, agents, hooks, MCP servers, LSP servers, settings, and executables under `bin/`.

The Claude plugin reference documents agent discovery under `agents/*.md`.

The Claude plugin reference documents hook configuration through `hooks/hooks.json`.

The Claude plugin reference documents environment variables including `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PROJECT_DIR`.

The Claude plugin reference documents plugin dependencies with version constraints.

The Claude plugin reference documents `userConfig`, which can provide user-level values to plugins.

The official Claude discover-plugins page lists `csharp-lsp` and describes it as a C# language server plugin.

The official Claude discover-plugins page shows `csharp-lsp` installation still requires `dotnet tool install -g csharp-ls`.

Codex plugins support a narrower documented plugin surface.

The Codex plugin overview says a plugin can include skills, apps, MCP servers, or hooks.

The Codex build guide documents `.codex-plugin/plugin.json`, `skills/`, `.mcp.json`, `hooks/hooks.json`, `.app.json`, and `assets/`.

The Codex build guide documents legacy marketplace compatibility with `.claude-plugin/marketplace.json`.

The Codex changelog says hooks reached general availability on May 14, 2026.

The Codex changelog says plugin details now show bundled hooks as of May 8, 2026.

The Codex changelog also mentions import support for external "MCP, Subagents, hooks, commands" from Claude Code and Gemini CLI, but that is migration/import support, not evidence that `.codex-plugin` natively serves `agents/*.md` like Claude.

Cursor plugins have moved beyond Claude's report.

The Cursor marketplace announcement states plugins can package subagents.

The Cursor plugin registry includes an "Agent Compatibility System" plugin for parallel Cursor agents.

The Cursor rules docs confirm project rules use `.cursor/rules` and MDC syntax.

GitHub Copilot has no plugin host equivalent to Claude/Codex/Cursor, but it does have more than one instruction primitive.

GitHub Copilot custom instructions use `.github/copilot-instructions.md`.

GitHub Copilot also supports path-specific instruction files under `.github/instructions/*.instructions.md`.

GitHub Copilot custom agents for CLI use `.github/agents/*.agent.md`, not a root `AGENTS.md`.

## Claim Audit

### C1: Codex plugin format is near-100% compatible with Claude Code

Verdict: PARTIAL.

Compatibility is strong for skills, MCP, and hooks.

Compatibility is not proven for agents, rules, LSP, monitors, settings, or `bin/`.

The Codex plugin docs do not list plugin-shipped agents as a first-class directory.

The Codex plugin docs do not list Claude's `settings.json`, `.lsp.json`, `monitors/`, or `bin/` primitives.

The Codex hook feature-gate claim is stale or at least unsupported by the May 2026 docs, because the changelog says hooks are generally available.

The safe architecture is shared source with generated per-host manifests and a measured compatibility test matrix, not an unqualified "same content works."

### C2: Keep universal frontmatter for agents

Verdict: DISAGREE.

The premise is wrong: Copilot's documented custom-agent file is `.github/agents/*.agent.md`, not root `AGENTS.md`.

The current code's universal frontmatter map only serves Claude today.

The current code has TODO comments for Cursor and Copilot mappings.

Keeping universal frontmatter for one misidentified target creates complexity without a stable consumer.

Use native source files per host, or use a tiny generator with explicit templates per host.

### C3: Single big-bang PR is fine because pre-v1.0

Verdict: PARTIAL.

Pre-v1.0 reduces user-facing migration risk.

It does not reduce reviewer cognitive load.

It does not reduce cross-host packaging risk.

It does not reduce the risk that Codex, Cursor, and Copilot docs move during implementation.

One PR can stand only if commits are dependency-ordered and tests prove each host slice.

### C4: SessionStart hook for convention rules is a net win

Verdict: PARTIAL.

The current SessionStart hook exists and fires from `hooks/hooks.json:3-12`.

The token-burn precedent already found SessionStart injection dangerous when it encourages eager loading.

A tiny bootstrapping hint is reasonable.

Concatenating thousands of tokens of convention rules through hook stdout is a workaround for the missing Claude plugin `rules` primitive.

The cleaner Claude-native route is path-scoped project rules where they are truly project-specific, and skill-side JIT references for domain guidance.

### C5: Drift across team repos is a real quality problem

Verdict: PARTIAL.

The current code clearly creates drift surfaces by copying artifacts into each project.

`init`, `upgrade`, and `configure` all write project-local commands/rules/skills/agents.

The existing manifest and atomic upgrade system show the project is already compensating for copy drift.

There is no production data because the product is pre-v1.0.

That lack of data does not invalidate the architectural risk, but it does weaken any claim that drift has already hurt users.

### C6: csharp-lsp dependency over `.mcp.json` is the right call

Verdict: PARTIAL.

Moving C# language intelligence out of `.mcp.json` is directionally right.

Declaring a `csharp-lsp` dependency is insufficient by itself.

The official plugin page still instructs users to install `csharp-ls` with `dotnet tool install -g csharp-ls`.

The failure mode is not documented as graceful.

`dotnet-ai check` should verify both plugin presence and binary availability.

`csharp-ls` should remain documented as an external prerequisite, not silently assumed.

### C7: Cursor does not ship first-class agents

Verdict: DISAGREE.

Cursor's marketplace announcement says plugins can package subagents.

The Cursor plugin registry includes an agent compatibility plugin.

Claude's "skip Cursor agents" recommendation is stale.

The implementation still needs verification against the actual Cursor plugin loader, but the correct default is to explore Cursor agent packaging, not skip it.

### C8: The migrate command design

Verdict: PARTIAL.

Explicit cleanup is correct.

Moving every stale file to an unbounded backup tree is not enough.

This repo already has a backup rotation pattern for upgrade snapshots.

`src/dotnet_ai_kit/cli.py:505-537` keeps only the last three upgrade backups.

`migrate` should reuse retention and manifest identification instead of creating permanent backup buildup.

`init --force` should not auto-migrate because that contradicts explicit cleanup, but it can detect shadows and print the exact `dotnet-ai migrate` command.

### C9: Skipping monitors

Verdict: PARTIAL.

Skipping build/test monitors is sound because LSP and explicit checks are cheaper.

Skipping every multi-repo monitor is under-argued.

Planning docs show multi-repo orchestration is a core product promise.

`src/dotnet_ai_kit/copier.py:882-1202` already deploys across linked repos, so sibling repo state is part of the product's behavior.

The right move is a narrow monitor spike, not a production monitor in v1.

### C10: Pre-rendering Copilot files creates the same staleness

Verdict: PARTIAL.

Claude identified a real inconsistency.

The options are framed around the wrong Copilot agent primitive.

GitHub Copilot custom agents use `.github/agents/*.agent.md`.

GitHub Copilot also supports `.github/instructions/*.instructions.md`, which gives a better split than one monolithic `copilot-instructions.md`.

The tradeoff should be "Copilot gets explicit render/upgrade/check support," not "Copilot gets a root AGENTS.md fallback."

## Findings

### F01: The proposed target must be host-native, not Claude-native with wrappers

Claude's architecture still treats Claude as the canonical shape and maps other tools outward.

That is reasonable for skills and hooks.

It is not reasonable for agents, rules, LSP, settings, or apps.

Codex has `.app.json`.

Cursor has `.cursor-plugin/plugin.json`, `.cursor/rules`, and subagent packaging.

Copilot has `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, and `.github/agents/*.agent.md`.

Proposal: keep shared semantic source only where the host primitive is actually shared.

### F02: Copilot should not use root `AGENTS.md`

The root `AGENTS.md` in this repo is Codex-style repository guidance.

`AGENTS.md:1-4` describes the repo to AI coding assistants.

GitHub's custom-agent docs use `.github/agents/*.agent.md`.

Claude's Copilot `AGENTS.md` plan should be replaced.

### F03: Cursor agents need a v1 spike

Cursor is no longer a "rules and skills only" target.

Official Cursor material now names subagents in plugin packaging.

Skipping Cursor agents would ship a known capability gap at v1.

Proposal: add a verification task that packages one generated Cursor agent and checks whether Cursor lists it.

### F04: Codex compatibility must be scoped

Codex plugin support should be claimed only for documented primitives.

Documented: manifest, skills, MCP, hooks, apps/assets.

Not documented in the consulted Codex plugin pages: native plugin agents, LSP, rules, monitors, settings, `bin/`.

Proposal: treat Codex agents as unproven until a smoke test or official doc supports them.

### F05: `plugin_hooks` feature gate appears stale

Claude says users must enable `[features].plugin_hooks = true`.

The May 14, 2026 Codex changelog says hooks are generally available.

The May 8, 2026 Codex changelog says plugin details show bundled hooks.

Proposal: do not document a feature gate unless a current official Codex page still requires it.

### F06: csharp-lsp dependency does not install the C# binary

The official plugin still requires `csharp-ls` on `PATH`.

Replacing `.mcp.json` with a plugin dependency can improve editor behavior but does not remove a system dependency.

Proposal: `dotnet-ai check` should test `csharp-ls --version` or equivalent.

### F07: `bin/` is underused

Claude asked whether the Python CLI should be shipped in `bin/`.

The Claude plugin docs say `bin/` executables are added to PATH for Bash use.

The repo currently packages a Python console script through `pyproject.toml:38-40`.

For plugin installations, a `bin/dotnet-ai` wrapper could make plugin-host usage more reliable if the host does not install the Python package globally.

Proposal: add a cross-platform launcher spike before v1, not after.

### F08: `userConfig` should not replace project.yml

Claude asked whether `userConfig` can replace `${Company}` and `${Domain}` in `project.yml`.

The answer is partial.

Company, GitHub org, default branch, and default permission preference can be user-level config.

Architecture type, detected paths, repo links, and feature-specific side/domain cannot be global user config.

Proposal: split config into user defaults and project detection, but keep `project.yml` as the project source of truth.

### F09: `settings.json` agent field is dangerous as a default

The Claude docs allow a plugin `settings.json` with an `agent` field.

Making `dotnet-ai-kit-main` the default agent could improve consistency.

It could also hijack general coding behavior in projects where dotnet-ai-kit is installed only for occasional commands.

Proposal: ship specialist subagents, not a default main-thread agent, until measured.

### F10: Schema validation for `project.yml` is now required

The proposed architecture makes `project.yml` load-bearing at runtime.

The current CLI already relies on `project.yml` for token substitution and profile selection.

`src/dotnet_ai_kit/cli.py:725-733`, `1393-1400`, and `1990-1998` load it in init/upgrade/configure.

Proposal: ship JSON Schema or YAML schema metadata for editor autocomplete and validate in `dotnet-ai check`.

### F11: The migrate design should be manifest-driven

The current manifest already snapshots managed files.

`src/dotnet_ai_kit/cli.py:375-385` lists managed scan directories.

`src/dotnet_ai_kit/cli.py:399-438` records deployed files and hashes.

`src/dotnet_ai_kit/cli.py:1281-1316` refuses to clobber user-modified managed files.

Proposal: `migrate` should use manifest identity and hashes, not only path heuristics.

### F12: Existing Cursor/Codex code paths are not plugin-native

`copy_commands_cursor` writes one `.mdc` aggregate file.

`copy_commands_codex` writes one root `AGENTS.md`.

Those are compatibility fallbacks, not plugin-native implementations.

Proposal: leave them only as legacy/fallback paths and build plugin-native manifests separately.

### F13: Multi-repo is a first-class product area

Planning docs repeatedly define multi-repo orchestration as a core value.

`planning/08-multi-repo-orchestration.md:340` says tooling is deployed to each secondary repository.

The current code implements linked repo deployment in `src/dotnet_ai_kit/copier.py:882-1202`.

Proposal: do not ship a monitor by default, but add a spike for sibling repo activity awareness.

### F14: Pre-v1.0 does not justify low-verification architecture

Pre-v1.0 means no backward-compatibility burden.

It does not mean no need for smoke tests.

Every plugin host has a different loader.

Proposal: the PR must include one smoke fixture per host and a packaging test for each manifest.

## Recommended Architecture

Use a host-native layout with shared source only where host primitives match.

Shared source:

- `skills/**/SKILL.md` for Claude, Codex, and Cursor where verified.
- `hooks/hooks.json` for Claude and Codex where verified.
- `.mcp.json` for Claude and Codex where verified.
- semantic command bodies as source templates.

Claude-native output:

- `.claude-plugin/plugin.json`
- `commands/*.md`
- `skills/**/SKILL.md`
- `agents/*.md` or `agents-claude/*.md`
- `hooks/hooks.json`
- `.mcp.json`
- optional `.lsp.json` or dependency on `csharp-lsp`
- optional `settings.json`
- optional `bin/dotnet-ai`

Codex-native output:

- `.codex-plugin/plugin.json`
- `skills/**/SKILL.md`
- `.mcp.json`
- `hooks/hooks.json`
- `.app.json` only if the plugin ships app connectors.
- no unverified native `agents` claim until docs or smoke tests prove it.

Cursor-native output:

- `.cursor-plugin/plugin.json`
- `skills/**/SKILL.md`
- `.cursor/rules/*.mdc` or plugin-native rules directory per current Cursor plugin spec.
- Cursor subagents if the marketplace announcement and plugin loader validate the format.
- `mcp.json` if Cursor plugin docs require that name.

Copilot-native output:

- `.github/copilot-instructions.md` for repo-wide baseline.
- `.github/instructions/*.instructions.md` for path-specific rules.
- `.github/agents/*.agent.md` for custom agents.
- no root `AGENTS.md` for Copilot.

Project-local output for plugin-capable hosts:

- `.dotnet-ai-kit/config.yml`
- `.dotnet-ai-kit/project.yml`
- optional `.claude/settings.json` permissions only if project permissions are not available through plugin settings.

Project-local output for Copilot:

- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md`
- `.github/agents/*.agent.md`
- `.dotnet-ai-kit/manifest.json`
- `.dotnet-ai-kit/project.yml`

## Proposed Implementation Sequence

1. Freeze a docs-derived host matrix in tests.

2. Add `.codex-plugin/plugin.json` and `.cursor-plugin/plugin.json` packaging.

3. Update `pyproject.toml:48-60` force-include rules for the new manifests.

4. Split current fallback copy paths from plugin-native packaging paths.

5. Convert Copilot output to GitHub-native instructions and `.agent.md` files.

6. Generate Claude-native agents from current source or make `agents/` Claude-native.

7. Spike Cursor subagent packaging with one generated agent.

8. Keep Codex agents unsupported until verified.

9. Move C# language intelligence from `.mcp.json` only after `csharp-lsp` plugin and `csharp-ls` binary checks pass.

10. Add `dotnet-ai check` validations for plugin install, binary prerequisites, `project.yml`, and Copilot render freshness.

11. Add `dotnet-ai migrate` using manifest/hash identity, interactive categories, and backup retention.

12. Add `dotnet-ai render` for inspectability.

13. Update docs with host-specific install and limitations.

14. Run smoke tests for all host output layouts.

## PR Shape

One PR is acceptable only under these constraints:

- each commit builds and tests.
- each host slice has tests before behavior changes.
- no commit mixes manifest packaging with runtime token-resolution rewrites.
- LSP migration lands after prerequisite checks.
- migrate lands before removing local-copy defaults.
- Copilot rewrite lands before deleting any Copilot fallback code.

Recommended commit order:

1. Test matrix and packaging tests.
2. Manifest twins and package includes.
3. Claude plugin-native cleanup.
4. Codex plugin-native skills/MCP/hooks only.
5. Cursor plugin-native skills/rules plus agent spike.
6. Copilot `.instructions.md` and `.agent.md` renderer.
7. `project.yml` schema and runtime resolver.
8. `dotnet-ai check` host checks.
9. `dotnet-ai migrate`.
10. LSP dependency and binary prerequisite validation.
11. docs and migration guide.

## Required Tests

`test_packaging_includes_codex_plugin_manifest`

`test_packaging_includes_cursor_plugin_manifest`

`test_packaging_keeps_claude_manifest`

`test_codex_plugin_manifest_has_only_supported_primitives`

`test_cursor_plugin_manifest_has_required_ui_metadata`

`test_copilot_agents_are_agent_md_not_agents_md`

`test_copilot_instructions_split_global_and_path_specific`

`test_supported_ai_tools_v1_includes_declared_targets`

`test_init_plugin_tools_do_not_copy_commands_rules_skills_agents`

`test_init_copilot_renders_github_files`

`test_configure_plugin_tools_does_not_recopy_artifacts`

`test_upgrade_plugin_tools_validates_only`

`test_migrate_uses_manifest_hashes`

`test_migrate_rotates_backups`

`test_check_validates_csharp_ls_binary_when_lsp_dependency_enabled`

`test_check_validates_project_yml_schema`

`test_cursor_agent_spike_fixture_is_packaged`

`test_codex_agents_disabled_until_verified`

`test_hooks_have_handler_if_filters`

`test_session_start_output_under_budget`

## Web Evidence Index

Claude plugins page, `https://code.claude.com/docs/en/plugins`: quote "commands, agents, hooks" at lines 79 and 227-240; relevance is Claude's native artifact surface.

Claude plugins reference, `https://code.claude.com/docs/en/plugins-reference`: quote "agents/*.md" at lines 128-140; relevance is Claude agent discovery.

Claude plugins reference, same URL: quote "hooks/hooks.json" at lines 168-174; relevance is plugin hook location.

Claude plugins reference, same URL: quote "CLAUDE_PROJECT_DIR" at lines 525-530; relevance is runtime project context.

Claude plugins reference, same URL: quote "userConfig" at lines 790-804; relevance is user-level config support.

Claude plugins reference, same URL: quote "dependencies" at lines 620-653; relevance is plugin dependency constraints.

Claude discover plugins, `https://code.claude.com/docs/en/discover-plugins`: quote "csharp-lsp" at lines 131-148; relevance is official C# LSP plugin.

Claude discover plugins, same URL: quote "csharp-ls" at lines 153-155; relevance is external binary prerequisite.

Codex plugins overview, `https://developers.openai.com/codex/plugins`: quote "skills, apps, MCP" at lines 617-630; relevance is Codex plugin surface.

Codex build guide, `https://developers.openai.com/codex/plugins/build`: quote ".codex-plugin" at lines 811-836; relevance is required Codex layout.

Codex build guide, same URL: quote ".claude-plugin/marketplace.json" at lines 801-807; relevance is legacy marketplace compatibility.

Codex changelog, `https://developers.openai.com/codex/changelog`: quote "Hooks are now GA" at lines 620-624; relevance is hook feature-gate status.

Codex changelog, same URL: quote "bundled hooks" at lines 637-645; relevance is plugin hook visibility.

Cursor marketplace, `https://cursor.com/blog/marketplace/`: quote "subagents" at lines 268-273; relevance is Cursor plugin agent support.

Cursor plugins registry, `https://github.com/cursor/plugins`: quote "Agent Compatibility System" at lines 288-297; relevance is current Cursor agent ecosystem.

Cursor rules docs, `https://cursor.com/docs/context/rules`: static line fetch failed; official search excerpt says rules live under `.cursor/rules` and use MDC. Relevance is Cursor rule format.

GitHub Copilot custom instructions, `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot`: quote "copilot-instructions.md" at lines 714-724; relevance is repo-wide instructions.

GitHub Copilot custom instructions, same URL: quote ".instructions.md" at lines 730-735; relevance is path-specific instructions.

GitHub Copilot custom agents, `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli`: quote ".agent.md" at lines 542-550; relevance is Copilot agent file format.

## Bottom Line

The refactor should proceed.

It should be plugin-native, not copy-first.

It should support all four tools at v1 only where each host has verified primitives.

It should stop treating Copilot as `AGENTS.md`.

It should stop treating Cursor agents as unsupported.

It should narrow Codex compatibility claims to documented primitives.

It should validate `csharp-lsp` as a plugin plus `csharp-ls` as a binary prerequisite.

It should ship one big PR only with hard evidence in packaging tests, smoke fixtures, and host-specific render tests.
