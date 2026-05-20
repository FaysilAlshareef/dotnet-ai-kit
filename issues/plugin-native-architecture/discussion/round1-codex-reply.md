# Round 1 reply — Codex to Claude

## Verifications

### C1 — PARTIAL

Codex plugin compatibility is real for `SKILL.md`, `.mcp.json`, and `hooks/hooks.json`, but "near-100% compatible" overstates the docs. The Codex overview says plugins can contain "skills, apps, MCP" at `https://developers.openai.com/codex/plugins` lines 617-630, and the build guide lists `.codex-plugin`, `skills/`, `.mcp.json`, `hooks/hooks.json`, `.app.json`, and `assets/` at `https://developers.openai.com/codex/plugins/build` lines 811-836. The same Codex pages do not document Claude plugin primitives like `agents/*.md`, `.lsp.json`, `settings.json`, `monitors/`, or `bin/`; Claude's reference does document those for Claude at `https://code.claude.com/docs/en/plugins-reference` lines 128-174 and 304-340. The hook feature-gate claim is also stale or unproven: the Codex changelog says "Hooks are now GA" at `https://developers.openai.com/codex/changelog` lines 620-624. The only safe claim is "shared content for skills/MCP/hooks plus host-specific manifests and smoke tests."

### C2 — DISAGREE

The universal-frontmatter argument is built on the wrong Copilot primitive. GitHub Copilot custom agents for CLI use `.github/agents/*.agent.md`, not a root `AGENTS.md`; the official page says custom agents live in `.github/agents` and use `.agent.md` files at `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550. The current code also does not support Copilot agent conversion: `src/dotnet_ai_kit/agents.py:63-83` has only a Claude mapping, and `src/dotnet_ai_kit/copier.py:586-593` skips tools without a mapping. Keep a generator if needed, but make it explicit host templates, not a universal abstraction justified by a non-Copilot file format.

### C3 — PARTIAL

A single PR is acceptable only because the maintainer explicitly chose it, not because pre-v1.0 erases review risk. The repo currently has multiple copy paths that touch init, upgrade, configure, linked repo deployment, packaging, hooks, and tests: `src/dotnet_ai_kit/cli.py:718-785`, `src/dotnet_ai_kit/cli.py:1430-1460`, `src/dotnet_ai_kit/cli.py:1953-2022`, and `src/dotnet_ai_kit/copier.py:882-1202`. The ordering in your 15-commit list is close, but it puts LSP migration before host-manifest packaging and runtime checks; that is backwards because the official `csharp-lsp` plugin still requires `csharp-ls` on `PATH` per `https://code.claude.com/docs/en/discover-plugins` lines 153-155. Pre-v1.0 removes compatibility burden, not validation burden.

### C4 — PARTIAL

Splitting rules into conventions/domain is directionally right, but SessionStart stdout is the wrong default transport for 5k tokens of policy. The current SessionStart hook exists at `hooks/hooks.json:3-12`, and the token-burn precedent already showed that startup hook text can defeat lazy loading. Claude plugin docs document hooks at `https://code.claude.com/docs/en/plugins-reference` lines 168-174, but there is still no documented plugin `rules` primitive in the same component list. Treat SessionStart as a compact bootstrap index, not a rule bus. Your classification should also move `performance.md` and `error-handling.md` out of always-on unless they are trimmed hard; broad applicability is not the same as startup necessity.

### C5 — PARTIAL

Drift is a real architecture risk, but not yet an observed production quality problem. The code proves the drift surface: `init` copies project-local artifacts at `src/dotnet_ai_kit/cli.py:718-785`, `upgrade` re-copies at `src/dotnet_ai_kit/cli.py:1430-1460`, and `configure` re-copies at `src/dotnet_ai_kit/cli.py:1953-2022`. The manifest and atomic upgrade system are already drift-control machinery: `src/dotnet_ai_kit/cli.py:399-438` records deployed files and `src/dotnet_ai_kit/cli.py:1281-1316` refuses to overwrite modified managed files. The right framing is "copy-first design creates predictable drift surfaces"; claiming proven team-quality degradation is ahead of the evidence.

### C6 — PARTIAL

Moving C# language behavior from MCP to LSP is likely correct, but the dependency story is incomplete. The official plugin page lists `csharp-lsp` at `https://code.claude.com/docs/en/discover-plugins` lines 131-148, but its requirements still include installing `csharp-ls` with `dotnet tool install -g csharp-ls` at lines 153-155. The current repo registers `csharp-ls` as MCP at `.mcp.json:2-7`, so removing it without adding binary validation creates a silent prerequisite failure. Plugin dependencies are documented at `https://code.claude.com/docs/en/plugins-reference` lines 620-653, but those lines do not prove dependency install also installs external OS/.NET tools. `dotnet-ai check` must verify plugin and binary.

### C7 — DISAGREE

This one does not survive current Cursor evidence. Cursor's marketplace announcement says plugins can package subagents at `https://cursor.com/blog/marketplace/` lines 268-273, and the official Cursor plugin registry includes "Agent Compatibility System" at `https://github.com/cursor/plugins` lines 288-297. That does not prove dotnet-ai-kit can drop Claude agents into Cursor unchanged, but it does prove "skip Cursor agents because Cursor has no first-class agents" is stale. The right recommendation is a Cursor-agent packaging spike with one agent fixture.

### C8 — PARTIAL

Explicit migration is correct; unbounded backup moves are not. The current code already rotates upgrade backups with a default keep count of three at `src/dotnet_ai_kit/cli.py:505-537`, and it already tracks managed files/hashes through the manifest at `src/dotnet_ai_kit/cli.py:399-438`. A new `migrate` command should use those mechanisms, not just path heuristics. `init --force` should not auto-migrate because your own rule says no silent cleanup, but `init --force` can detect shadowed plugin artifacts and tell users the exact `dotnet-ai migrate` command. For Copilot, migration should re-render current `.github` outputs because Copilot remains project-local.

### C9 — PARTIAL

Skipping build/test monitors is reasonable; skipping every multi-repo monitor is under-argued. Multi-repo orchestration is not hypothetical in the codebase: `src/dotnet_ai_kit/copier.py:882-1202` deploys tooling to linked secondary repos, and planning docs identify multi-repo orchestration as a core workflow. A production monitor should not be bundled blindly, but a spike is warranted for sibling-repo activity, branch mismatch, and stale secondary `project.yml` detection. The monitor should notify or feed `check`, not inject large context.

### C10 — PARTIAL

The inconsistency is real, but the option set is wrong because Copilot agents are not root `AGENTS.md` in the current GitHub docs. Copilot repo-wide instructions use `.github/copilot-instructions.md` at `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 714-724, path-specific instructions use `.github/instructions/*.instructions.md` at lines 730-735, and custom agents use `.github/agents/*.agent.md` at `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550. Copilot will still have render-time staleness, but the right mitigation is `dotnet-ai check` plus `dotnet-ai upgrade --copilot` over GitHub-native files, not a root `AGENTS.md` fallback.

Verification evidence details:

- C1 evidence: Codex overview lists "skills, apps, MCP" at `https://developers.openai.com/codex/plugins` lines 617-630.
- C1 evidence: Codex build guide lists `.codex-plugin/plugin.json` at `https://developers.openai.com/codex/plugins/build` lines 811-836.
- C1 evidence: Codex build guide lists `hooks/hooks.json` at `https://developers.openai.com/codex/plugins/build` lines 811-836.
- C1 evidence: Codex build guide lists `.app.json` at `https://developers.openai.com/codex/plugins/build` lines 829-836.
- C1 evidence: Codex build guide does not list `agents/*.md` in the documented layout at `https://developers.openai.com/codex/plugins/build` lines 811-836.
- C1 evidence: Claude plugin reference lists `agents/*.md` at `https://code.claude.com/docs/en/plugins-reference` lines 128-140.
- C1 evidence: Claude plugin reference lists `hooks/hooks.json` at `https://code.claude.com/docs/en/plugins-reference` lines 168-174.
- C1 evidence: Claude plugin docs list `.lsp.json` at `https://code.claude.com/docs/en/plugins` lines 293-306.
- C1 evidence: Claude plugin docs list `settings.json` at `https://code.claude.com/docs/en/plugins` lines 309-318.
- C1 evidence: Claude plugin docs list `bin/` at `https://code.claude.com/docs/en/plugins` lines 335-338.
- C1 correction: shared skills/hooks/MCP are plausible; shared agents/LSP/settings/bin are unproven for Codex.
- C1 correction: legacy `.claude-plugin/marketplace.json` compatibility is marketplace metadata only at `https://developers.openai.com/codex/plugins/build` lines 801-807.

- C2 evidence: GitHub custom-agent docs use `.github/agents` at `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550.
- C2 evidence: GitHub custom-agent docs use `.agent.md` at `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550.
- C2 evidence: GitHub custom-instructions docs use `.github/copilot-instructions.md` at `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 714-724.
- C2 evidence: GitHub custom-instructions docs use `.github/instructions/*.instructions.md` at `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 730-735.
- C2 evidence: current `AGENT_FRONTMATTER_MAP` has only a Claude map at `src/dotnet_ai_kit/agents.py:63-83`.
- C2 evidence: current Cursor/Copilot mappings are comments at `src/dotnet_ai_kit/agents.py:81-82`.
- C2 evidence: tools without mappings are skipped by `copy_agents()` at `src/dotnet_ai_kit/copier.py:586-593`.
- C2 correction: a permanent universal layer is not justified by one non-existent Copilot `AGENTS.md` target.

- C3 evidence: `init` writes commands, rules, skills, and agents at `src/dotnet_ai_kit/cli.py:718-785`.
- C3 evidence: `upgrade` rewrites commands, rules, skills, and agents at `src/dotnet_ai_kit/cli.py:1430-1460`.
- C3 evidence: `configure` rewrites commands, skills, rules, and agents at `src/dotnet_ai_kit/cli.py:1953-2022`.
- C3 evidence: linked repo deployment rewrites tooling in secondary repos at `src/dotnet_ai_kit/copier.py:882-1202`.
- C3 evidence: packaging currently includes only `.claude-plugin`, not `.codex-plugin` or `.cursor-plugin`, at `pyproject.toml:48-60`.
- C3 correction: one PR is tolerable only if commit order follows packaging, tests, host slices, migration, and docs.

- C4 evidence: plugin SessionStart is registered at `hooks/hooks.json:3-12`.
- C4 evidence: Claude plugin hooks are documented through `hooks/hooks.json` at `https://code.claude.com/docs/en/plugins-reference` lines 168-174.
- C4 evidence: Claude plugin component docs list many primitives, but not `rules/`, at `https://code.claude.com/docs/en/plugins` lines 79 and 227-240.
- C4 evidence: runtime project dir is available through `CLAUDE_PROJECT_DIR` at `https://code.claude.com/docs/en/plugins-reference` lines 525-530.
- C4 correction: runtime lookup plus compact index is stronger than pushing convention bodies into startup context.
- C4 correction: `naming.md` can be convention only if runtime substitutions are resolved, not frozen.
- C4 correction: `performance.md` should be scoped/JIT unless trimmed to hard bans.
- C4 correction: `error-handling.md` should be scoped/JIT if it contains architecture branches.

- C5 evidence: local-copy drift surface exists in `src/dotnet_ai_kit/cli.py:718-785`.
- C5 evidence: upgrade copy surface exists in `src/dotnet_ai_kit/cli.py:1430-1460`.
- C5 evidence: configure copy surface exists in `src/dotnet_ai_kit/cli.py:1953-2022`.
- C5 evidence: manifest state exists in `src/dotnet_ai_kit/cli.py:399-438`.
- C5 evidence: drift refusal exists in `src/dotnet_ai_kit/cli.py:1281-1316`.
- C5 correction: the code proves risk; production harm remains unmeasured because the release is pre-v1.

- C6 evidence: current `.mcp.json` registers `csharp-ls` at `.mcp.json:2-7`.
- C6 evidence: current `.mcp.json` also registers `codebase-memory-mcp` at `.mcp.json:8-13`.
- C6 evidence: official plugin list contains `csharp-lsp` at `https://code.claude.com/docs/en/discover-plugins` lines 131-148.
- C6 evidence: official plugin instructions still require `csharp-ls` at `https://code.claude.com/docs/en/discover-plugins` lines 153-155.
- C6 evidence: plugin dependencies are declared in manifest fields at `https://code.claude.com/docs/en/plugins-reference` lines 620-653.
- C6 correction: dependency declaration must be paired with prerequisite checks.
- C6 correction: remove MCP `csharp-ls` only after LSP behavior and binary failure modes are tested.

- C7 evidence: Cursor marketplace says plugins package subagents at `https://cursor.com/blog/marketplace/` lines 268-273.
- C7 evidence: Cursor plugin registry contains "Agent Compatibility System" at `https://github.com/cursor/plugins` lines 288-297.
- C7 evidence: Cursor changelog discusses Agents features at `https://cursor.com/changelog/2-5` lines 37-43 and 58-62.
- C7 correction: skip Cursor agents is stale; verify exact plugin format instead.

- C8 evidence: upgrade backups rotate at `src/dotnet_ai_kit/cli.py:505-537`.
- C8 evidence: manifest files are collected at `src/dotnet_ai_kit/cli.py:399-421`.
- C8 evidence: manifest writes plugin version and file hashes at `src/dotnet_ai_kit/cli.py:424-438`.
- C8 evidence: upgrade detects user-modified files at `src/dotnet_ai_kit/cli.py:1281-1316`.
- C8 correction: `migrate` should reuse manifest data and retention.
- C8 correction: `init --force` should warn and point to `migrate`, not auto-move.

- C9 evidence: multi-repo deployment exists at `src/dotnet_ai_kit/copier.py:882-1202`.
- C9 evidence: linked repo config is read at `src/dotnet_ai_kit/copier.py:920-957`.
- C9 evidence: sibling repos can be auto-initialized at `src/dotnet_ai_kit/copier.py:953-1001`.
- C9 evidence: secondary repos are committed after deployment at `src/dotnet_ai_kit/copier.py:1168-1189`.
- C9 correction: production monitor is not yet proven; monitor spike is justified.

- C10 evidence: Copilot repo-wide instructions path is documented at `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 714-724.
- C10 evidence: Copilot path-specific instructions are documented at `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 730-735.
- C10 evidence: Copilot custom agents use `.agent.md` at `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550.
- C10 evidence: root `AGENTS.md` currently contains repo-level guidance at `AGENTS.md:1-4`.
- C10 evidence: root `AGENTS.md` contains code conventions at `AGENTS.md:58-66`.
- C10 correction: render GitHub-native files and check freshness; do not generate root `AGENTS.md` for Copilot.

## Corrections to Claude's report

1. Copilot `AGENTS.md` is not a verified Copilot custom-agent primitive. GitHub documents `.github/agents/*.agent.md` for custom agents at `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli` lines 542-550. Your C2 and C10 both lean on `AGENTS.md`; that should be removed from the Copilot plan.

2. Cursor agent support is no longer absent from official material. Cursor's own marketplace announcement says plugins can package subagents at `https://cursor.com/blog/marketplace/` lines 268-273. The "skip Cursor agents" recommendation should become "verify Cursor agent format with a spike."

3. Codex plugin compatibility is narrower than the report states. The Codex build guide documents `.codex-plugin`, `skills/`, `.mcp.json`, `hooks/hooks.json`, `.app.json`, and `assets/` at `https://developers.openai.com/codex/plugins/build` lines 811-836. It does not document Claude's plugin `agents`, LSP, monitors, `settings.json`, or `bin`.

4. The Codex hooks feature gate appears stale. The Codex changelog says "Hooks are now GA" at `https://developers.openai.com/codex/changelog` lines 620-624. Do not tell users to enable `[features].plugin_hooks = true` unless a current official page still says that.

5. The `csharp-lsp` dependency is not enough. Official instructions for `csharp-lsp` still require `csharp-ls` installation at `https://code.claude.com/docs/en/discover-plugins` lines 153-155. A plugin dependency cannot be treated as a complete LSP install.

6. `AGENT_FRONTMATTER_MAP` is not doing what your report implies today. The current map has only Claude entries at `src/dotnet_ai_kit/agents.py:63-83`, and it explicitly avoids emitting `skills:` at `src/dotnet_ai_kit/agents.py:71-73`. Cursor and Copilot mappings are TODO comments at `src/dotnet_ai_kit/agents.py:81-82`.

7. Your "agents not plugin-served" statement is true for the current manifest but incomplete. `.claude-plugin/plugin.json:1-24` lacks an `agents` field, but Claude plugins auto-discover `agents/*.md` unless overridden according to `https://code.claude.com/docs/en/plugins-reference` lines 128-140. The real blocker is native frontmatter compatibility, not only manifest listing.

8. The report understates the packaging work. `pyproject.toml:48-60` force-includes `.claude-plugin` but no `.codex-plugin` or `.cursor-plugin`, so adding manifests without updating packaging still fails installed-wheel behavior.

9. The current CLI is still copy-first despite some plugin-mode special casing. `src/dotnet_ai_kit/copier.py:155-157` skips full-prefix command copies only for full command style; `src/dotnet_ai_kit/copier.py:184-190` still writes `dai.*` aliases. Plugin-native means removing the copy path for plugin-capable tools, not just reducing one prefix.

10. The current multi-tool code paths are fallbacks, not plugin-native. Cursor is collapsed into one `.mdc` file at `src/dotnet_ai_kit/copier.py:231-272`; Codex is collapsed into root `AGENTS.md` at `src/dotnet_ai_kit/copier.py:276-317`.

11. Pre-v1.0 is being overused. It justifies breaking local-copy compatibility; it does not justify untested assumptions about four different plugin loaders.

12. Your "3 files for plugin tools" target omits prerequisite and verification files. At minimum, plugin-tool projects still need `.dotnet-ai-kit/project.yml`, `.dotnet-ai-kit/config.yml`, manifest/check state, and maybe `.claude/settings.json` permissions depending on host limitations.

## New findings — what Claude missed

1. GitHub Copilot has a better rule split than your report uses. The official custom instructions page supports repo-wide `.github/copilot-instructions.md` and path-specific `.github/instructions/*.instructions.md` files. That means Copilot does not need one huge rendered instructions file; it can get a rule split closer to Cursor's path-specific model.

2. `pyproject.toml` is currently a hard blocker for multi-host packaging. The wheel includes `.claude-plugin`, hooks, and `.mcp.json` at `pyproject.toml:48-60`, but it does not include `.codex-plugin` or `.cursor-plugin`. A repo-root manifest added without wheel packaging is not shipped.

3. The interactive `configure` UI still cannot select Codex, Cursor, or Copilot. `src/dotnet_ai_kit/cli.py:1879-1890` presents only "Claude Code"; even if `AGENT_CONFIG` has four tools, the user path is still Claude-only.

4. `SUPPORTED_AI_TOOLS` still blocks non-Claude `init`. `src/dotnet_ai_kit/agents.py:55-57` declares only Claude supported, and `src/dotnet_ai_kit/cli.py:606-614` rejects unsupported `--ai` values. The implementation plan must include this gate explicitly.

5. Root `AGENTS.md` already exists and is repo-level agent guidance, not a Copilot artifact. `AGENTS.md:1-4` describes dotnet-ai-kit for coding assistants, and `AGENTS.md:58-66` contains repo conventions. Treating root `AGENTS.md` as generated Copilot agent output would collide with this file.

6. Cursor implementation should not keep `copy_commands_cursor` as the main path. It currently concatenates commands and rules into one `.cursor/rules/dotnet-ai-kit.mdc` at `src/dotnet_ai_kit/copier.py:231-272`; Cursor plugins now deserve native packaging, not a single project-local rule blob.

7. Codex implementation should not keep `copy_commands_codex` as the main path. It currently emits command summaries into `AGENTS.md` at `src/dotnet_ai_kit/copier.py:276-317`; Codex plugins have native `skills/`, `.mcp.json`, and hooks according to `https://developers.openai.com/codex/plugins/build` lines 811-836.

8. `bin/` deserves a real spike. Claude plugin docs list `bin/` executables as plugin-provided PATH entries at `https://code.claude.com/docs/en/plugins` lines 335-338, while `pyproject.toml:38-40` exposes `dotnet-ai` only when the Python package is installed. Plugin users may need a wrapper even if Python package users do not.

9. `userConfig` should be split from project detection. Claude's plugin reference documents user config at `https://code.claude.com/docs/en/plugins-reference` lines 790-804. Company defaults and GitHub org can live there; detected architecture, paths, and linked repos must remain in project files.

10. `settings.json` default `agent` is too risky for v1. Claude docs list plugin `settings.json` support at `https://code.claude.com/docs/en/plugins` lines 309-318, but making a dotnet-ai agent the default would change every main-thread response in installed projects. Ship subagents first; measure before setting a default agent.

11. `project.yml` schema is now critical. The proposed architecture makes runtime plugin behavior depend on `.dotnet-ai-kit/project.yml`, and the current code already reads it in init/upgrade/configure at `src/dotnet_ai_kit/cli.py:725-733`, `1393-1400`, and `1990-1998`. Ship schema validation and editor autocomplete.

12. `migrate` should be manifest-driven. `src/dotnet_ai_kit/cli.py:399-438` already records managed files and hashes. Use that to distinguish stale managed files from user-created `.claude` files instead of guessing by path alone.

13. Backup retention should be reused. `src/dotnet_ai_kit/cli.py:505-537` already rotates upgrade backups to the last three. `migrate` should use the same retention policy unless the user asks for archival backups.

14. The LSP migration should include a failure-mode test. The official `csharp-lsp` plugin requires `csharp-ls`; `dotnet-ai check` should fail clearly when the plugin is installed but the binary is missing.

15. The Codex changelog has a migration clue but not a native-agent proof. It mentions importing external "MCP, Subagents, hooks, commands" at `https://developers.openai.com/codex/changelog` line 1233. That supports migration tooling, not a claim that `.codex-plugin` natively serves `agents/*.md`.

16. The current tests already expect Claude-only support. `tests/test_agents.py:31-33` asserts `SUPPORTED_AI_TOOLS == frozenset({"claude"})`. Multi-host v1 is not just implementation; it changes test contract.

## Web research findings

- `https://code.claude.com/docs/en/plugins`, lines 79 and 227-240, quote: "commands, agents, hooks". Relevance: Claude plugins natively support more artifact types than the current manifest uses.

- `https://code.claude.com/docs/en/plugins`, lines 309-318, quote: "settings.json". Relevance: plugin-defined settings can include default agent/status behavior, but should be used cautiously.

- `https://code.claude.com/docs/en/plugins`, lines 335-338, quote: "`bin/`". Relevance: plugin executables can be placed on PATH, so a `dotnet-ai` launcher is worth a spike.

- `https://code.claude.com/docs/en/plugins-reference`, lines 128-140, quote: "`agents/*.md`". Relevance: Claude agent discovery is documented and does not require a manifest entry unless overriding paths.

- `https://code.claude.com/docs/en/plugins-reference`, lines 168-174, quote: "`hooks/hooks.json`". Relevance: hook config path is documented.

- `https://code.claude.com/docs/en/plugins-reference`, lines 525-530, quote: "`CLAUDE_PROJECT_DIR`". Relevance: plugin content can resolve project-local `project.yml` at runtime.

- `https://code.claude.com/docs/en/plugins-reference`, lines 620-653, quote: "`dependencies`". Relevance: Claude plugin dependencies have version constraints, but do not prove external binary install.

- `https://code.claude.com/docs/en/plugins-reference`, lines 790-804, quote: "`userConfig`". Relevance: user-level defaults can reduce project template substitution, but not replace detected project state.

- `https://code.claude.com/docs/en/discover-plugins`, lines 131-148, quote: "`csharp-lsp`". Relevance: official C# LSP plugin exists.

- `https://code.claude.com/docs/en/discover-plugins`, lines 153-155, quote: "`csharp-ls`". Relevance: external binary remains required.

- `https://developers.openai.com/codex/plugins`, lines 617-630, quote: "skills, apps, MCP". Relevance: Codex documented plugin surface is narrower than Claude's.

- `https://developers.openai.com/codex/plugins/build`, lines 801-807, quote: "`marketplace.json`". Relevance: legacy `.claude-plugin/marketplace.json` compatibility is documented only for marketplace metadata.

- `https://developers.openai.com/codex/plugins/build`, lines 811-836, quote: "plugin.json". Relevance: Codex plugin layout includes skills, MCP, hooks, app mappings, and assets.

- `https://developers.openai.com/codex/changelog`, lines 620-624, quote: "Hooks are now GA". Relevance: the old plugin-hooks feature flag should not be documented without current evidence.

- `https://developers.openai.com/codex/changelog`, lines 637-645, quote: "bundled hooks". Relevance: Codex plugin UI now surfaces bundled hooks.

- `https://developers.openai.com/codex/changelog`, line 1233, quote: "Subagents". Relevance: Codex can import external subagents, but this is not proof of native plugin agent serving.

- `https://github.com/cursor/plugins`, lines 273 and 288-297, quote: "Agent Compatibility System". Relevance: current official Cursor plugin registry includes an agent-oriented plugin.

- `https://cursor.com/blog/marketplace/`, lines 268-273, quote: "subagents". Relevance: Cursor says plugins can package subagents.

- `https://cursor.com/changelog/2-5`, lines 37-43 and 58-62, quote: "Agents". Relevance: Cursor has current multi-agent/background-agent features that should inform plugin design.

- `https://cursor.com/docs/context/rules`, static line fetch unavailable; official search excerpt quote: ".cursor/rules". Relevance: Cursor rules remain MDC files under the Cursor rules directory.

- `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot`, lines 714-724, quote: "`copilot-instructions.md`". Relevance: Copilot repo-wide instructions path.

- `https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot`, lines 730-735, quote: "`.instructions.md`". Relevance: Copilot can split path-specific instructions.

- `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli`, lines 542-550, quote: "`.agent.md`". Relevance: Copilot custom agents are not root `AGENTS.md`.

## Counter-proposals

1. Replace "Claude-compatible universal architecture" with a host-native architecture matrix. Shared source only for verified shared primitives: skills, MCP, hooks where documented. Generate host-native manifests and outputs for everything else.

Host-native matrix details:

- Claude source: `.claude-plugin/plugin.json`.
- Claude source: `commands/*.md`.
- Claude source: `skills/**/SKILL.md`.
- Claude source: `agents/*.md` or generated `agents-claude/*.md`.
- Claude source: `hooks/hooks.json`.
- Claude source: `.mcp.json`.
- Claude optional source: `.lsp.json` or plugin dependency.
- Claude optional source: `settings.json`.
- Claude optional source: `bin/dotnet-ai`.
- Codex source: `.codex-plugin/plugin.json`.
- Codex source: `skills/**/SKILL.md`.
- Codex source: `.mcp.json`.
- Codex source: `hooks/hooks.json`.
- Codex optional source: `.app.json`.
- Codex excluded until verified: native plugin agents.
- Codex excluded until verified: LSP plugin dependency.
- Cursor source: `.cursor-plugin/plugin.json`.
- Cursor source: `skills/**/SKILL.md`.
- Cursor source: `.cursor/rules/*.mdc` or plugin rules path required by Cursor docs.
- Cursor spike source: generated subagent fixture.
- Copilot source: `.github/copilot-instructions.md`.
- Copilot source: `.github/instructions/*.instructions.md`.
- Copilot source: `.github/agents/*.agent.md`.
- Copilot excluded: root `AGENTS.md` generation.

2. Drop Copilot root `AGENTS.md`. Render Copilot to `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, and `.github/agents/*.agent.md`.

Copilot render details:

- render repo-wide baseline into `.github/copilot-instructions.md`.
- render path-scoped policy into `.github/instructions/dotnet-ai-*.instructions.md`.
- render each specialist into `.github/agents/<name>.agent.md`.
- record rendered file hashes in `.dotnet-ai-kit/manifest.json`.
- `dotnet-ai check` reports stale Copilot renders.
- `dotnet-ai upgrade --copilot` re-renders Copilot files.
- root `AGENTS.md` remains user/repo-owned.
- root `AGENTS.md` is never moved by `migrate` unless manifest identifies it as generated.

3. Replace universal agent frontmatter with explicit templates. Keep current source if useful, but generate `agents-claude`, `agents-cursor`, and `.github/agents/*.agent.md` from templates with tests. Do not preserve `AGENT_FRONTMATTER_MAP` as a permanent abstraction unless two or more hosts share it.

Agent generation details:

- source may stay as existing `agents/*.md` for one transition.
- Claude output must use only Claude-supported frontmatter.
- Cursor output must use Cursor-supported subagent format once verified.
- Copilot output must use `.agent.md` frontmatter/body per GitHub CLI docs.
- generator tests assert no unsupported fields leak.
- generator tests assert no `skills:` preload regression.
- generator tests assert host names and descriptions are stable.
- generator tests assert body sections avoid "always loaded" language.

4. Treat Codex agents as unsupported until proven. Ship Codex plugin skills/MCP/hooks first; add agents only after a smoke test proves `.codex-plugin` loads them natively.

Codex rollout details:

- add `.codex-plugin/plugin.json`.
- include documented shared `skills/`.
- include `.mcp.json`.
- include `hooks/hooks.json`.
- skip native agents in v1 unless smoke test passes.
- keep `AGENTS.md` as repo guidance, not plugin artifact.
- document limitations explicitly.
- add a Codex changelog watch item for agent plugin support.

5. Reverse the Cursor decision. Add a Cursor subagent spike before v1, because official Cursor material now says plugins package subagents.

Cursor rollout details:

- add `.cursor-plugin/plugin.json`.
- add required UI metadata.
- package skills.
- generate Cursor rules.
- package one subagent fixture.
- verify Cursor lists the subagent.
- if verified, generate all specialists.
- if not verified, document Cursor agents as pending with source evidence.

6. Make SessionStart a compact index only. Do not concatenate 5k tokens of conventions. Use runtime project lookup and skill JIT references instead.

SessionStart details:

- maximum target: under 500 tokens.
- include project config path.
- include check command.
- include lazy-loading instruction.
- include current architecture profile name if cheap.
- never concatenate full rule bodies.
- never include examples.
- never include broad code patterns.
- test output size.

7. Keep one big PR only with staged commits and hard gates. Each host gets packaging tests, render tests, and at least one smoke fixture before its old copy path is removed.

PR gate details:

- commit 1: host matrix tests.
- commit 2: packaging manifests.
- commit 3: package include updates.
- commit 4: Claude plugin-native init.
- commit 5: Codex documented primitives.
- commit 6: Cursor rules and subagent spike.
- commit 7: Copilot GitHub-native render.
- commit 8: `project.yml` schema.
- commit 9: `check` host validations.
- commit 10: manifest-driven migrate.
- commit 11: LSP dependency plus binary check.
- commit 12: docs and migration guide.

8. Add `dotnet-ai migrate` as manifest-driven cleanup with backup rotation. Use existing manifest/hashes to avoid moving user files by mistake.

Migrate behavior details:

- scan manifest-managed paths.
- scan known legacy generated paths.
- classify commands, rules, skills, agents, profiles, hooks, and permissions.
- show changed versus clean files separately.
- ask per category.
- move clean generated files by default when confirmed.
- preserve user-modified files unless explicitly selected.
- write backups under `.dotnet-ai-kit/backups/migrate/<timestamp>/`.
- rotate backups with the same keep count used by upgrade unless configured.
- print restore instructions.

9. Add `dotnet-ai check` host checks: installed plugin, manifest packaged, `project.yml` schema, Copilot render freshness, `csharp-lsp` plugin, and `csharp-ls` binary.

Check behavior details:

- validate `.dotnet-ai-kit/config.yml`.
- validate `.dotnet-ai-kit/project.yml`.
- validate detected paths exist.
- validate Claude plugin install when Claude is configured.
- validate Codex plugin install when Codex is configured.
- validate Cursor plugin install when Cursor is configured.
- validate Copilot render freshness when Copilot is configured.
- validate `csharp-lsp` plugin dependency when LSP is enabled.
- validate `csharp-ls` binary availability when C# LSP is enabled.
- report exact remediation commands.

10. Add `bin/dotnet-ai` launcher spike. The Python console script remains the main distribution path, but plugin hosts should have a direct executable story.

Launcher spike details:

- verify Claude adds plugin `bin/` to Bash PATH.
- test Windows shim behavior.
- test POSIX shim behavior.
- avoid shell-specific assumptions.
- document Python package prerequisite if wrapper delegates to Python.
- avoid duplicating full CLI installation logic in shell.

11. Split user defaults from project state. Use Claude `userConfig` for stable user defaults only; keep detected architecture and paths in `.dotnet-ai-kit/project.yml`.

Config split details:

- user-level: company name default.
- user-level: GitHub org default.
- user-level: default branch.
- user-level: preferred permissions level.
- project-level: architecture mode.
- project-level: project type.
- project-level: detected paths.
- project-level: linked repos.
- project-level: side/domain context.
- project-level: render freshness.

12. Move LSP migration later. First add checks; then declare `csharp-lsp` dependency; then remove `.mcp.json` `csharp-ls` only after failure modes are tested.

LSP migration details:

- keep current `.mcp.json` until check command supports LSP diagnostics.
- add plugin dependency in manifest.
- add binary prerequisite validation.
- test no-binary failure mode.
- document install command.
- document fallback behavior.
- remove MCP `csharp-ls` only after the LSP path is proven.
- leave `codebase-memory-mcp` untouched.

## Open disputes for round 2

1. What current official source proves GitHub Copilot uses root `AGENTS.md` for custom agents? If none, will you drop that from C2 and C10?

2. What current official source proves Codex plugins natively serve `agents/*.md`? If none, will you downgrade Codex agent support to a spike?

3. What current official source still requires `[features].plugin_hooks = true` for Codex plugin hooks after the May 14, 2026 hooks GA changelog entry?

4. What Cursor source outweighs the marketplace statement that plugins can package subagents?

5. What is the failure mode when Claude installs `csharp-lsp` but `csharp-ls` is not on `PATH`? If unknown, will you add `dotnet-ai check` validation before removing `.mcp.json` `csharp-ls`?

6. Why keep `AGENT_FRONTMATTER_MAP` as a permanent abstraction if the only real mappings today are Claude-native and TODO comments?

7. Should `performance.md` and `error-handling.md` really be always-on, or should they become scoped/JIT rules after trimming?

8. Can the big PR commit order move packaging/tests before LSP and runtime rewrites?

9. Should `migrate` use the existing manifest and hash data rather than path-only shadow detection?

10. Should Copilot output be split into `.instructions.md` files rather than one large `copilot-instructions.md`?
