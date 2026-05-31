# dotnet-ai-kit

AI dev tool plugin for the full .NET development lifecycle. Authored **once** in a
tool-agnostic `artifacts/` source tree and **projected** to Claude Code, Codex CLI,
Cursor, and GitHub Copilot, CI-gated so the assistants never drift apart.

> v2 is a .NET 10 rewrite. The .NET CLI is the sole implementation — the v1 Python
> CLI has been removed.

## Setup

**Requirements**: .NET 10 SDK (10.0.300+) · Git

```bash
dotnet tool install --global DotnetAiKit.Tool     # the `dotnet-ai` CLI
```

## Build & Test

```bash
dotnet build dotnet-ai-kit.slnx -warnaserror      # build engine + analyzer
dotnet test  dotnet-ai-kit.slnx                    # full suite incl. corpus-integrity
dotnet format dotnet-ai-kit.slnx --verify-no-changes
dotnet run --project src/DotnetAiKit.Cli -- generate --check   # CI drift gate (exit 0 = clean)
```

## Architecture

Clean/hexagonal .NET solution; dependencies point inward (Core is pure):

```
DotnetAiKit.Cli ─▶ DotnetAiKit.Hosts ─┐
                   DotnetAiKit.Infrastructure ─▶ DotnetAiKit.Application ─▶ DotnetAiKit.Core
                   DotnetAiKit.Analyzers (netstandard2.0, shipped as NuGet)
```

- **Core** — artifacts (Skill/Agent/Rule/Profile/Knowledge), value objects, policies
  (DescriptionStandard, TokenBudget, SubstitutionEngine), the artifact graph. No I/O.
- **Application** — use-case services (Init/Check/Render/Generate/Detect/Migrate/Configure/Upgrade) + ports.
- **Hosts** — one `IHostProjector` per assistant (Claude/Codex/Cursor/Copilot) + plugin manifests.
- **Infrastructure** — filesystem, YAML parsing, detection, manifest integrity (sha256).
- **Cli** — System.CommandLine verbs; packs as the `dotnet-ai` tool.
- **Analyzers** — Roslyn analyzers DAK0001 (no `async void`) / DAK0004 (aggregate no public setter) + code-fix.

## Single-source projection

`artifacts/` is the only authored source. `dotnet-ai generate` projects it to
`build/{claude,codex,cursor,copilot}` + per-host plugin manifests + `marketplace.json`.
CI runs `generate --check` (`git diff --exit-code`) so drift cannot merge.

## Development Workflow

Spec-Driven Development: `specify → clarify → plan → tasks → analyze → implement →
review → verify → PR`. `/dai.do "feature"` chains the full lifecycle. Features live
under `specs/NNN-name/`.

## Code Conventions

- **Paths**: `System.IO.Path` / `Path.Combine` — never string concatenation.
- **Cross-platform**: must work on Windows, macOS, Linux.
- **Serialization**: explicit/source-friendly (no reflection-heavy paths) — keeps a future Native-AOT path open.
- **Determinism**: projection + policies are pure and deterministic (CI-gated; no network in init/check/migrate/render/generate).
- **Token budgets**: skill ≤500 lines, rule ≤100, agent ≤120, profile ≤100.
- **Descriptions**: every skill is action-verb-first + "Use when…" + "Do NOT use… (use <sibling>)" (hard-gated).

## Testing

- xUnit; `DotnetAiKit.Acceptance.Tests` holds the portable cross-host invariants
  (corpus loads, zero broken graph edges, every host projects without path collisions,
  every skill passes the description standard).
- Mock external calls; never hit the network. Verify golden-output where projection shape matters.

## Project Structure

```
artifacts/        # SINGLE SOURCE: skills/ agents/ rules/ profiles/ knowledge/ (+ manifest)
src/              # .NET 10 solution (Core/Application/Hosts/Infrastructure/Cli/Analyzers)
tests/            # xUnit suites incl. Acceptance + Triggering.Evals
build/            # GENERATED per-host outputs + plugin manifests (CI drift-gated)
docs/             # setup + architecture + ADRs
specs/            # SDD features (NNN-name)
planning/         # design record (20–26; 26 authoritative) — not shipped
```
