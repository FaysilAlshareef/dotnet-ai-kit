# Data Model: Multi-Repo Awareness

**Feature**: 013-multi-repo-awareness | **Date**: 2026-03-30

## Entity: ReposConfig (existing — modified)

**File**: `src/dotnet_ai_kit/models.py`
**Change**: Update `validate_repo_path` field validator

| Field | Type | Validation |
|-------|------|-----------|
| command | Optional[str] | None, local path, `github:org/repo`, GitHub HTTPS URL, git SSH URL |
| query | Optional[str] | Same as above |
| processor | Optional[str] | Same as above |
| gateway | Optional[str] | Same as above |
| controlpanel | Optional[str] | Same as above |

**Normalization rules** (applied in validator, before storage):
- `https://github.com/org/repo` → `github:org/repo`
- `https://github.com/org/repo.git` → `github:org/repo`
- `git@github.com:org/repo.git` → `github:org/repo`
- `github:org/repo` → unchanged
- Local path → strip whitespace, unchanged
- None → unchanged

## Entity: FeatureBrief (new)

**File**: `src/dotnet_ai_kit/models.py`
**Purpose**: Programmatic validation of feature-brief.md content

| Field | Type | Default | Validation |
|-------|------|---------|-----------|
| feature_name | str | (required) | Non-empty string |
| feature_id | str | (required) | Matches pattern `\d{3}-[a-z0-9-]+` |
| projected_date | str | (required) | ISO date format |
| phase | str | (required) | One of: specified, planned, tasks-generated, implementing, implemented, blocked |
| source_repo | str | (required) | Non-empty string (directory name) |
| source_path | str | (required) | Non-empty string (local path or github:org/repo) |
| source_feature_path | str | (required) | Relative path starting with `.dotnet-ai-kit/features/` |
| role | str | "" | Free text description |
| required_changes | list[str] | [] | List of change descriptions |
| events_produces | list[str] | [] | List of event names/descriptions |
| events_consumes | list[str] | [] | List of event names/descriptions |
| tasks | list[dict] | [] | Each dict: id (str), description (str), file (str), done (bool) |
| blocked_by | list[str] | [] | List of upstream repo names |
| blocks | list[str] | [] | List of downstream repo names |
| implementation_approach | str | "" | Free text from plan |

**Phase state transitions**:
```
specified → planned → tasks-generated → implementing → implemented
                                           ↘ blocked
```

## Entity: Feature Brief File (filesystem)

**Location**: `{target-repo}/.dotnet-ai-kit/briefs/{source-repo-name}/{NNN}-{name}/feature-brief.md`

**Directory structure**:
```
.dotnet-ai-kit/
├── features/          ← LOCAL features (own numbering, own lifecycle)
│   └── 001-xxx/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
└── briefs/            ← PROJECTED from other repos (read-only from local perspective)
    ├── source-repo-A/
    │   ├── 001-feature/
    │   │   └── feature-brief.md
    │   └── 002-feature/
    │   │   └── feature-brief.md
    └── source-repo-B/
        └── 002-feature/  ← same number as above, no collision
            └── feature-brief.md
```

**Key invariants**:
- `features/` and `briefs/` are completely independent — never mixed
- Feature numbering scans only `features/`
- `briefs/` is namespaced by source repo name — prevents collisions
- `/dai.init` never touches `briefs/`
- Brief projection is idempotent — overwrites on re-run

## Relationships

```
DotnetAiConfig
  └── repos: ReposConfig  (existing, validator updated)

FeatureBrief (new model)
  → references source repo via source_repo + source_path
  → contains filtered subset of primary feature's spec/plan/tasks

feature-brief.md (filesystem)
  → lives in target repo's briefs/ directory
  → auto-committed to git after projection
```
