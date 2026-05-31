# Contract: Skill resource set — authoring, loading, projection (FR-022-01..05)

## On-disk layout (authored, opt-in per AR-5)

```text
artifacts/skills/<category>/<name>/
├── SKILL.md            # required (≤500 lines)
├── scripts/            # optional — .py default (+ .ps1/.sh siblings); executable → trust-governed
├── examples/           # optional — compilable C# (a real project/file)
├── references/         # optional — .md long-form, loaded on demand
├── assets/             # optional — .json / templates / diagrams
└── evals/cases.jsonl   # optional — triggering cases (see eval-cases.schema.md)
```

## Required-set rules (corpus-integrity test)

| Skill kind | MUST have |
|---|---|
| command-skills `constitution`/`checklist`/`fix`/`release` | `scripts/` (non-empty) |
| code-gen command-skills `add-*` | `examples/` (≥1 compilable C#) |
| ambiguous-cluster skills | `evals/cases.jsonl` |
| all others | nothing (bare `SKILL.md` is valid) |

A declared resource dir that is empty, or any resource file that is missing/unreadable, FAILS corpus load (broken-resource error).

## Loading (`FileSystemArtifactRepository`)

`Load()` populates `Skill.Resources : SkillResourceSet` from the subdirs above; executable scripts get a `ScriptTrust` (AutoRun=false).

## Projection (every `IHostProjector`)

Each host copies the skill's resource set into `build/<host>/skills/<name>/<resource>/` **byte-stable**; `generate --check` stays drift-clean. No resource is executed at projection time. (Codex/Cursor/Copilot copy the same set under their own skill dir.)

## Trust (FR-022-05 / FR-J)

Bundled executable scripts are **declared, never auto-run without consent**, provenance = Bundled, cross-platform (`.py` default + `.ps1`/`.sh`). The kit never invokes a bundled script implicitly.
