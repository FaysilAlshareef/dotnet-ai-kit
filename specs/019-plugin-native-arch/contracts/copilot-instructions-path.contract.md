# Contract: `.github/instructions/<scope>.instructions.md`

**Spec source**: FR-004, FR-007, US2 (acceptance scenarios 1, 2, 3)
**Render command**: `dotnet-ai upgrade --copilot`
**Render template**: `agents-copilot-templates/instructions-path.md.j2`

## Purpose

Path-scoped Copilot instructions. One file per logical area of the project (data access, API design, testing, etc.) — the same 11 `DomainRule` areas from FR-011. Read by GitHub Copilot only when the user is editing files within the declared path scope.

## File-name pattern

`.github/instructions/<area>.instructions.md` where `<area>` is a domain area that ACTUALLY APPLIES to the current project.

**Generation rule** (per Codex round-1 critique CP11): files are generated ONLY for areas whose corresponding `detected_paths` entries exist in the project's `.dotnet-ai-kit/project.yml`. A project without a data-access layer (e.g., a console app with no persistence) MUST NOT receive a `data-access.instructions.md`.

Mapping from area name → `detected_paths` key:
- `api-design` → `api_path` or `endpoints_path`
- `architecture` → always generated (every project has an architecture)
- `configuration` → `configuration_path`
- `data-access` → `data_access_path` or `repositories_path`
- `error-handling` → always generated (every project has error handling)
- `localization` → `localization_path` (skip if absent)
- `multi-repo` → generated only for `microservice` branch projects
- `naming` → always generated (uses runtime `${Company}/${Domain}` substitution)
- `observability` → `logging_path` or `telemetry_path`
- `performance` → always generated
- `testing` → `tests_path` (skip if absent)

The five `ConventionRule` files are NOT rendered as path-scoped instructions because they are always-on — they live in the repository-wide `copilot-instructions.md`. Total path-scoped files generated: between 4 (minimal app: architecture + error-handling + naming + performance) and 11 (full microservice project).

## Required frontmatter

Per GitHub Copilot docs (`https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot` lines 730-735):

```yaml
---
applyTo:
  - <glob 1>
  - <glob 2>
---
```

The `applyTo` array is computed from each `DomainRule`'s `loads_when` field plus the project's `detected_paths` mapping (so `data-access.instructions.md` scopes to whatever path the project uses for its data layer, e.g., `**/Infrastructure/**`, `**/Persistence/**`, `**/Repositories/**`).

## Required content blocks

1. The `DomainRule` body (e.g., `rules/domain/data-access.md` content)
2. Any project-specific overrides resolved from `ProjectMetadata` (e.g., naming substitution for `naming.md`)
3. Pointer back to `.github/copilot-instructions.md` for the always-on conventions

## Freshness contract

Same as `copilot-instructions.md` (see `copilot-instructions.contract.md`).

## Token / size limits

Each file SHOULD remain under ~1500 tokens. The render template MUST fail loudly (non-zero exit, clear message) if a `DomainRule` body produces a file over 2500 tokens after `ProjectMetadata` substitution.

## Path collision rules

Per FR-008 / A-008, these files are owned by the tool's managed-file manifest. Pre-existing developer-authored files in `.github/instructions/` MUST be preserved per the manifest rule.
