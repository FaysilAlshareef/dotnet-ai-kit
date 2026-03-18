# Data Model: Fix Tool Quality Issues

**Branch**: `004-fix-tool-issues` | **Date**: 2026-03-18

## Entities

### DetectionSignal

Represents a single indicator found during project analysis.

| Field | Type | Description |
| ----- | ---- | ----------- |
| pattern_name | string | Human-readable name (e.g., "AggregateRoot base class") |
| signal_type | enum | `naming`, `code-pattern`, `structural`, `build-config` |
| target_project_type | string | Which project type this signal supports (e.g., `command`, `query-sql`) |
| confidence | enum | `high`, `medium`, `low` |
| weight | int | Scoring weight (high=3, medium=2, low=1) |
| evidence | string | The actual match found (e.g., file path + matched line) |
| is_negative | bool | If true, this signal reduces confidence for the target type |

### DetectedProject (extended)

Extends the existing `DetectedProject` pydantic model with new fields for signal-based detection. Not a separate model — the existing model in `models.py` is enriched.

**Existing fields** (unchanged): mode, project_type, dotnet_version, architecture, namespace_format, packages

**New fields added**:

| Field | Type | Description |
| ----- | ---- | ----------- |
| confidence | enum | `high`, `medium`, `low` |
| confidence_score | float | Numeric score (0.0-1.0) |
| top_signals | list[dict] | Top 3 signals that contributed most to classification (serialized DetectionSignal) |
| user_override | string or None | User's override if they changed the type |

### DetectionScoreCard

Internal scoring used to determine classification.

| Field | Type | Description |
| ----- | ---- | ----------- |
| project_type | string | The candidate project type |
| positive_score | float | Sum of positive signal weights |
| negative_score | float | Sum of negative signal weights |
| net_score | float | positive_score - negative_score |
| signal_count | int | Number of signals contributing |

### ConfigOption (for interactive configure)

| Field | Type | Description |
| ----- | ---- | ----------- |
| key | string | Config key (e.g., `permissions_level`) |
| label | string | Human-readable label |
| description | string | Help text for the option |
| input_type | enum | `select-single`, `select-multiple`, `text-input` |
| choices | list[Choice] or None | Available choices (for select types) |
| default_value | any | Default/current value |
| validator | callable or None | Validation function (for text inputs) |

### Choice (for ConfigOption)

| Field | Type | Description |
| ----- | ---- | ----------- |
| value | string | Internal value to store |
| label | string | Display label |
| description | string | Brief help text |
| selected | bool | Whether currently selected (for multi-select) |

## Relationships

```
DetectedProject 1──* DetectionSignal (via top_signals, serialized)
DetectedProject 1──* DetectionScoreCard (internal, one per candidate type during scoring)
```

> **Note**: `ConfigOption` and `Choice` are conceptual entities for the configure UX. They are not implemented as pydantic models — the interactive prompts are built directly using `questionary` and `rich.prompt` APIs with inline choice definitions.

## State Transitions

### Detection Flow

```
Scanning → Signals Collected → Scoring → Classification → Summary Displayed → [User Override?] → Final Result Saved
```

### Configure Flow

```
Load Existing Config → Present Options → User Selects/Types → Validate → Save Config
```

## Validation Rules

- `DetectedProject.confidence_score` must be between 0.0 and 1.0
- `DetectedProject.project_type` must be one of the defined enum values (including new `hybrid`)
- `DetectedProject.top_signals` contains at most 3 items
- Company name must match `^[A-Za-z_][A-Za-z0-9_]*$` (C# identifier)
- GitHub org must match `^[A-Za-z0-9]([A-Za-z0-9\-]*[A-Za-z0-9])?$`
