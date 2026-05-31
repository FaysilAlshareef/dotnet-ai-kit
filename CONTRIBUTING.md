# Contributing to dotnet-ai-kit

dotnet-ai-kit is a **.NET 10** tool. Every assistant-facing artifact is authored once
in `artifacts/` and projected per host into `build/`, CI-gated against drift.

## Project Structure

```
dotnet-ai-kit/
├── artifacts/                # ◀ SINGLE SOURCE OF TRUTH (tool-agnostic, human-authored)
│   ├── skills/               #   149 skills + 32 command-skills (commands/) by category
│   ├── agents/               #   15 specialist agents (reference skills)
│   ├── rules/                #   21 rules — conventions/ (5 universal) + domain/ (16 path-scoped)
│   ├── profiles/             #   12 architecture profiles
│   └── knowledge/            #   reference documents
├── src/                      # .NET 10 solution (clean/hexagonal)
│   ├── DotnetAiKit.Core/         #   pure domain — artifacts, value objects, policies, graph
│   ├── DotnetAiKit.Application/  #   use-case services + ports
│   ├── DotnetAiKit.Hosts/        #   one IHostProjector per assistant + plugin manifests
│   ├── DotnetAiKit.Infrastructure/  # filesystem, YAML, detection, manifest integrity
│   ├── DotnetAiKit.Cli/          #   System.CommandLine verbs; packs as the `dotnet-ai` tool
│   └── DotnetAiKit.Analyzers/    #   Roslyn analyzers (netstandard2.0) — shipped as NuGet
├── tests/                    # xUnit suites (Core/Application/Hosts/Cli/Analyzers/Acceptance/Triggering.Evals)
├── build/                    # GENERATED per-host outputs + plugin manifests (CI drift-gated)
├── docs/                     # setup + architecture + ADRs
├── specs/                    # SDD features (NNN-name)
└── planning/                 # design record (20–26; 26 authoritative) — not shipped
```

## Development Setup

```bash
git clone https://github.com/FaysilAlshareef/dotnet-ai-kit.git
cd dotnet-ai-kit
dotnet restore dotnet-ai-kit.slnx
```

Requires the **.NET 10 SDK** (10.0.300+).

```bash
dotnet build dotnet-ai-kit.slnx -warnaserror          # build engine + analyzer
dotnet test  dotnet-ai-kit.slnx                        # full suite
dotnet format dotnet-ai-kit.slnx --verify-no-changes   # format gate
dotnet run --project src/DotnetAiKit.Cli -- generate --check   # drift gate (exit 0 = clean)
```

## Authoring artifacts

Author under `artifacts/`, then regenerate `build/` and confirm no drift.

### Skills (`artifacts/skills/<category>/<name>/SKILL.md`, ≤500 lines)

```markdown
---
name: skill-name
description: Verb-first summary. Use when <trigger>. Do NOT use <case> (use <sibling-skill>).
---

# Skill content (patterns, compilable examples, anti-patterns)
```

The **description standard is a hard gate**: action-verb-first + an explicit
"Use when…" trigger + an explicit negative scope ("Do NOT use… (use <sibling>)").
`DotnetAiKit.Acceptance.Tests` fails the build if any skill violates it.

### Command-skills (`artifacts/skills/commands/<name>/SKILL.md`)

Same shape as skills, plus `disable-model-invocation` so they stay off the
always-loaded listing and are invoked explicitly as `/dai.*`.

### Rules (`artifacts/rules/{conventions,domain}/<name>.md`, ≤100 lines)

- `conventions/<name>.md` — universal, always-on, no `paths:`.
- `domain/<name>.md` — path-scoped; carry a `paths:` list so they load only when a
  matching file is touched. `init` writes these to `.claude/rules/*.md` (the v1
  rule-delivery defect, fixed). Cursor projection emits `.mdc` with glob scoping.

## How to Contribute

1. Read the relevant `planning/` doc (20–26) and the active `specs/NNN-*/` feature.
2. Follow existing patterns; keep `DotnetAiKit.Core` pure (no I/O).
3. Before submitting, all four gates must pass: `build -warnaserror`, `test`,
   `format --verify-no-changes`, `generate --check`.
4. Add/extend tests — new policies and projectors need acceptance coverage.
5. Submit a PR with a clear description of what changed and why.

## Key Conventions

- Use `System.IO.Path`/`Path.Combine` for paths — never string concatenation.
- All code must work cross-platform (Windows, macOS, Linux).
- No network in `init`/`check`/`migrate`/`render`/`generate` (enforced by acceptance test).
- Prefer deterministic, reflection-free serialization (keeps a future Native-AOT path open).
- Specify `encoding`/UTF-8 on all file I/O.
