# dotnet-ai-kit v2 — Full Project Structure & Class Responsibilities

**Date:** 2026-05-30 · **Extends:** [21-v2-architecture-blueprint.md](21-v2-architecture-blueprint.md) · **Status:** concrete layout spec
**Locked decisions reflected here:** full CLI parity (artifacts/projection first) · JSON tool-config · `ISender` dispatch abstraction (default source-gen Mediator) · Copilot single-manifest (cloud = render) · consolidated skills (commands off the model budget) · project-scope pinned marketplace.

> **Commands→skills (verified, official Anthropic, 2026-05-30):** *"Custom commands have been merged into skills … both create `/deploy` and work the same way. Your existing `.claude/commands/` files keep working."* ([code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)). **Consequence for v2:** lifecycle "commands" are authored **as skills** (kind=`command`, usually `disable-model-invocation`+user-invocable) so they gain bundled `scripts/`/`examples/`; the projector emits each tool's command/prompt surface from that one source. There is no separate hand-written commands corpus.

---

## 1. Repository top-level

```
dotnet-ai-kit/
├── artifacts/                      # ◀ SINGLE SOURCE OF TRUTH (tool-agnostic, human-authored)
│   ├── skills/                     #   knowledge/capability + lifecycle "command" skills
│   ├── agents/                     #   specialist agent definitions (reference skills)
│   ├── rules/                      #   conventions/ (universal) + domain/ (path-scoped)
│   ├── profiles/                   #   architecture hard-constraints (path-scoped)
│   ├── fragments/                  #   reusable stanzas (authored once, included at projection)
│   ├── knowledge/                  #   long-form reference docs (linked, loaded on demand)
│   └── manifest.yml                #   ONE manifest descriptor → all per-tool plugin.json
│
├── src/                            # ◀ .NET 10 CLI (clean/hexagonal) — see §4-5
│   ├── DotnetAiKit.Core/
│   ├── DotnetAiKit.Application/
│   ├── DotnetAiKit.Hosts/
│   ├── DotnetAiKit.Infrastructure/
│   ├── DotnetAiKit.Cli/
│   └── DotnetAiKit.Analyzers/      #   Roslyn analyzers (netstandard2.0) — shipped as NuGet
│
├── tests/                          # ◀ see §6
│   ├── DotnetAiKit.Core.Tests/
│   ├── DotnetAiKit.Application.Tests/
│   ├── DotnetAiKit.Hosts.Tests/
│   ├── DotnetAiKit.Cli.Tests/
│   ├── DotnetAiKit.Analyzers.Tests/
│   ├── DotnetAiKit.Acceptance.Tests/   # cross-language invariants (the portable spec)
│   └── DotnetAiKit.Triggering.Evals/   # skill-description triggering harness + confusion matrix
│
├── build/                          # GENERATED per-tool outputs (CI-regenerated, git diff --exit-code)
│   ├── .claude-plugin/             #   also auto-detected by Copilot CLI + VS Code
│   ├── .codex-plugin/   .cursor-plugin/
│   ├── claude/  codex/  cursor/  copilot/   # projected artifact trees per tool
│   └── marketplace.json
│
├── .github/workflows/              # CI: gen + git-diff gate, tests, AOT pack matrix, publish
├── docs/                           # shipped setup/usage docs
├── planning/                       # 20 (strategy) · 21 (blueprint) · 22 (this) · …
├── Directory.Build.props  Directory.Packages.props  global.json   # central build/version mgmt
└── dotnet-ai-kit.sln
```

---

## 2. `artifacts/` — the authored source (one skill expanded)

```
artifacts/
├── skills/
│   ├── <category>/<skill-name>/            # category mirrors today's api/ data/ cqrs/ microservice/ …
│   │   ├── SKILL.md                        # ≤500 lines; portable frontmatter + x-<host> blocks
│   │   ├── scripts/
│   │   │   ├── generate.py                  # PORTABLE DEFAULT (stdlib, cross-OS)
│   │   │   ├── generate.ps1   generate.sh   # optional per-OS siblings
│   │   ├── examples/
│   │   │   └── MinimalSample/ (.csproj + Program.cs)   # compilable C# example
│   │   ├── references/
│   │   │   └── REFERENCE.md                 # Tier-3, loaded on demand
│   │   ├── assets/
│   │   │   ├── schema.json   template.cs.tmpl   appsettings.sample.json
│   │   └── evals/
│   │       ├── cases.jsonl                  # {"query": "...", "should_trigger": true|false}
│   │       └── expected/                    # golden outputs for the script/codegen
│   │
│   └── commands/<name>/SKILL.md             # lifecycle workflows authored AS skills (kind: command)
│                                            #   do, specify, plan, implement, review, verify, pr, …
│                                            #   frontmatter: disable-model-invocation: true (user-only)
│
├── agents/<name>.md                         # frontmatter (name, description, host_overrides, skills:[…],
│                                            #   routing-intents) + body (role/boundaries). REFERENCES skills.
├── rules/
│   ├── conventions/<name>.md                # universal (always-on): scope: universal
│   └── domain/<name>.md                     # path-scoped: scope: domain + paths: [globs]
├── profiles/
│   ├── generic/<arch>.md                    # clean-arch, vsa, ddd, modular-monolith, generic
│   └── microservice/<role>.md               # command, query-sql, query-cosmos, processor, gateway, controlpanel, hybrid
├── fragments/<name>.md                      # e.g. dry-run-behavior, bounded-skill-selection (FR-012)
├── knowledge/<topic>.md                     # long-form references (graph-linked, on-demand)
└── manifest.yml                             # name, version, description, keywords, component map, host caps
```

**`SKILL.md` frontmatter (portable core + gated per-host blocks):**
```yaml
name: query-entity                 # == dir; ≤64 lowercase-hyphen
description: >-                     # ≤1024; action-first + "Use when…" + "Do NOT use… (use X)"
  Generates a query-side read-model entity + projection handler for CQRS/event-sourced .NET.
  Use when adding a read model, projection, or query-side entity. Do NOT use for command-side
  aggregates (use add-aggregate) or a full CRUD stack (use add-crud).
metadata: { category: microservice/query, agent: query-architect, kind: skill }
x-claude: { paths: "${detected_paths.entities}/**/*.cs", disable-model-invocation: false }
x-cursor: { globs: "...", alwaysApply: false }
```
The `x-<host>` blocks are translated/stripped by the projector; each tool's emitted `SKILL.md` carries only fields it understands (portability rule T5).

---

## 3. Projected per-tool outputs (what lands on disk)

The **projection engine** renders `artifacts/` into each host's native shape at build time (committed under `build/`, CI-gated). `dotnet-ai init` then writes only the small per-solution set into the target repo.

```
── Claude Code ─────────────────────────         ── Codex CLI ───────────────────────────
build/.claude-plugin/plugin.json                 build/.codex-plugin/plugin.json   (no agents field)
build/claude/skills/<name>/SKILL.md  (+resources) build/codex/skills/<name>/SKILL.md
build/claude/agents/<name>.md                     build/codex/agents/<name>.toml    (skills.config refs)
build/claude/rules/<name>.md  (+ paths:)          AGENTS.md                          (universal conventions)
build/claude/hooks/hooks.json
  (lifecycle "commands" → skills, per the merge)

── Cursor ──────────────────────────────         ── GitHub Copilot ──────────────────────
build/.cursor-plugin/plugin.json (agents field)   reuses build/.claude-plugin/plugin.json  ◀ ONE manifest,
build/cursor/skills/<name>/SKILL.md                  auto-detected by Copilot CLI + VS Code
build/cursor/rules/<name>.mdc (alwaysApply|globs) build/copilot/  (CLOUD agent = render-only:)
build/cursor/commands/<name>.md                     .github/copilot-instructions.md
                                                    .github/instructions/<name>.instructions.md (applyTo)
                                                    .github/agents/<name>.agent.md
                                                    .github/prompts/<name>.prompt.md

Shared reach optimization (verified): author skills also surface via .agents/skills/
(read by Cursor + Codex + Copilot); NOT load-bearing — projector writes each tool's own dir anyway.
```

**Per-solution footprint written by `dotnet-ai init`** (small, per blueprint): `.dotnet-ai-kit/{config.yml, project.yml, manifest.json, version.txt}` + `.claude/settings.json` + `.claude/rules/*.md` (the rule-delivery fix). Everything else comes from the plugin install path.

---

## 4. `src/` solution tree & dependency direction

```
src/
├── DotnetAiKit.Core/            depends on: (nothing)
├── DotnetAiKit.Application/     depends on: Core
├── DotnetAiKit.Hosts/           depends on: Application, Core
├── DotnetAiKit.Infrastructure/  depends on: Application, Core
├── DotnetAiKit.Cli/             depends on: Hosts, Infrastructure, Application, Core   (composition root)
└── DotnetAiKit.Analyzers/       depends on: Microsoft.CodeAnalysis only  (netstandard2.0, shipped separately)

        Cli ──▶ Hosts ──▶ Application ──▶ Core ◀── Infrastructure ◀── Cli
                                    ▲                     │
                                    └──── ports ◀─────────┘     (deps point INWARD; Core is pure)
```

---

## 5. Per-project class responsibilities

### 5.1 `DotnetAiKit.Core` — domain (pure, no I/O, no NuGet beyond BCL)

```
Core/
├── Artifacts/   Skill.cs  Agent.cs  Rule.cs  Profile.cs  Fragment.cs  KnowledgeDoc.cs
├── Graph/       ArtifactGraph.cs  ArtifactNode.cs  ArtifactEdge.cs
├── Manifest/    PluginManifest.cs  ComponentMap.cs
├── Project/     ProjectMetadata.cs  DetectedPaths.cs  UserConfig.cs  ArchitectureProfileRef.cs
├── Values/      ArtifactName.cs  Description.cs  Glob.cs  SemVer.cs  HostName.cs  TokenBudget.cs  InvocationPolicy.cs  SkillKind.cs
├── Frontmatter/ Frontmatter.cs  HostExtensionBlock.cs
└── Policies/    DescriptionStandard.cs  TokenBudgetPolicy.cs  SubstitutionEngine.cs
```

| Class | Responsibility |
|---|---|
| `Skill` | Skill aggregate: name, `Description`, `Frontmatter`, body, resource set (scripts/examples/refs/assets/evals), `SkillKind` (Knowledge\|Command), `InvocationPolicy`, owning-agent ref, `paths`. Enforces invariants (name==dir, ≤64 kebab, body ≤500 lines). |
| `Agent` | Agent definition: name, description, per-host overrides, **referenced** skill names, routing-intent phrases, boundaries. Holds no resources (references skills). |
| `Rule` | Convention/domain rule: scope (universal\|domain), `Glob[]` paths, body. |
| `Profile` | Architecture hard-constraints: target `Glob[]`, constraint body; flags which constraints are analyzer-backed. |
| `Fragment` | Reusable authored stanza included into skills/commands at projection time (kills the 17/27 duplication). |
| `ArtifactGraph` / `ArtifactNode` / `ArtifactEdge` | The knowledge graph: nodes = artifacts, edges = owns/relates/triggers/enforced-by. Powers the disambiguator + broken-link validation. Built (not hand-authored) from frontmatter. |
| `PluginManifest` / `ComponentMap` | The single manifest descriptor; one per-host manifest is rendered from it (kills 4-copy drift). |
| `ProjectMetadata` / `DetectedPaths` | Detected company/domain/architecture/.NET-version + path map; the substitution source. |
| `UserConfig` | enabled_hosts, permission_profile, retention, plugin_version (the config.yml contract; honors `ai_tools`→`enabled_hosts` legacy alias). |
| `ArtifactName` / `Description` / `Glob` / `SemVer` / `HostName` / `TokenBudget` / `InvocationPolicy` / `SkillKind` | Validated value objects (parse-don't-validate). `Description` enforces the ≤1024/1536-char + standard shape. |
| `Frontmatter` / `HostExtensionBlock` | Portable core fields + `x-<host>` extension blocks; knows which fields are portable vs host-specific. |
| `DescriptionStandard` | Pure validator: action-first, "Use when…", explicit negative scope, concrete nouns — the CI-enforced rules. |
| `TokenBudgetPolicy` | Budget math: which skills are model-invocable, the ~1% listing fit, consolidation signals. |
| `SubstitutionEngine` | The `${Company}`/`${detected_paths.x}` token substitution (regex over a metadata dict — *not* a template engine). |

### 5.2 `DotnetAiKit.Application` — use-cases + ports (depends only on Core)

```
Application/
├── UseCases/   InitService  CheckService  RenderService  MigrateService  GenerateService
│               ConfigureService  DetectService  UpgradeService
└── Ports/      IFileSystem  IGitClient  IProcessRunner  IHostAdapter  IProjectionEngine
               IArtifactRepository  IArtifactSerializer  IConsoleReporter  ITokenizer
               IDetectionProvider  IManifestWriter  IBackupService
```

| Use-case | Responsibility (maps 1:1 to a CLI verb) |
|---|---|
| `InitService` | Orchestrate per-solution init: detect → write `.dotnet-ai-kit/*` + `.claude/settings.json` + **`.claude/rules/*.md` with `paths:`** (the rule-delivery fix) → route per-host writes through `IHostAdapter`. |
| `CheckService` | Validate the install: 6 check classes → the 8 exit codes (FR-031), token budgets (via `ITokenizer`), manifest integrity, no-network, footprint (SC-001). |
| `RenderService` | Resolve a skill/rule + substitute project metadata → emit the rendered body (FR-019). |
| `MigrateService` | Detect & clean legacy layout artifacts; 3-keep backup rotation (via `IBackupService`); `--include-linked`. |
| `GenerateService` | **Build-time projection:** load `artifacts/` (`IArtifactRepository`) → project every artifact to every host (`IProjectionEngine`) → render all manifests (`IManifestWriter`) → write `build/`. The CI `git diff --exit-code` target. |
| `ConfigureService` | Interactive config wizard (enabled_hosts, permission profile, repos). |
| `DetectService` | Drive `IDetectionProvider` → produce `ProjectMetadata` + `DetectedPaths`. |
| `UpgradeService` | Plugin-native = no-op; Copilot re-render; MCP/version checks. |

| Port | Contract |
|---|---|
| `IFileSystem` | Atomic temp-replace writes, utf-8, dir ops — the only file I/O seam (testable). |
| `IGitClient` / `IProcessRunner` | git ops / generic subprocess (list-args, never shell). |
| `IHostAdapter` | Per-tool: `InstallPaths()`, `VerifyInstall()`, `WritePerSolution()→HostWriteResult`, `Project(artifact)`. (Heir of v1 `hosts/base.py`.) |
| `IProjectionEngine` | Orchestrates per-artifact projection across the host registry. |
| `IArtifactRepository` | Load `artifacts/` tree → Core models + build `ArtifactGraph`. |
| `IArtifactSerializer` | Parse/emit frontmatter (YAML) + body, round-trip-safe. |
| `IConsoleReporter` | Progress/tables/prompts/errors (Spectre behind this port — use-cases stay UI-free). |
| `ITokenizer` | Count tokens (budget enforcement) — `TiktokenTokenizer`. |
| `IDetectionProvider` | Architecture/.NET-version/path detection from `.csproj`/namespaces. |
| `IManifestWriter` | Render one host's plugin.json/AGENTS.md from `PluginManifest`. |
| `IBackupService` | Atomic backup → rollback → rotate (port of `upgrade.py`). |

### 5.3 `DotnetAiKit.Hosts` — per-tool adapters (the projection backbone)

```
Hosts/
├── HostRegistry.cs            PluginNativeHostBase.cs   RenderOnlyHostBase.cs   HostWriteResult.cs
├── Claude/   ClaudeHostAdapter.cs   ClaudeProjector.cs   ClaudeManifestWriter.cs
├── Codex/    CodexHostAdapter.cs    CodexProjector.cs    CodexManifestWriter.cs   AgentsMdWriter.cs
├── Cursor/   CursorHostAdapter.cs   CursorProjector.cs   CursorManifestWriter.cs  MdcRuleWriter.cs
├── Copilot/  CopilotHostAdapter.cs  CopilotProjector.cs  InstructionsWriter.cs    PromptFileWriter.cs
└── ProjectionEngine.cs        (impl of IProjectionEngine)
```

| Class | Responsibility |
|---|---|
| `HostRegistry` | name → `IHostAdapter` lookup (replaces keyed DI; AOT-safe). |
| `PluginNativeHostBase` | Shared verify/install/write for Claude/Codex/Cursor (collapses v1's 3× copy-paste). |
| `RenderOnlyHostBase` | Render-to-files path (Copilot cloud agent only). |
| `HostWriteResult` | `{ Written, Preserved, ForceRendered, PendingConsent }` — the rich contract replacing v1's `list[Path]`. |
| `<Host>Projector` | Render each artifact (skill/agent/rule/command) into that tool's shape: Claude `.md` skills (+commands-as-skills), Codex `.toml` agents + `AGENTS.md`, Cursor `.mdc` rules + `.md` commands, Copilot `.instructions.md`/`.prompt.md`/`.agent.md`. (Generalizes v1's `render_cursor_rule_mdc`.) |
| `<Host>ManifestWriter` | Render that host's `plugin.json` from the one `PluginManifest`. |
| `ProjectionEngine` | Drive every adapter over every artifact; aggregate `HostWriteResult`s; the engine `GenerateService` calls. |

### 5.4 `DotnetAiKit.Infrastructure` — adapter implementations

| Class | Responsibility |
|---|---|
| `PhysicalFileSystem : IFileSystem` | Real FS with atomic temp-replace + utf-8 (ports v1's cross-platform discipline). |
| `GitCliClient : IGitClient` | git via subprocess (list-args). |
| `ProcessRunner : IProcessRunner` | `System.Diagnostics.Process`, no shell. |
| `JsonArtifactSerializer` | `System.Text.Json` **source-gen** for JSON config (AOT-clean). |
| `YamlFrontmatterParser : IArtifactSerializer` | `YamlDotNet` + **static generator** for frontmatter (AOT-clean). |
| `TiktokenTokenizer : ITokenizer` | `Microsoft.ML.Tokenizers` token counts. |
| `FileSystemArtifactRepository : IArtifactRepository` | Walk `artifacts/` → Core models + build `ArtifactGraph`. |
| `DotnetProjectDetector : IDetectionProvider` | Parse `.csproj`/namespaces → architecture/version/paths. |
| `ManifestIntegrityService` | sha256 + path-traversal guard (port of `manifest.py`). |
| `BackupRotationService : IBackupService` | Atomic backup/rollback/rotate (port of `upgrade.py`). |

### 5.5 `DotnetAiKit.Cli` — composition root + verbs

| Class | Responsibility |
|---|---|
| `Program` | Wire `ServiceCollection` → `BuildServiceProvider`; build the `RootCommand` tree; `Parse(args)` → `InvokeAsync`. |
| `Commands/*Command` | One per verb (`Init/Check/Render/Migrate/Generate/Configure/Detect/Upgrade`): define options/args, `SetAction((parseResult, ct) => useCase.RunAsync(...))`. No business logic. |
| `Output/SpectreConsoleReporter : IConsoleReporter` | Spectre.Console rendering (the one place Spectre is referenced). |
| `Json/AppJsonContext : JsonSerializerContext` | `[JsonSerializable]` for Core config types (AOT). |
| `Yaml/YamlStaticContext` | `[YamlSerializable]` for Core frontmatter types (AOT). |

### 5.6 `DotnetAiKit.Analyzers` — deterministic enforcement (netstandard2.0, shipped as `Dotnet.Ai.Kit.Analyzers` NuGet)

| Class | Responsibility |
|---|---|
| `ConventionAnalyzer : DiagnosticAnalyzer` | Emit diagnostics for the analyzer-backed rules/profiles: naming, layer-dependency direction, banned APIs, public setters on aggregates. |
| `ConventionCodeFixProvider : CodeFixProvider` | Offer fixes for the above where mechanical. |
| `LayeringRuleAnalyzer`, `NamingRuleAnalyzer`, `BannedApiAnalyzer` | The individual rule analyzers `ConventionAnalyzer` composes (one diagnostic id each). |
| `(optional) BoilerplateGenerator : IIncrementalGenerator` | Emit repetitive scaffolding deterministically (opt-in). |
| `analyzers/dotnet/cs` + `.editorconfig` defaults | Packaging asset + severity mapping so generated solutions get guardrails out of the box. |

---

## 6. `tests/` structure & coverage

```
tests/
├── DotnetAiKit.Core.Tests/         domain invariants · DescriptionStandard · graph build · value objects
├── DotnetAiKit.Application.Tests/  use-cases vs FAKE ports (InitService writes rules; CheckService exit codes)
├── DotnetAiKit.Hosts.Tests/        projection per host + Verify golden-output of each tool's emitted files
├── DotnetAiKit.Cli.Tests/          verb end-to-end on a temp IFileSystem + Verify golden generated solution
├── DotnetAiKit.Analyzers.Tests/    Microsoft.CodeAnalysis.Testing — diagnostics fire / don't / codefixes
├── DotnetAiKit.Acceptance.Tests/   the PORTABLE SPEC: no-network (A-011), token budgets, FR-031 8 exit codes,
│                                   SC-001 ≤18-file footprint, host symmetry  ← the cross-language gate
└── DotnetAiKit.Triggering.Evals/   skill-description harness: 20 queries/skill, 60/40 split, 3× runs,
                                    cross-skill CONFUSION MATRIX (right skill fires, siblings don't)
```

| Test project | What it guarantees |
|---|---|
| Core.Tests | Pure domain correctness; fast, no I/O. |
| Application.Tests | Use-case behavior with fake ports — most logic coverage. |
| Hosts.Tests | **Verify** snapshots: each artifact projects to the exact committed per-tool shape (drift fails CI). |
| Cli.Tests | Whole-binary behavior; **Verify** golden snapshot of a generated solution. |
| Analyzers.Tests | Each diagnostic triggers on violations and stays silent on valid code; codefixes transform correctly. |
| Acceptance.Tests | The v1 invariants re-expressed language-neutrally — the spec the .NET binary must satisfy; ~40 v1 tests port near-verbatim here. |
| Triggering.Evals | "Intelligent invocation" as a CI-gated metric, not a vibe. |

---

## 7. Data / control flow (two paths)

```
A) BUILD-TIME PROJECTION (authoring → shippable plugin)            B) RUNTIME (developer in a solution)

 artifacts/ ──IArtifactRepository──▶ Core models + ArtifactGraph    $ dotnet-ai init
      │                                      │                            │
      ▼                                      ▼                       Cli.InitCommand
 GenerateService ──IProjectionEngine──▶ ProjectionEngine                  │ SetAction
      │                                      │                       Application.InitService
      │                          ┌───────────┼───────────┐                │ (via ports)
      ▼                          ▼           ▼           ▼          ┌──────┼─────────────┐
 IManifestWriter           ClaudeProj   CodexProj   CursorProj      ▼      ▼             ▼
      │                          │           │           │      IDetection IFileSystem IHostAdapter
      ▼                          ▼           ▼           ▼          (detect) (write      (per-solution
 build/.<tool>-plugin/    build/claude/ build/codex/ build/cursor/  + Copilot  .dotnet-ai-kit/* ,    settings.json,
      │                          (committed; CI `git diff --exit-code`)         .claude/rules/)      .codex/agents)
      ▼
 CI publishes hybrid AOT `dotnet tool` + marketplace.json (project-scope, pinned)
```

---

### How this satisfies the requirements

- **All artifacts** (skills/agents/rules/profiles/commands/fragments/knowledge/manifest) live in `artifacts/` (§2); **rich resources** (scripts/examples/refs/assets/evals) are first-class on every skill.
- **Supporting tool files** for all four tools are explicit projected outputs (§3), generated from one source.
- **src + tests** are fully laid out with **every class's responsibility** (§5-6).
- **Intelligent invocation** = `DescriptionStandard` + `ArtifactGraph` + the `commands/` skills' `disable-model-invocation` (§5.1) + the `Triggering.Evals` gate (§6).
- **Clean architecture + clean separation per tool** = the inward-pointing `Core/Application/Hosts/Infrastructure/Cli` layering with one `IHostAdapter`/`Projector` per tool (§4-5).
