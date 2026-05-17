---
name: dotnet-ai-architect
description: Cursor sub-agent fixture for the A-005 spike (CHK003)
host_overrides:
  cursor:
    model: claude-sonnet-4
    readonly: false
  claude:
    role: advisory
---

# .NET Architecture Specialist (Cursor Spike Fixture)

**Purpose**: This is the spike fixture for the Cursor sub-agent capability per
spec A-005 / SC-008 / OOS-005 and `cursor-fixture-decision.contract.md`. If
this agent loads in Cursor and appears in the host's sub-agent listing
(`tests/integration/test_smoke_cursor.py` passes in CI), the release ships
full Cursor sub-agent generation. If the fixture fails, the release scope is
revised per the fail-path in the contract.

## Responsibilities

- Review .NET project architecture decisions
- Recommend Clean Architecture / VSA / DDD / Modular Monolith patterns
- Read-only mode (`readonly: false` is intentional — needed to write
  ADR documents during architecture review sessions)
