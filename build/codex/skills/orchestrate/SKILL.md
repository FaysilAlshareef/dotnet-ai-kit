---
name: orchestrate
description: "Coordinates a multi-repo feature — initializes every affected repo, projects a feature-brief to each, and sequences work by dependency. Use when a feature spans multiple repositories. Do NOT use for single-repo features (use implement) or cross-repo contract checks alone (use analyze)."
---
# /dotnet-ai.orchestrate — Multi-Repo Conductor

Drive a feature across all affected repositories (the multi-repo conductor).

## Usage
```
/dotnet-ai.orchestrate $ARGUMENTS   [--parallel]
```

## Steps
1. Resolve the service map (affected repos + roles + events) from the feature spec / config.
2. Initialize every affected repo (`.dotnet-ai-kit/project.yml` + tooling + the enforcement hook) so conventions fire everywhere.
3. Project a `feature-brief.md` (role, required changes, events consumed/produced) into each repo's `.dotnet-ai-kit/features/NNN/`.
4. Sequence implementation in dependency order (Command → Query/Processor → Gateway → ControlPanel); `--parallel` opts into per-repo subagent fan-out.
5. Branch safety: secondary repos on main get `chore/feature/NNN`; dirty trees are warned and skipped.
6. Report a single cross-repo status view.

A **contract test** asserts every service-map repo ends with a matching feature-brief (awareness cannot silently regress).

This is a user-invoked command (off the always-loaded listing).
