# ADR 0001 — Rewrite dotnet-ai-kit in .NET 10 with a single-source projection engine

**Status**: Accepted (2026-05) · **Supersedes**: the v1 Python CLI

## Context

v1 (Python) authored each assistant's knowledge separately. The corpus drifted between tools, the per-tool manifests churned, and — the load-bearing defect — plugin-native Claude never received the domain rules (`copy_rules` sat in a dead `else` branch), so conventions were unenforced. v1 was never released, so there is no migration or hotfix burden.

## Decision

Rewrite as a **.NET 10 clean/hexagonal CLI** with a **single authored source (`artifacts/`) projected per assistant**, CI-gated by `git diff --exit-code` so drift cannot merge. Add **deterministic enforcement** (a shipped Roslyn analyzer + PreToolUse/Stop hooks) and fix rule delivery (`init` writes `.claude/rules/*.md` with `paths:`). Keep the corpus token-frugal (commands off the always-loaded listing; selection via descriptions + an artifact graph, not a router).

## Consequences

- **+** One source of truth; drift is structurally impossible; the rule-delivery defect is fixed and locked by tests.
- **+** Quality is deterministic (analyzers/CI/Stop-hook cost zero model tokens).
- **+** Reflection-free serialization keeps a future Native-AOT path open.
- **−** A large corpus migration (v1 → `artifacts/`) and a transition period where the Python v1 coexisted as a reference.
- **Gate (met)**: the Python v1 was removed once the .NET CLI fully covered it — the parity assessment confirmed coverage and the acceptance suite is green. The .NET CLI is now the **sole implementation**; no Python remains.

## Distribution

Framework-dependent `dotnet tool` first; per-RID Native AOT deferred until trim-warning-clean. License-light generated code by default (MediatR/AutoMapper/MassTransit are commercial → opt-in).

See `planning/20`–`26` for the full decision record (26 authoritative).
