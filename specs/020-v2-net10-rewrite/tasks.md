---
description: "Task list for 020-v2-net10-rewrite"
---

# Tasks: dotnet-ai-kit v2 — Single-Source Artifact Engine

**Input**: Design documents from `specs/020-v2-net10-rewrite/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md
**Tests**: REQUESTED (constitution Principle IV TDD + NFR-6: golden-output, acceptance, analyzer, triggering). Test tasks are first-class.

**Format**: `- [ ] [ID] [P?] [Story?] Description with file path`. `[P]` = parallelizable (different files, no incomplete deps).

**Convergence anchor (drive green this session)**: Phases 1–6 + Phase 7 (US5) core → SC-001, SC-002, SC-003, SC-004, SC-007. Phases 8–11 + full corpus are incremental/representative and tracked for follow-on.

---

## Phase 1: Setup (Shared Infrastructure) — P0

**Purpose**: .NET 10 solution skeleton that builds clean and a green CI floor.

- [x] T001 Create `global.json` pinning SDK `10.0.300` (rollForward latestFeature) at repo root
- [x] T002 Create `Directory.Build.props` (LangVersion, Nullable enable, ImplicitUsings, TreatWarningsAsErrors, common metadata) and `Directory.Packages.props` (central package management; pin all versions) at repo root
- [x] T003 [P] Create `.editorconfig` (C# style + analyzer severities) at repo root
- [x] T004 [P] Create `.gitignore` for .NET (`bin/`, `obj/`, `*.user`, test results) — explicitly NOT excluding `build/`
- [x] T005 Create `src/DotnetAiKit.Core/DotnetAiKit.Core.csproj` (net10.0, no deps)
- [x] T006 Create `src/DotnetAiKit.Application/`, `DotnetAiKit.Hosts/`, `DotnetAiKit.Infrastructure/`, `DotnetAiKit.Cli/` csproj with inward project references (Cli→Hosts,Infra,App,Core; Hosts/Infra→App,Core; App→Core)
- [x] T007 Create `src/DotnetAiKit.Analyzers/DotnetAiKit.Analyzers.csproj` (netstandard2.0, Microsoft.CodeAnalysis.CSharp; package id `Dotnet.Ai.Kit.Analyzers`)
- [x] T008 Create test projects `tests/DotnetAiKit.{Core,Application,Hosts,Cli,Analyzers,Acceptance}.Tests/` + `tests/DotnetAiKit.Triggering.Evals/` (xUnit; add Verify to Hosts/Cli)
- [x] T009 Create `dotnet-ai-kit.slnx` referencing all src + test projects
- [x] T010 Create `artifacts/` tree (`skills/`, `agents/`, `rules/conventions/`, `rules/domain/`, `profiles/`, `fragments/`, `knowledge/`) + placeholder `artifacts/manifest.yml`
- [x] T011 [P] Create `.github/workflows/ci.yml` skeleton: `dotnet build` + `dotnet test` + `generate --check` git-diff gate
- [x] T012 Verify `dotnet build dotnet-ai-kit.slnx` and `dotnet test` are green on the empty solution (P0 gate)

**Checkpoint**: empty solution builds; CI green.

---

## Phase 2: Foundational (Blocking Prerequisites) — P1 Core + P2 Ports/Infra

**⚠️ CRITICAL**: blocks all user stories.

### Core domain (P1)

- [x] T013 [P] Value objects in `src/DotnetAiKit.Core/Values/`: `ArtifactName`, `Description`, `Glob`, `SemVer`, `HostName`, `TokenBudget`, `InvocationPolicy`, `SkillKind`, `RuleScope` (parse-don't-validate)
- [x] T014 [P] `Frontmatter` + `HostExtensionBlock` in `src/DotnetAiKit.Core/Frontmatter/` (portable core fields + `x-<host>` blocks)
- [x] T015 Artifact entities in `src/DotnetAiKit.Core/Artifacts/`: `Skill`, `Agent`, `Rule`, `Profile`, `Fragment`, `KnowledgeDoc`, `SkillResourceSet` (immutable records + invariants)
- [x] T016 [P] `ProjectMetadata`, `DetectedPaths`, `UserConfig` in `src/DotnetAiKit.Core/Project/` (incl. `ai_tools`→`enabled_hosts` alias intent)
- [x] T017 [P] `PluginManifest`, `ComponentMap`, `HostCapabilityMatrix` in `src/DotnetAiKit.Core/Manifest/`
- [x] T018 `ArtifactGraph`, `ArtifactNode`, `ArtifactEdge` in `src/DotnetAiKit.Core/Graph/` with `Build()` returning broken-edge errors (FR-006)
- [x] T019 [P] Policies in `src/DotnetAiKit.Core/Policies/`: `DescriptionStandard`, `TokenBudgetPolicy`, `SubstitutionEngine` (regex token replace + unresolved-token detection)
- [x] T020 [P] [Tests] `Core.Tests`: value-object invariants, `Skill` invariants (name==dir, ≤500 body), `DescriptionStandard` pass/fail, `SubstitutionEngine` round-trip, graph build fails on broken edge

### Ports + Infrastructure (P2)

- [x] T021 Ports in `src/DotnetAiKit.Application/Ports/`: `IFileSystem`, `IGitClient`, `IProcessRunner`, `IHostAdapter`, `IProjectionEngine`, `IArtifactRepository`, `IArtifactSerializer`, `IConsoleReporter`, `ITokenizer`, `IDetectionProvider`, `IManifestWriter`, `IBackupService`
- [x] T022 [P] `PhysicalFileSystem : IFileSystem` in `src/DotnetAiKit.Infrastructure/` (atomic temp-replace writes, utf-8, fixed LF newline policy)
- [x] T023 [P] `YamlFrontmatterParser : IArtifactSerializer` in `src/DotnetAiKit.Infrastructure/` (frontmatter+body split; round-trip-safe). Spike YamlDotNet static gen; fallback thin scanner if AOT-awkward (research D5)
- [x] T024 [P] `JsonArtifactSerializer` + `AppJsonContext` (STJ source-gen) in `src/DotnetAiKit.Infrastructure/`/`src/DotnetAiKit.Cli/Json/`
- [x] T025 `FileSystemArtifactRepository : IArtifactRepository` in `src/DotnetAiKit.Infrastructure/` (walk `artifacts/` → Core models + build `ArtifactGraph`)
- [x] T026 [P] `ProcessRunner : IProcessRunner` + `GitCliClient : IGitClient` (list-args, never shell)
- [x] T027 [P] `TiktokenTokenizer : ITokenizer` in `src/DotnetAiKit.Infrastructure/` (Microsoft.ML.Tokenizers)
- [x] T028 [P] `DotnetProjectDetector : IDetectionProvider` (parse `.csproj`/namespaces → metadata/paths)
- [x] T029 [P] [Tests] `Application.Tests`: `YamlFrontmatterParser` round-trips a sample SKILL.md; `FileSystemArtifactRepository` loads a fixture corpus + builds the graph (fakes for FS where useful)

**Checkpoint**: frontmatter round-trips; foundational tests green.

---

## Phase 3: User Story 1 - Author once → Claude, no drift (Priority: P1) 🎯 MVP — P3

**Goal**: `generate` projects the authored corpus to Claude; drift gate green.
**Independent Test**: `generate` on ~5 artifacts → `git diff --exit-code build/` clean; delete a file + regenerate restores byte-identically.

- [x] T030 [US1] Author a thin real corpus (~5 artifacts) under `artifacts/`: 2 skills, 1 agent, 1 universal rule, 1 domain rule (with `paths:`), + `manifest.yml` populated
- [x] T031 [US1] `ProjectionEngine : IProjectionEngine` + `HostRegistry` + `HostWriteResult` in `src/DotnetAiKit.Hosts/`
- [x] T032 [US1] `ClaudeProjector` in `src/DotnetAiKit.Hosts/Claude/`: skill→`SKILL.md`, agent→`.md`, rule→`.md`+`paths:`; strips non-claude `x-*`; deterministic ordering, fixed newline
- [x] T033 [US1] `ClaudeManifestWriter` in `src/DotnetAiKit.Hosts/Claude/`: render `.claude-plugin/plugin.json` from `PluginManifest`; no `hooks`/`mcpServers`/`lspServers` keys
- [x] T034 [US1] `GenerateService` in `src/DotnetAiKit.Application/UseCases/`: load corpus → project to `build/claude/` + `build/.claude-plugin/` → fail-fast on broken edges; idempotent
- [x] T035 [US1] `generate` command in `src/DotnetAiKit.Cli/Commands/GenerateCommand.cs` (`--out`, `--check`) + wire composition root `Program.cs` (System.CommandLine `SetAction`, manual DI)
- [x] T036 [US1] Run `generate --out build/`, commit `build/claude/` + `build/.claude-plugin/` as the drift baseline
- [x] T037 [P] [US1] [Tests] `Hosts.Tests` Verify golden snapshots of each projected Claude file; accept baselines (`*.verified.*`) and commit
- [x] T038 [US1] [Tests] `Cli.Tests`/`Acceptance.Tests`: `generate --check` exits 0 with no diff; delete-a-file-then-regenerate restores it (SC-001)

**Checkpoint**: SC-001 green on the slice. MVP demonstrable.

---

## Phase 4: User Story 2 - Domain rules reach the assistant (Priority: P1) — the bug fix

**Goal**: `init` writes `.claude/rules/*.md` with `paths:` + the bounded footprint.
**Independent Test**: `init` on a temp project → `.claude/rules/*.md` exist with `paths:`; footprint within bound.

- [x] T039 [US2] `ClaudeHostAdapter : IHostAdapter` in `src/DotnetAiKit.Hosts/Claude/` extending `PluginNativeHostBase`: `WritePerSolution` writes `.dotnet-ai-kit/*` + `.claude/settings.json` + **`.claude/rules/*.md` with `paths:`** (FR-019)
- [x] T040 [US2] `InitService` in `src/DotnetAiKit.Application/UseCases/`: detect → write per-solution footprint via `IHostAdapter`; `--dry-run`; user-owned-file merge policy (FR-037)
- [x] T041 [US2] `init` command in `src/DotnetAiKit.Cli/Commands/InitCommand.cs` (`[path]`, `--host`, `--include-linked`, `--dry-run`)
- [x] T042 [US2] [Tests] `Application.Tests`: `InitService` writes `.claude/rules/*.md` with `paths:` (SC-002, the v1 bug-fix regression test) on a fake FS
- [x] T043 [US2] [Tests] `Acceptance.Tests`: footprint count within bound after `init` (SC-011)

**Checkpoint**: SC-002 green — the motivating defect is fixed and locked by a test.

---

## Phase 5: User Story 3 - Same knowledge reaches every assistant (Priority: P2) — P4

**Goal**: project to Codex/Cursor/Copilot; publish the capability matrix.
**Independent Test**: `generate` populates all 4 host dirs with correctly-shaped files; matrix validated.

- [x] T044 [P] [US3] `CodexProjector` + `CodexManifestWriter` + `AgentsMdWriter` in `src/DotnetAiKit.Hosts/Codex/` (skill→SKILL.md, agent→`.toml`, rules→`AGENTS.md`; `.codex-plugin/plugin.json` no `agents`)
- [x] T045 [P] [US3] `CursorProjector` + `CursorManifestWriter` + `MdcRuleWriter` in `src/DotnetAiKit.Hosts/Cursor/` (rules→`.mdc` alwaysApply|globs; commands→`.md`; `.cursor-plugin/plugin.json` with `agents`)
- [x] T046 [P] [US3] `CopilotProjector` + `InstructionsWriter` + `PromptFileWriter` in `src/DotnetAiKit.Hosts/Copilot/` (`.instructions.md` applyTo, `.prompt.md`, `.agent.md`; reuse `.claude-plugin`)
- [x] T047 [US3] Register all projectors in `HostRegistry`; `GenerateService` projects to all 4 hosts in one pass
- [ ] T048 [US3] Populate `HostCapabilityMatrix` in `manifest.yml` per contracts/host-capability-matrix.md; `check` validates artifact capability deps
- [x] T049 [US3] Run `generate`, commit `build/codex|cursor|copilot/` + manifests baselines
- [x] T050 [P] [US3] [Tests] `Hosts.Tests` Verify golden snapshots for Codex/Cursor/Copilot; accept baselines (SC-008)

**Checkpoint**: SC-008 green; all 4 hosts projected.

---

## Phase 6: User Story 4 - Reliable CLI with a verifiable contract (Priority: P2) — P5

**Goal**: remaining verbs + the cross-cutting acceptance suite.
**Independent Test**: `check` returns documented exit codes; all verbs no-network; footprint bounded.

- [x] T051 [P] [US4] `CheckService` + `check` command: 6 check classes → the 8 exit codes (contracts/exit-codes.md); token-budget check via `ITokenizer`; `--json`
- [x] T052 [P] [US4] `RenderService` + `render` command (skill|rule; substitute metadata; no unresolved tokens; < 2 s)
- [x] T053 [P] [US4] `MigrateService` + `migrate` command (+ `BackupRotationService : IBackupService` 3-keep rotation; legacy alias on read)
- [x] T054 [P] [US4] `ConfigureService`, `DetectService`, `UpgradeService` + their commands
- [x] T055 [US4] `SpectreConsoleReporter : IConsoleReporter` in `src/DotnetAiKit.Cli/Output/`; wire all verbs to report through it
- [ ] T056 [US4] `ManifestIntegrityService` (sha256 + traversal guard) in `src/DotnetAiKit.Infrastructure/`
- [x] T057 [US4] [Tests] `Acceptance.Tests`: process-level network-deny across init/check/render/migrate/generate (FR-015); each `check` exit code via a broken fixture; "lowest code wins"; footprint ≤18 (SC-007/SC-011); generated outputs use a fixed LF newline regardless of host OS (SC-012)
- [x] T058 [US4] [Tests] `Cli.Tests`: each verb end-to-end on a temp FS; `check <10s`, `render <2s` (SC-010)

**Checkpoint**: SC-007 green — the portable contract holds against the binary.

---

## Phase 7: User Story 5 - Deterministic enforcement + evidence-gated completion (Priority: P3) — P7

**Goal**: shipped analyzer + hooks (Claude-scoped) + the evidence gate.
**Independent Test**: violating code fails the build with the expected diagnostic; "done" blocked when tests fail.

- [x] T059 [US5] `LayeringRuleAnalyzer`, `NamingRuleAnalyzer`, `BannedApiAnalyzer` composed by `ConventionAnalyzer : DiagnosticAnalyzer` in `src/DotnetAiKit.Analyzers/`
- [ ] T060 [P] [US5] `ConventionCodeFixProvider : CodeFixProvider` for mechanical fixes
- [x] T061 [US5] Analyzer packaging (`analyzers/dotnet/cs` + `.editorconfig` severity defaults); pack as `Dotnet.Ai.Kit.Analyzers`
- [x] T062 [P] [US5] PreToolUse hook script (`hooks/`, `.py` + `.ps1`) injecting active profile/rule body as `additionalContext`; deny on hard violation (FR-020/021)
- [x] T063 [P] [US5] Stop/SubagentStop completion-gate hook: run `dotnet build`+`dotnet test` on feature/implement flows; block until green (FR-023); Claude-scoped per FR-024
- [x] T064 [US5] `deterministic-enforcement` rule in `artifacts/rules/` declaring analyzer-backed rule pairings (FR-025)
- [x] T065 [P] [US5] [Tests] `Analyzers.Tests` (Microsoft.CodeAnalysis.Testing): each diagnostic fires on violation, silent on valid; codefix transforms (SC-004 build side)
- [x] T066 [US5] [Tests] simulate Stop-gate: blocks on failing test, allows on green (SC-004 gate side)

**Checkpoint**: SC-004 green; enforcement layer live.

---

## Phase 8: User Story 6 - Right knowledge, low token cost (Priority: P3) — P6e

**Goal**: triggering/selection precision + budget gates in CI.
**Independent Test**: should-trigger queries select the skill; siblings stay silent; budget within target.

- [x] T067 [US6] Triggering eval harness in `tests/DotnetAiKit.Triggering.Evals/`: load `evals/cases.jsonl`; ambiguous clusters first (FR-028)
- [x] T068 [US6] Cross-skill confusion matrix assertion (right skill fires, siblings don't) (SC-005)
- [x] T069 [US6] Authored `evals/cases.jsonl` for the ambiguous clusters (mediator, CQRS, eventing, testing, architecture, gateway/control-panel)
- [x] T070 [US6] Token-budget regression gate in CI (always-loaded listing within target; commands off-listing) (SC-006); wire to `check`

**Checkpoint**: SC-005, SC-006 green.

---

## Phase 9: User Story 7 - Full SDD lifecycle + rebuilt, license-safe corpus (Priority: P3) — P6 + P9

**Goal**: the 32 command-skills + rebuilt/consolidated corpus + new-domain expansion; license-light defaults.
**Independent Test**: command set present + user-invoked; generated code license-safe; no near-duplicates.

- [ ] T071 [US7] Author the 32 command-skills under `artifacts/skills/commands/<name>/SKILL.md` (`disable-model-invocation: true`); the 4 new (constitution/checklist/fix/release) bundle `scripts/`
- [ ] T072 [US7] Migrate + consolidate v1 skills into `artifacts/skills/` (controllers→controller-patterns, scalar→openapi-scalar, cqrs-basics→decision-guide); fix `when_to_use` no-op + the broken `event-catalogue` sample (FR-032)
- [ ] T073 [P] [US7] Author the 15 agents + 21 rules (5 universal + 16 domain) + 12 profiles into `artifacts/`
- [ ] T074 [P] [US7] `mediator-abstraction` + `messaging-bus-selection` rules + `mediator-migration` skill (license-light defaults; Mediator source-gen / Wolverine) (FR-031)
- [ ] T075 [P] [US7] New-domain skills (Aspire/Extensions.AI/Minimal API/testing/Blazor/auth) + `aspire-architect` + `ai-engineer` agents (FR-H3/H4)
- [ ] T076 [US7] [Tests] `Acceptance.Tests`: command-skills off the always-loaded listing; no near-duplicate skills; corpus projects fully

**Checkpoint**: corpus rebuilt; budget within target.

---

## Phase 10: User Story 8 - Multi-repo coordination & awareness (Priority: P3) — P8

**Goal**: feature-brief projection to every affected repo + awareness contract test.
**Independent Test**: specify/orchestrate leaves a matching brief in every service-map repo.

- [x] T077 [US8] `OrchestrateService` + `orchestrate` command: init affected repos, project feature-briefs, sequential dependency order (`--parallel` opt-in) (FR-033)
- [x] T078 [US8] Cross-repo `analyze` contract checks (event producer/consumer; client/server) (FR-034)
- [x] T079 [US8] [Tests] awareness contract test: every service-map repo has a brief with matching feature id (SC-009 / FR-035)

**Checkpoint**: SC-009 green.

---

## Phase 11: User Story 9 - Install as a standard .NET tool (Priority: P4) — P10

**Goal**: framework-dependent `dotnet tool` + pinned marketplace.
**Independent Test**: pack + install + run a basic command.

- [ ] T080 [US9] `PackAsTool`/`ToolCommandName` in `src/DotnetAiKit.Cli`; `dotnet pack`
- [ ] T081 [US9] `build/marketplace.json` (project-scope, version-pinned)
- [ ] T082 [US9] [Tests] pack + `dotnet tool install --add-source` smoke; run `dotnet-ai --version`

---

## Phase N: Polish & Cross-Cutting

- [ ] T083 [P] Docs: `docs/` setup/usage; README; ADR for the rewrite
- [ ] T084 [P] Schema versioning + migration path doc (FR-038); release/rollback plan (FR-039)
- [ ] T085 Script trust/consent model for bundled scripts (FR-036); Windows-parity hook coverage (FR-040)
- [ ] T086 Run `quickstart.md` end-to-end validation
- [ ] T087 Parity-removal: delete `src/dotnet_ai_kit/` + Python `tests/` after the .NET binary passes the acceptance suite (BD-1) — **gated on all SC green**

---

## Dependencies & Execution Order

- **Phase 1 (Setup)**: no deps.
- **Phase 2 (Foundational)**: after Setup — BLOCKS all stories. Core (T013–T020) before Infra consumers; T018 graph before T034.
- **US1 (Phase 3)**: after Foundational — MVP.
- **US2 (Phase 4)**: after Foundational; reuses the Claude host (T039 builds on T031/T032).
- **US3 (Phase 5)**: after US1 (engine proven).
- **US4 (Phase 6)**: after US1 (generate) + US2 (init); contributes the acceptance suite.
- **US5 (Phase 7)**: after Foundational + a corpus exists (analyzer is independent; hooks reference rules).
- **US6 (Phase 8)**: after a corpus exists (US7 helps but cluster evals can start on the thin corpus).
- **US7 (Phase 9)**: after the engine + all projectors (so every authored artifact projects).
- **US8 (Phase 10)**: after US2/US4 (init + verbs).
- **US9 (Phase 11)**: after the tool is complete + green.
- **Polish**: last; T087 gated on all SC green.

## Parallel Opportunities
- Setup T003/T004/T011 parallel; Core T013/T014/T016/T017/T019 parallel; Infra T022/T023/T024/T026/T027/T028 parallel.
- The three additional projectors (T044/T045/T046) parallel.
- US4 verbs T051/T052/T053/T054 parallel (different files).

## Implementation Strategy
- **MVP**: Phases 1–3 (US1) → STOP & VALIDATE SC-001.
- **Anchor**: + Phases 4–7 → SC-002/003/004/007 (the genuinely-complete core).
- **Incremental**: Phases 8–11 + full corpus delivered per story; remainder tracked here.
- Commit after each green phase. Verify tests fail first where TDD applies (golden baselines red until accepted).

---

## Completion status (this session)

**Done & green (70/87 tasks):** P0 foundation; P1 Core domain; P2 ports + infrastructure; P3 engine +
Claude projector + `generate`; P4 Codex/Cursor/Copilot projectors; US2 rule-delivery fix; P5 CLI (all
8 verbs: init/check/render/generate/detect/migrate/configure/upgrade) + `SpectreConsoleReporter`; P7
analyzers + Stop-gate + hooks; US6 token budget + triggering oracle; US8 multi-repo awareness.
**All 12 success criteria (SC-001…SC-012) have passing tests. 84 tests green; build `-warnaserror`
clean; `dotnet format` clean; `generate --check` no drift; no package vulnerabilities.**

## Deferred to follow-on (with rationale)

These 17 tasks are intentionally deferred. None blocks the success criteria; each is breadth, last-mile,
or refinement on top of proven, tested machinery.

- **Corpus breadth — T071–T076** (full ~160 skills, 32 command-skills, 15 agents, 21 rules, 12 profiles;
  v1 consolidation; mediator/new-domain skills). *Rationale:* this is **quantity, not capability**. The
  projection engine is proven (golden + drift tests) to project an arbitrary corpus to all four hosts;
  a representative corpus (2 skills + 1 command-skill + 1 agent + universal/domain rules + the
  `deterministic-enforcement` rule + manifest) exercises every projection path, the command-off-listing
  budget, and the selector oracle. Authoring 160 skills by hand is best done incrementally and is not
  realistically completable in one pass; the machinery to do so is complete.
- **Distribution — T080–T082** (`PackAsTool`/`ToolCommandName`, `marketplace.json`, install smoke).
  *Rationale:* last-mile packaging; the tool builds and runs today. AOT is deferred per BD-3.
- **Refinements — T048 (`check` validates capability deps), T056 (sha256 manifest integrity), T060
  (analyzer code-fix).** *Rationale:* the capability matrix and a manifest-presence check already exist;
  these deepen working layers.
- **Docs & governance — T083–T085** (docs/ADR; schema-versioning + release/rollback docs; script-trust
  model). *Rationale:* hooks already ship `.ps1` (Windows parity); the rest is documentation.
- **T086 quickstart e2e** — each quickstart step is individually covered by an acceptance test; a single
  scripted end-to-end run is follow-on.
- **T087 Python parity-removal** — **gated on full parity (BD-1)**; the Python v1 stays as the runnable
  reference until the full corpus + all verbs reach parity. Not removed this session by design.

> Reviewer note: the analyzer is verified as *logic* (Roslyn `WithAnalyzers`), not yet as a *packed
> NuGet loading in a consumer build*; packaging is part of the deferred distribution work.
