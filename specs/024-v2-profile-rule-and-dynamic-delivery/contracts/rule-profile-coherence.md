# Contract: Rule/Profile Coherence

Covers FR-009..FR-014. Verifiable by `Acceptance.Tests`.

## C-RC-1 — No profile restates a universal rule (dedup; prerequisite for always-on)

- **Given** the 5 universal rules (`async-concurrency`, `coding-style`, `existing-projects`, `security`, `tool-calls`) and the 12 profiles,
- **Then** no profile body restates a universal-rule constraint; profiles carry only architecture/role-specific guidance and reference the universal rules.
- **Check**: a deterministic duplication check (e.g., signature-line / normalized-overlap assertion) over `profile × universal-rule` returns an empty set. Must hold **before** always-on profile delivery is exercised so profile + rules never inject the same generic constraint twice.

## C-RC-2 — Three globs narrowed, two kept broad

- `mediator-abstraction` paths ⊆ DI/composition (`**/Program.cs`, `**/*Extensions.cs`, `**/DependencyInjection/**`); no `**/*.cs`.
- `messaging-bus-selection` paths ⊆ DI/messaging composition; no `**/*.cs`.
- `ai-integration` paths ⊆ AI features/namespaces; no `**/*.cs`.
- `error-handling` and `performance` **retain** broad `**/*.cs` scope (assertion that they are NOT narrowed — guards against over-narrowing).

## C-RC-3 — deterministic-enforcement is universal, not fake-path-scoped

- `deterministic-enforcement` has **universal** scope (always-apply, no `paths:`/`globs:`) and reads as a registry/pointer to its analyzer-backed constraints — assertable by frontmatter scope + absence of a path glob.

## C-RC-4 — Testing-rule residue

- `rules/domain/testing.md` (and any touched testing guidance) contains no v1/Python residue (`pytest`, `ruff`, `pip`, `RuntimeMoniker.Net90`). Verifies/extends the 023 removal; a residue guard asserts absence.

## Tests

- `RuleProfileCoherenceTests`: C-RC-1 dedup check; C-RC-2 per-rule glob assertions (narrowed set scoped, broad set still broad); C-RC-3 universal scope; C-RC-4 residue guard.
- `Hosts.Tests` golden: narrowed `.mdc`/`.instructions.md`/`.claude/rules` frontmatter re-accepted.
