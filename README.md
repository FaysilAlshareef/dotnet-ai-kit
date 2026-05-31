<p align="center">
  <img src="assets/banner-github.svg" alt="dotnet-ai-kit banner" width="900"/>
</p>

<h3 align="center">The AI brain for .NET — authored once, projected to every assistant</h3>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-00D4AA?style=flat-square" alt="License"></a>
  <a href="https://dotnet.microsoft.com/"><img src="https://img.shields.io/badge/.NET-10-512BD4?style=flat-square&logo=dotnet&logoColor=white" alt=".NET 10"></a>
  <a href="#"><img src="https://img.shields.io/badge/Claude_Code-·_Codex_·_Cursor_·_Copilot-F78166?style=flat-square" alt="Assistants"></a>
</p>

---

**dotnet-ai-kit** equips AI coding assistants — **Claude Code, Codex CLI, Cursor, and GitHub Copilot** — with the skills, agents, commands, rules, and guardrails for the full .NET development lifecycle. Every artifact is authored **once** in a tool-agnostic source tree and **projected** into each assistant's native shape, CI-gated so the four assistants never drift apart.

> **v2** is a ground-up rewrite in **.NET 10** (clean/hexagonal architecture). A single authored source (`artifacts/`) is projected into each assistant's native shape, CI-gated against drift. It fixes the v1 defect where domain rules never reached the assistant and adds deterministic enforcement (a shipped Roslyn analyzer). The .NET 10 CLI is the **sole implementation** — the v1 Python CLI has been removed.

## What it gives you

- **One source, four assistants** — author a skill/agent/rule/command once in `artifacts/`; `dotnet-ai generate` projects it to Claude, Codex, Cursor, and Copilot. A CI drift gate (`git diff --exit-code`) makes divergence impossible to merge.
- **Rules that actually arrive** — `dotnet-ai init` writes your domain rules to `.claude/rules/*.md` with `paths:` scoping, so the right conventions load when the relevant file is touched (the v1 bug, fixed).
- **Deterministic enforcement** — all four `planning/24` tiers are wired: advisory rules + a PreToolUse `additionalContext` injection (T1), a PreToolUse **deny** on generated-file edits (T2), the shipped `DotnetAiKit.Analyzers` Roslyn package turning mechanical conventions into build errors with code-fixes (`DAK0001`, `DAK0004` — T3), and a **Stop hook** that blocks "done" until `dotnet build` + `dotnet test` are green (T4). The hard hook tiers are Claude-scoped (other hosts fall back to the analyzer + CI).
- **A full SDD lifecycle** — 32 commands from `constitution` → `specify` → … → `verify` → `pr` → `release`, plus code-generation commands.
- **Token-frugal** — commands are off the always-loaded listing; selection is sharp descriptions + an artifact graph, gated by a triggering eval — not a heavyweight router.

## The corpus

| Kind | Count | Where |
|---|---|---|
| Skills | 149 | `artifacts/skills/` |
| Command-skills | 32 | `artifacts/skills/commands/` |
| Agents | 15 | `artifacts/agents/` |
| Rules | 21 (5 universal + 16 path-scoped) | `artifacts/rules/` |
| Profiles | 12 | `artifacts/profiles/` |

## Quick start (developing the kit)

```bash
dotnet build dotnet-ai-kit.slnx        # build the engine + analyzer
dotnet test  dotnet-ai-kit.slnx        # full suite incl. the corpus-integrity test

# project the authored corpus to every assistant
dotnet run --project src/DotnetAiKit.Cli -- generate --out build/
dotnet run --project src/DotnetAiKit.Cli -- generate --check --out build/   # drift gate: exit 0 = no drift
```

## CLI

`dotnet-ai <verb>` — `init` · `check` · `render` · `generate` · `detect` · `migrate` · `configure` · `upgrade`.

```bash
dotnet-ai init --host claude     # write the per-solution footprint (+ .claude/rules with paths:)
dotnet-ai check                  # validate the install (enumerated exit codes)
dotnet-ai render skill <name>    # render a skill with project metadata substituted
```

## Architecture (v2)

```
artifacts/  ──(projection engine, CI-gated)──▶  build/{claude,codex,cursor,copilot} + manifests
   │  single source of truth                         the per-assistant shapes
   ▼
src/  Core → Application(+ports) → {Hosts, Infrastructure} → Cli ;  Analyzers (Roslyn NuGet)
```

Dependencies point inward; `Core` is pure (no I/O). One `IHostProjector` per assistant. Reflection-free serialization keeps the AOT path open. See [docs/architecture.md](docs/architecture.md) and [planning/](planning/).

## Repository layout

| Path | What |
|---|---|
| `artifacts/` | the single authored source (skills, agents, rules, profiles, knowledge, manifest) |
| `src/` | the .NET 10 solution (`DotnetAiKit.{Core,Application,Hosts,Infrastructure,Cli,Analyzers}`) |
| `tests/` | xUnit test projects incl. `Acceptance.Tests` (the cross-cutting contract) |
| `build/` | generated per-assistant outputs (committed; the drift baseline) |
| `docs/` · `planning/` | documentation + the v2 design record |

## Setup per assistant

[Claude Code](docs/setup-claude-code.md) · [Codex CLI](docs/setup-codex-cli.md) · [Cursor](docs/setup-cursor.md) · [GitHub Copilot](docs/setup-copilot.md)

## License

MIT — see [LICENSE](LICENSE).
