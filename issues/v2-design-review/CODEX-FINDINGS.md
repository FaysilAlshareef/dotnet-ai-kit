# Codex Findings: v2 Design Review

Date: 2026-05-30

## Verdict

**PROCEED WITH CHANGES.**

The v2 direction is responding to real defects. The rule-delivery bug is real, command duplication is real, the agent artifact pipeline is drifting, and the current test/budget gates have blind spots. A single-source artifact model with deterministic projections is the right center of gravity.

The current plan still overreaches. It bundles an urgent artifact/rule-delivery repair with a full .NET 10 clean/hexagonal rewrite, per-RID Native AOT ambitions, cross-tool capability claims that are not all independently verified, and new domain expansion work. The highest-confidence path is to ship the artifact/projection/rule-delivery fixes first, keep the CLI rewrite behind a contract suite, and mark host features as GA, preview, or unverified instead of treating them as parity.

## Claim Verification Table

| Claim | Status | Evidence | Notes |
|---|---:|---|---|
| Claude/Codex/Cursor plugin-native hosts do not go through the `copy_rules(...)` fallback branch. | **Confirmed** | `src/dotnet_ai_kit/cli.py:149`, `src/dotnet_ai_kit/cli.py:1281-1334` | `PLUGIN_NATIVE_HOSTS = {"claude", "codex", "cursor"}` and `copy_rules(...)` is only reached in the fallback branch. |
| `ClaudeHost.write_per_solution_files(...)` writes only `.claude/settings.json`. | **Confirmed** | `src/dotnet_ai_kit/hosts/claude.py:110-130` | The method docstring and body only describe/write settings; no rules, commands, skills, or agents. |
| Field investigation corroborates the rule-enforcement gap. | **Confirmed, with updated caveat** | `issues/rule-enforcement-gap/REPORT.md:11-16`, `issues/rule-enforcement-gap/REPORT.md:187-198`, `issues/rule-enforcement-gap/RESEARCH-2-workflows-and-tooling.md:145-152` | The original finding is materially correct, but the newer research adds channels such as forced output styles and notes path-scoped rules load on Read, not Write. |
| 17 of 27 commands have the bounded-skill-selection boilerplate. | **Confirmed** | `commands/` has 27 files; `rg "Bounded skill selection (FR-012)" commands` returns 17 files | The duplication is large enough to justify a fragment/projection source. |
| Agent counts drift across sources. | **Confirmed** | `agents-source/` has 14 files; `agents-claude/` has 13 files; `.claude-plugin/plugin.json` has 13 entries; `.codex-plugin/plugin.json` and `.cursor-plugin/plugin.json` describe 14 | The excluded file is a spike fixture in `agents-source/dotnet-ai-architect.md`. |
| The spike fixture can leak into generated Codex/Copilot agents. | **Confirmed** | `src/dotnet_ai_kit/hosts/codex.py:141-154`, `src/dotnet_ai_kit/hosts/copilot.py:259-263` | Both hosts iterate `agents-source/*.md` without excluding the fixture. |
| System.CommandLine 2.0.8 is a stable package choice. | **Confirmed, time-sensitive** | [NuGet System.CommandLine](https://www.nuget.org/packages/System.CommandLine/) | The package exists as stable 2.x; recheck immediately before implementation because 3.x previews may move. |
| Spectre.Console.Cli is Native AOT-hostile. | **Confirmed** | [Spectre.Console source](https://github.com/spectreconsole/spectre.console/blob/main/src/Spectre.Console.Cli/CommandApp.cs) | The CLI layer marks core APIs with dynamic-code requirements; using `Spectre.Console` for output is different from using `Spectre.Console.Cli` for command dispatch. |
| Native AOT cross-OS compilation is unsupported. | **Confirmed** | [Microsoft Native AOT cross-compilation docs](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/cross-compile) | Cross-architecture within an OS family is supported in some cases; Linux-to-Windows or Windows-to-Linux AOT publishing is not. |
| YamlDotNet needs a static generator for AOT. | **Partially confirmed / overstated** | [Vecc.YamlDotNet.Analyzers.StaticGenerator](https://www.nuget.org/packages/Vecc.YamlDotNet.Analyzers.StaticGenerator) | True for reflection-free typed serialization/deserialization. Not proven necessary if v2 only parses simple frontmatter maps or moves tool config to JSON. Requires a spike. |
| Microsoft.Extensions.AI is a viable .NET package family. | **Confirmed, time-sensitive** | [NuGet Microsoft.Extensions.AI](https://www.nuget.org/packages/Microsoft.Extensions.AI/) | The package is GA on NuGet. It should not become a core dependency unless the CLI actually needs provider abstraction. |
| Claude custom slash commands have been merged into skills. | **Confirmed** | [Claude Code slash commands docs](https://code.claude.com/docs/en/slash-commands) | Existing custom commands still work, but new Claude authoring should bias toward skills. |
| Claude hooks can inject context, deny tools, and block Stop/SubagentStop. | **Confirmed for Claude** | [Claude Code hooks docs](https://code.claude.com/docs/en/hooks) | This does not prove equivalent hook semantics for Cursor, Codex, Copilot CLI, or VS Code. |
| VS Code/Copilot can consume Claude-style agent plugins. | **Confirmed with preview/platform caveat** | [VS Code agent plugin docs](https://code.visualstudio.com/docs/copilot/customization/agent-plugins) | This supports the `.claude-plugin` bridge in VS Code. It does not automatically cover GitHub-hosted Copilot coding agent or all Copilot surfaces. |
| `.agents/skills/` is read uniformly by Cursor, Codex, and Copilot. | **Unconfirmed / partial** | [OpenAI Codex skills docs](https://developers.openai.com/codex/skills), [Cursor rules docs](https://cursor.com/docs/context/rules), [VS Code agent plugin docs](https://code.visualstudio.com/docs/copilot/customization/agent-plugins) | Skill support is real in some tools, but the exact shared `.agents/skills` contract was not independently verified across all named hosts. Treat as an experiment until smoke-tested. |
| Cursor rules use `.cursor/rules/*.mdc` with path/glob metadata. | **Confirmed** | [Cursor rules docs](https://cursor.com/docs/context/rules) | This supports keeping a Cursor-specific rule projection, not assuming Claude rule files work everywhere. |
| MediatR has a commercial license model in current major versions. | **Confirmed with version caveat** | [MediatR repository](https://github.com/jbogard/MediatR), [Lucky Penny Software license page](https://automapper.io/) | The concern applies to current commercial-license-key versions such as MediatR 13+. Earlier versions remain a different licensing decision. |
| AutoMapper has a commercial license model in current major versions. | **Confirmed with version caveat** | [AutoMapper license page](https://automapper.io/), [AutoMapper 15 upgrade guide](https://docs.automapper.io/en/stable/15.0-Upgrade-Guide.html) | The current major-version licensing issue is real; v2 should prefer manual mapping in generated code unless users opt in. |
| MassTransit v9 is moving to commercial source-available licensing. | **Confirmed with version caveat** | [MassTransit docs](https://masstransit.io/) | v8 remains Apache 2.0; v9 policy and free-use thresholds need explicit generated-code guidance. |
| Mediator and Wolverine are plausible alternatives. | **Confirmed with architectural caveat** | [Mediator.SourceGenerator NuGet](https://www.nuget.org/packages/Mediator.SourceGenerator/), [Mediator GitHub](https://github.com/martinothamar/Mediator), [Wolverine docs](https://wolverine.netlify.app/) | Alternatives exist, but v2 should not force a replacement into every template without measuring generated-code complexity and user expectations. |

## Findings By Severity

### Critical

1. **The plan conflates an urgent artifact/rule fix with a full CLI rewrite.**

   `planning/20-rewrite-strategy-net10.md:24-30` says the CLI is mature and the real problem is the content layer. The same document says not to rewrite from scratch and not to start .NET before the current artifact bugs and Python-host refactor are done (`planning/20-rewrite-strategy-net10.md:309-314`). Later docs reverse that into a full .NET 10 rewrite and re-authoring plan (`planning/21-v2-architecture-blueprint.md:6`, `planning/25-v2-requirements.md:44-49`).

   This is the central design risk. The most valuable work is not language migration; it is deterministic artifact projection, rule delivery, host capability contracts, and acceptance tests. A rewrite should be a later track gated by black-box compatibility tests against v1 behavior.

   **Recommendation:** Define v2.0 as artifact/projection/rule-delivery repair. Move the .NET CLI port to v2.x or a parallel spike. Before rewriting, freeze a contract suite that covers current init outputs, host manifests, command/skill projections, rule projections, and permission config behavior.

2. **Cross-tool platform parity is claimed more strongly than the evidence supports.**

   The blueprint says the same skill/resource model works across Claude, Codex, Cursor, and Copilot (`planning/21-v2-architecture-blueprint.md:86`, `planning/21-v2-architecture-blueprint.md:179-185`). The requirements make this part of the product contract (`planning/25-v2-requirements.md:35-40`, `planning/25-v2-requirements.md:90-96`). Independent verification supports some pieces: Claude skills/commands, Claude hooks, Cursor `.mdc` rules, Codex skills, and VS Code agent plugins. It does not prove a uniform `.agents/skills` or hook model across all hosts.

   **Recommendation:** Add a host capability matrix with `GA`, `Preview`, `Experimental`, and `Not supported`. Every projected artifact should name the capability it depends on. Each host needs a smoke test that installs a generated project and proves the target tool can discover the artifact.

3. **The enforcement tier model is Claude-specific but is written like a universal contract.**

   `planning/24-v2-selector-gates-lifecycle-multirepo.md:28-45` defines tiers using Claude-specific mechanisms such as `PreToolUse`, `permissionDecision: deny`, `Stop`, and `SubagentStop`. `planning/25-v2-requirements.md:100-105` makes the gates sound like v2-wide requirements. That is defensible for Claude, but not proven for Cursor, Codex, Copilot CLI, or VS Code.

   **Recommendation:** Scope T2/T4 to Claude where those semantics are verified. For other hosts, define explicit fallbacks: analyzer/CI gates, generated `/verify` commands, static rule projection, and host-native rule systems. Do not claim Stop-level enforcement unless the host can actually block completion.

4. **The real rule-delivery bug should be fixed before the rewrite.**

   The bug is not speculative. Plugin-native hosts skip the rule-copy fallback, and Claude per-solution install writes only settings. The rule-enforcement report shows the behavioral consequence. Waiting for a full v2 rewrite prolongs a live correctness problem.

   **Recommendation:** Ship a v1 hotfix that writes `.claude/rules` or the current recommended forced output-style channel, generates a hook/analyzer where needed, and initializes secondary repos consistently. Then preserve those outputs as v2 contract tests.

### High

1. **The command count and lifecycle scope are internally inconsistent.**

   `planning/23-v2-artifact-catalog.md:7` says 32 commands, described as 27 existing plus 5 additions. `planning/24-v2-selector-gates-lifecycle-multirepo.md:68-87` says add four commands and consider `fix`. `planning/24-v2-selector-gates-lifecycle-multirepo.md:119` says 31 commands. `planning/25-v2-requirements.md:52-86` includes `fix` and says all 32 commands include "the 4 new ones."

   **Recommendation:** Decide whether `fix` is in v2.0. Then update the strategy, catalog, lifecycle, and requirements docs to one number and one list.

2. **The skill-resource model is directionally right but over-normalized.**

   Claude has moved custom commands toward skills, so authoring command-like artifacts as skills is plausible for Claude. But `planning/21-v2-architecture-blueprint.md:86` goes further by stating agents and commands cannot bundle resources and must reference skills. That is a host-model assumption, not a universal law.

   **Recommendation:** Keep `SkillDefinition` as the resource-bearing unit, but introduce a neutral `WorkflowDefinition` or `PromptArtifact` for commands/agents/rules. Let each host projection choose whether the artifact becomes a skill, slash command, rule, agent prompt, or manifest entry.

3. **Selector quality has no credible oracle yet.**

   `planning/24-v2-selector-gates-lifecycle-multirepo.md:10-24` proposes a selector model and `planning/24-v2-selector-gates-lifecycle-multirepo.md:49-61` argues token quality is cheap when deterministic. The missing part is the measured selection oracle. With roughly 160 skills after expansion, the proposed 20 queries per skill and repeated runs become a large, brittle evaluation surface.

   **Recommendation:** Start with ambiguous clusters: mediator, CQRS, eventing, testing, architecture, gateway/control panel. Add curated queries and expected top-k skills for those clusters first. Do not gate every skill until the harness proves useful and stable.

4. **Multi-repo awareness does not yet prove contract correctness.**

   The mechanisms in `planning/24-v2-selector-gates-lifecycle-multirepo.md:91-109` mostly prove that a feature brief exists and sibling repos can be discovered. That does not prove event schemas, proto contracts, version compatibility, or producer/consumer drift.

   **Recommendation:** Add contract artifacts: event schema catalog entries, proto/gRPC compatibility checks, generated expected-consumer lists, and per-repo contract tests. A feature brief is coordination metadata, not a correctness gate.

5. **Native AOT and per-RID distribution add operational risk without clear user value for v2.0.**

   `planning/20-rewrite-strategy-net10.md:231-239` and `planning/25-v2-requirements.md:44-49` put Native AOT into the core stack. AOT raises serializer, reflection, plugin discovery, and CI-matrix costs. Microsoft documents that cross-OS Native AOT publishing is not supported, so release engineering must build per OS.

   **Recommendation:** Ship a framework-dependent `dotnet tool` first. Add Native AOT only after the CLI has no trim warnings, serializer choices are proven, and release automation can build all target OS/RID combinations.

6. **The licensing response is correct in spirit but too blunt for generated code.**

   The plan correctly flags MediatR, AutoMapper, and MassTransit licensing changes (`planning/21-v2-architecture-blueprint.md:261-263`, `planning/23-v2-artifact-catalog.md:175`, `planning/23-v2-artifact-catalog.md:184`, `planning/23-v2-artifact-catalog.md:227`, `planning/23-v2-artifact-catalog.md:235`, `planning/23-v2-artifact-catalog.md:248`, `planning/23-v2-artifact-catalog.md:266`). But "replace with Mediator/Wolverine" is not always the right default. Some templates can avoid mediation entirely; most mapping can be manual.

   **Recommendation:** Make the default generated code license-light: manual mapping, explicit interface boundaries, no commercial packages by default. Offer MediatR, AutoMapper, and MassTransit as opt-in profiles with version and license notes.

### Medium

1. **Clean/hexagonal layering is probably heavier than the tool needs.**

   The proposed `Core`, `Application`, `Infrastructure`, `Hosts`, `Cli`, and `Analyzers` layout (`planning/21-v2-architecture-blueprint.md:193-231`) is service-shaped. This project is primarily a file projection and validation CLI. Too much layering will make simple artifact transforms harder to follow.

   **Recommendation:** Keep ports for real volatility: filesystem, process execution, package discovery, host rendering, and external tool invocation. Avoid abstracting simple manifest records and projection functions behind service layers until duplication proves the need.

2. **The YamlDotNet static-generator decision needs a spike.**

   `planning/22-v2-project-structure.md:252-253` prescribes STJ source generation and YamlDotNet static generation. That may be right for typed YAML, but skill frontmatter could be parsed as simple scalar maps or moved to JSON manifests.

   **Recommendation:** Spike three cases before locking the dependency: simple frontmatter parser, YamlDotNet static generator, and JSON sidecar manifests. Measure AOT/trimming, diagnostics, and authoring ergonomics.

3. **Domain expansion distracts from the product fix.**

   `planning/23-v2-artifact-catalog.md:332-334` adds mediator migration and MassTransit-related skills, and the broader plan contemplates more domain skills. These are useful later, but they increase selector load and authoring burden while the projection engine is still unsettled.

   **Recommendation:** Freeze the corpus except for skills required to remove risky licensed defaults and repair current defects. Add new domain packs after the projection/test harness is green.

4. **Stop-hook build/test enforcement can create false blockers.**

   `planning/24-v2-selector-gates-lifecycle-multirepo.md:28-45` treats build/test/analyzer runs as enforcement. That is valuable in CI or explicit `/verify`; it can be hostile as an automatic Stop hook when a repo has known baseline failures or when the user is making a narrow edit.

   **Recommendation:** Scope stop enforcement by touched files, selected task type, and known baseline. Expensive tests should require an explicit command or a host-supported consent pattern.

5. **Planning documents contain stale or non-generated metrics.**

   `planning/20-rewrite-strategy-net10.md:20` says 739 `def test_` across 130 files; the current repo has 739 test functions across 141 files. `planning/25-v2-requirements.md:10` references 717 tests.

   **Recommendation:** Avoid exact test counts in hand-authored strategy docs, or generate them in a checked report during planning.

6. **Budget tests no longer cover the rule files they claim to cover.**

   `tests/test_budgets.py:9-15` includes a `rules/*.md` budget, but current rules are nested under `rules/conventions` and `rules/domain`. The `_files("rules/*.md")` scan at `tests/test_budgets.py:31-37` misses them.

   **Recommendation:** Update the budget test to scan `rules/**/*.md` and add separate budgets for conventions and path-scoped rules if needed.

### Low

1. **Command naming still has friction.**

   The proposed lifecycle adds `review`, `verify`, `checklist`, and possibly `fix`. `planning/24-v2-selector-gates-lifecycle-multirepo.md:68-87` should define aliases carefully so `check`, `checklist`, `analyze`, and `verify` do not overlap.

2. **`learn` versus `constitution` needs versioning semantics.**

   Splitting knowledge capture from constitutional rules is sensible, but the plan should define who can promote learned facts into enforceable policy and how rule changes are versioned.

3. **`force-for-plugin` output style is not fully reflected in the v2 enforcement design.**

   The later rule-gap research identifies forced output styles as part of the current Claude plugin channel. The v2 docs mostly talk about `.claude/rules` and hooks. That may miss the best immediate Claude-native delivery path.

4. **Commands still contain host-specific path assumptions.**

   Several commands reference `agents/<role>.md`, while Claude uses `agents-claude/*.md` in the plugin manifest. This is exactly the kind of drift a projection model should remove.

5. **Copilot plugin support needs variable/path auditing.**

   If `.claude-plugin` is reused by VS Code/Copilot, all `${CLAUDE_PLUGIN_ROOT}`-style references and Claude-specific wording need explicit tests in that host.

## Gaps And Missing Requirements

1. **Host capability contract.** The plan needs a machine-readable matrix for each target host: skills, slash commands, agents, rules, hooks, denial/blocking, path-scoped instructions, bundled resources, and plugin packaging. Each entry should carry status: GA, preview, experimental, or unsupported.

2. **v1 hotfix acceptance criteria.** The plan should require a pre-v2 patch for rule delivery and fixture leakage. Those fixes should become golden-output tests for v2.

3. **Migration and user-owned file policy.** The requirements do not say how v2 handles existing `.claude/settings.json`, `AGENTS.md`, `.cursor/rules`, `.github` files, or user edits. It needs merge, overwrite, backup, and diff-preview rules.

4. **Generated artifact schema versioning.** Single-source artifacts need schema versions and migration rules, especially if v2 reauthors commands as skills and moves metadata into manifests.

5. **Selector evaluation oracle.** Add expected top-k skill selections for representative prompts, false-positive thresholds, and regression fixtures. Without this, "bounded selection" is an aspiration.

6. **Multi-repo contract verification.** Add schema/proto/event compatibility checks, not only sibling-repo discovery and feature-brief propagation.

7. **Security model for bundled resources and scripts.** Skills may ship scripts, examples, assets, and evals. The plan should define which are executable, how they are trusted, and whether generated projects can run them automatically.

8. **Licensing policy in generated output.** Requirements should state default package choices, version pins, generated README disclosures, and opt-in behavior for commercial-license packages.

9. **Release and rollback plan.** For the .NET CLI, define framework-dependent versus AOT artifacts, RID matrix, install/upgrade behavior from the Python `uv tool`, and rollback if v2 projection output differs.

10. **Windows parity for hooks and shell commands.** The repo supports cross-platform usage. Hook examples and generated commands need explicit PowerShell/Windows coverage, not only bash-style workflows.

## Over-Engineering And Things To Cut

1. **Cut the full clean/hexagonal rewrite from v2.0 scope.** Keep a .NET spike or future track, but do not make it the delivery vehicle for urgent rule/artifact fixes.

2. **Cut Native AOT as a launch requirement.** Make it an optimization after framework-dependent distribution works and trim analysis is clean.

3. **Cut broad domain-skill expansion until the current corpus projects cleanly.** Add only the licensing-remediation skills required to stop recommending risky defaults.

4. **Cut universal all-skill selector evals at first.** Start with ambiguous clusters and real user prompts; expand once the harness proves signal.

5. **Cut automatic Stop-hook build/test runs as a universal policy.** Prefer explicit `/verify`, analyzer gates, and CI. Use Stop hooks only where host semantics and repo baselines are known.

6. **Cut the assumption that every command must become a skill everywhere.** Use host-native surfaces when they are more discoverable or more reliable.

7. **Cut default resource folders on every skill.** `scripts/`, `examples/`, `evals/`, and `assets/` should be opt-in per skill, not boilerplate.

## Top 5 Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Shipping a second implementation while the current enforcement bug remains. | Users keep getting advisory-only guidance and v2 inherits uncertain behavior. | Ship a v1 hotfix first, then convert the fixed outputs into v2 golden tests. |
| False cross-tool parity. | The project claims support that some hosts cannot enforce or discover. | Add a capability matrix, mark preview/unverified features, and require per-host smoke tests before claiming support. |
| Rewrite regression despite the existing test suite. | The .NET CLI may miss subtle behavior from the Python CLI. | Build a host-output contract suite and run it against both implementations before replacing Python. |
| Selector/token regressions with a larger skill corpus. | Relevant skills may be missed or too many skills may enter context. | Measure `/context` where available, evaluate ambiguous clusters first, and keep skill descriptions purpose-built for routing. |
| License churn and ecosystem lock-in. | Generated code may push users into commercial packages unintentionally. | Default to license-light generated code, document opt-ins, pin versions, and keep package choices behind templates/profiles. |

## Recommended Sequence

1. **Patch v1 now:** rule delivery for Claude/plugin-native hosts, fixture exclusion, command/agent path drift, and rule budget test glob.

2. **Create artifact contract tests:** current golden outputs for Claude, Codex, Cursor, Copilot/VS Code where supported, plus install smoke tests.

3. **Build the single-source projection engine in the existing Python CLI first:** command fragments, agent manifests, rule projections, and capability matrix.

4. **Only then start the .NET port:** preserve behavior through the contract suite, begin framework-dependent, and defer Native AOT.

5. **After projection is stable, expand skills:** licensing remediation first, then new architecture/domain packs.

## Bottom Line

The plan should not be rejected. It correctly identifies the architectural failure mode: artifact drift and unenforced rules. But the current v2 shape is trying to solve too many problems at once and makes cross-tool promises that are not fully verified. The strongest version of v2 is a smaller release: fix live enforcement, centralize artifact authoring, project deterministically per host, and prove host behavior with smoke tests. The .NET rewrite can still happen, but it should be the beneficiary of those contracts, not the prerequisite for fixing them.
