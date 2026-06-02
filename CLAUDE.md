# dotnet-ai-kit

AI dev tool for the full .NET development lifecycle. Authors every artifact (skills, agents, commands, rules, profiles) **once** in a tool-agnostic source tree and **projects** it to Claude Code, Codex CLI, Cursor, and GitHub Copilot.

> **v2 = a .NET 10 rewrite.** The CLI and engine are C# (.NET 10). The .NET solution is the **sole product** — the v1 Python CLI has been removed.

## Tech Stack (v2)

- **Language**: C# 13 on **.NET 10** (SDK 10.0.300); the Roslyn analyzer targets `netstandard2.0`.
- **CLI**: System.CommandLine 2.0.8 (`SetAction`); manual DI (no Generic Host / keyed DI).
- **Output**: Spectre.Console behind an `IConsoleReporter` port (never `Spectre.Console.Cli`).
- **Serialization**: System.Text.Json source-gen (tool config) + YamlDotNet (artifact frontmatter).
- **Tokenizer**: Microsoft.ML.Tokenizers (`TiktokenTokenizer`) for the budget check.
- **Tests**: xUnit + Verify (golden output). **Analyzer**: Microsoft.CodeAnalysis.
- **Build**: central package management (`Directory.Packages.props`), `global.json` pins 10.0.300.

## Project Structure (v2)

```
artifacts/                   # SINGLE SOURCE OF TRUTH (authored once)
  skills/<cat>/<name>/SKILL.md   skills/commands/<name>/SKILL.md (command-skills)
  agents/<name>.md  rules/{conventions,domain}/<name>.md  profiles/<name>.md
  knowledge/<topic>.md  manifest.yml
src/
  DotnetAiKit.Core/          # pure domain (no I/O, no third-party deps)
  DotnetAiKit.Application/   # use-cases + ports (→ Core only)
  DotnetAiKit.Hosts/         # IHostProjector per assistant (→ Application, Core)
  DotnetAiKit.Infrastructure/# adapter impls (FS, git, serializers, tokenizer, detector)
  DotnetAiKit.Cli/           # composition root + System.CommandLine verbs
  DotnetAiKit.Analyzers/     # Roslyn analyzers (netstandard2.0) → DotnetAiKit.Analyzers NuGet
tests/                       # Core/Application/Hosts/Cli/Analyzers/Acceptance.Tests + Triggering.Evals
build/                       # GENERATED per-assistant outputs (committed; drift baseline)
dotnet-ai-kit.slnx  Directory.Build.props  Directory.Packages.props  global.json
```

## Build / Test / Generate

```bash
dotnet build dotnet-ai-kit.slnx -warnaserror      # 0 warnings expected
dotnet test  dotnet-ai-kit.slnx                   # incl. the corpus-integrity test
dotnet format dotnet-ai-kit.slnx --verify-no-changes
dotnet run --project src/DotnetAiKit.Cli -- generate --out build/
dotnet run --project src/DotnetAiKit.Cli -- generate --check --out build/   # drift gate
```

## Key Conventions

1. **Clean architecture**: dependencies point inward; `Core` is pure. Use-cases depend only on ports.
2. **Single source → projection**: never hand-author a per-assistant file; author in `artifacts/`, run `generate`. The CI drift gate enforces this.
3. **Determinism**: generated output is byte-stable (sorted, fixed LF newline). `generate --check` must be drift-clean.
4. **No-network** for local verbs (`init`/`check`/`render`/`migrate`/`generate`); cross-platform (FS port, list-arg subprocess, never a shell).
5. **Description standard** (CI-gated for new artifacts): action-verb-first · explicit "Use when…" · explicit "Do NOT use… (use X)".
6. **Token discipline**: command-skills are `disable-model-invocation` (off the always-loaded listing); skill body ≤500 lines, rule ≤100, agent ≤120, profile ≤100.
7. **Paths**: `System.IO.Path`; UTF-8; LF newlines. **Encoding**: always specify UTF-8.

## Corpus (counts)

32 commands · 15 agents · 21 rules (5 universal + 16 path-scoped) · 12 profiles · ~160 skills · knowledge docs. The catalog is `planning/23`; the structure is `planning/22`; the requirements baseline is `planning/25`; locked decisions are `planning/26` (authoritative).

## CLI verbs

`init` · `check` · `render` · `generate` · `detect` · `migrate` · `configure` · `upgrade` — each a thin `*Command` delegating to an Application use-case.

## SDD

The kit ships the spec-driven lifecycle as command-skills: `constitution → specify → clarify → checklist → plan → tasks → analyze → orchestrate → implement → review → verify → fix → pr → release` (+ `status`/`undo`/`checkpoint`/`wrap-up`).

## Testing Guidelines

- xUnit; use `tmp_path`-style temp dirs for filesystem tests; mock external calls (no real network).
- The `Acceptance.Tests` project carries the cross-cutting contract (no-network, exit codes, footprint, drift, corpus integrity).
- Verify golden baselines are red on first authoring — accept (`*.verified.*`) then commit.
