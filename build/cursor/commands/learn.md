---
description: "Generates a project constitution + topic split. Use when persisting project knowledge across sessions. Do NOT use to scan and report the raw project architecture (use detect)."
---
# /dotnet-ai.learn

Produce a small, always-readable `constitution.md` (≤100 lines) and a six-file topic split. Consumers load only the topic they need (FR-023 / FR-024).

## Usage

```
/dotnet-ai.learn $ARGUMENTS
```

`--update`, `--dry-run`, `--verbose` supported.

## MCP-first project queries (FR-021 / FR-022)

For graph, dependency, ownership, or architecture questions in this project,
query `codebase-memory-mcp` first; use `csharp-ls` for symbol-precise lookups;
fall back to `grep` / file reads only when neither MCP can answer.

If the memory MCP is unavailable, emit exactly:

> MCP unavailable: codebase-memory-mcp is not connected or below >=0.6.1; falling back to csharp-ls + grep/read.

## Outline

You generate seven files under `.dotnet-ai-kit/memory/`:

1. `constitution.md` — index, ≤100 lines
2. `architecture.md` — patterns, layering, deployment shape
3. `domain-model.md` — aggregates, entities, value objects
4. `event-flow.md` — events, schemas, consumers/producers
5. `interfaces.md` — public contracts (APIs, MediatR, gRPC)
6. `dependencies.md` — NuGet packages of note + .NET version
7. `conventions.md` — naming, namespace, DI, error/logging style

`constitution.md` lists each topic file and the one-line cue that a consumer (e.g. `/dai.plan`, `/dai.review`) uses to decide which topic to load. Claude Code routes by description triggers, not by sentence-level instructions, so the historical bulk-load prose was removed.

`/dai.plan` and `/dai.review` reference only the relevant topic file. For example, `/dai.review` reads `conventions.md` and `interfaces.md`; `/dai.plan` reads `architecture.md` and `domain-model.md`. Selective reads cut load by ~80% vs the monolithic constitution.

## Execution

1. **Prereq**: `.dotnet-ai-kit/` exists; if not, tell user to run `/dotnet-ai.init`.
2. **Detect**: reuse `project.yml` if valid; else run `/dotnet-ai.detect`.
3. **Scan**: read aggregates, events, conventions, packages — up to 10 representative files.
4. **Emit** the seven files. Each topic file is ≤200 lines; the index is ≤100 lines.
5. **Bounded skill selection (FR-012)**: keep one architect agent loaded, ≤2 task-specific skills, MCP queries before broad file reads.
6. **Report**: per-topic file size + total count.

## Bounded skill selection

Keep one architect agent for the project type loaded, load at most 2 task-specific skills initially, and run MCP queries (codebase-memory-mcp) before broad file reads.

## Update mode

`--update`: read each existing topic file, merge new findings, annotate changed sections with `(updated {DATE})`.

## Dry-run / errors

- `--dry-run`: print the seven files; never write to disk.
- No .NET projects: write `constitution.md` + `conventions.md` only.
- Detection fails: ask user for project type, then continue.
