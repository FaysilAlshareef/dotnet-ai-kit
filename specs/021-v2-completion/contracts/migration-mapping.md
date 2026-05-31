# Contract: v1 → v2 migration mapping (the script's spec)

The throwaway migration script MUST implement exactly this transform. After it runs, `repo.Load()` MUST be Ok (0 broken edges) and `generate --check` MUST be drift-clean.

| v1 source | v2 target | Transform |
|---|---|---|
| `skills/<cat>/<name>/SKILL.md` | `artifacts/skills/<cat>/<name>/SKILL.md` | keep `name` (== dir), `description`, `metadata.{category,agent}`; **drop `when_to_use`**; add `metadata.paths` if location-specific; preserve body verbatim |
| `commands/<name>.md` | `artifacts/skills/commands/<name>/SKILL.md` | `name=<name>`; `metadata.kind: command`; `metadata.invocation: disable-model-invocation`; description from v1; body verbatim |
| `agents/<name>.md` (shipped set) | `artifacts/agents/<name>.md` | keep `name`/`description`/body; add `metadata.skills:` = CSV of skills whose `metadata.agent == <name>`; add `metadata.routing-intents` if derivable |
| `agents/dotnet-ai-architect.md` | `tests/fixtures/` | NOT a shipped agent (Cursor spike) |
| `rules/conventions/<n>.md` (5) | `artifacts/rules/conventions/<n>.md` | must be exactly {async-concurrency, coding-style, existing-projects, security, tool-calls}; `name`=file; description from v1; body verbatim |
| `rules/domain/<n>.md` (11) | `artifacts/rules/domain/<n>.md` | `metadata.paths` set (JIT scope); description from v1; body verbatim |
| `rules/cursor/*.mdc` | — | IGNORED (v1 generated projection, not source) |
| `profiles/<arch>.md` (12) | `artifacts/profiles/<arch>.md` | description + constraint body; `metadata.paths` for the architecture scope |
| `knowledge/<topic>.md` (16) | `artifacts/knowledge/<topic>.md` | description + body |

## Consolidations (done in-pass; rewrite references to the survivor)
- `api/controllers` → **`api/controller-patterns`** (drop source; rewrite refs)
- `api/scalar` → **`api/openapi-scalar`**
- `architecture/cqrs-basics` → a CQRS **decision-guide** linking `cqrs/`

## Invariants the script asserts (fail loudly, don't ship)
- every emitted skill: `frontmatter.name == directory name`
- every `metadata.agent` and every agent `metadata.skills` entry resolves to a migrated artifact (no dangling edge after consolidation)
- `conventions/` contains exactly the 5 whitelist rules; everything else is `domain/` with `paths`
- no `when_to_use` field remains
- output is deterministic (stable ordering) so re-running yields no diff

## Verification (after the script)
1. `repo.Load(artifacts/)` → `Ok == true`, `Errors` empty
2. `generate --out build/` then `generate --check` → no drift
3. corpus-integrity test green
