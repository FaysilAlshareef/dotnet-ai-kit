# Contract: `.github/copilot-instructions.md`

**Spec source**: FR-004, FR-007, US2 (acceptance scenario 1)
**Render command**: `dotnet-ai upgrade --copilot`
**Render template**: `agents-copilot-templates/copilot-instructions.md.j2`

## Purpose

Repository-wide Copilot instructions file. Single content class per the three logical content classes (FR-007). Read by GitHub Copilot at every interaction with the repository.

## Required content blocks

1. **Project identity** — company, domain, side, project_type from `ProjectMetadata` (current values at render time)
2. **Always-on conventions** — the 5 `ConventionRule` bodies inlined verbatim (because Copilot has no plugin-root path substitution mechanism)
3. **Pointers to path-scoped guidance** — references to the `.github/instructions/*.instructions.md` files generated for this project (FR-007)
4. **Architecture profile snippet** — the active profile body (one of 12 per clarify Q1) inlined verbatim
5. **Per-agent quick reference** — list of `.github/agents/*.agent.md` files Copilot can route to

## Freshness contract

Per spec FR-017 and SC-006:
- `dotnet-ai check` reports staleness if any of:
  - The convention rule bodies on disk differ from those baked into the rendered file
  - The active profile body differs from what's baked in
  - The `ProjectMetadata` has changed since render time
- `dotnet-ai upgrade --copilot` re-renders the file using current `ProjectMetadata` + current plugin source
- The render is recorded in `.dotnet-ai-kit/manifest.json` with `host_owner: "copilot"`, content hashed, source_template captured

## Token / size limits

No explicit token budget (Copilot has no SessionStart equivalent), but the file SHOULD remain under ~3000 tokens to fit comfortably in Copilot's context window. The render template SHOULD be designed so that adding new conventions does not inflate this past the practical limit.

## Path collision rules

Per FR-008 / A-008, this file is owned by the tool's managed-file manifest. Default behavior on pre-existing file:

- If the developer authored content at `.github/copilot-instructions.md` before init, `init` MUST detect the existing file, classify it as user-modified (not in the manifest), and preserve it. The tool emits a clear corrective error and exits non-zero. This is the safe default.

Opt-in override per spec FR-008 ("unless the user explicitly opts in to that exact path"):

- `dotnet-ai init --force-render .github/copilot-instructions.md` (or equivalent path-specific flag) MUST allow the user to explicitly opt in to overwriting a pre-existing file at that exact path. The flag MUST be path-specific (it does NOT bypass the protection for OTHER unmanaged paths). After opt-in, the file is recorded in the managed-file manifest with the user's explicit consent flag.
