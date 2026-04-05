# Contract: copier.py New Functions

## copy_profile()

```python
def copy_profile(
    target_root: Path,
    tool_name: str,
    project_type: str,
    confidence: str = "high",
) -> Path | None:
```

**Behavior**:
- Looks up `PROFILE_MAP[project_type]`. If not found or confidence is "low", uses `FALLBACK_PROFILE`.
- Gets rules directory from `AGENT_CONFIG[tool_name]["rules_dir"]`.
- Copies profile to `target_root / rules_dir / "architecture-profile.md"`.
- Returns the deployed path, or None if tool has no rules_dir.

**Error handling**: If source profile doesn't exist, raises FileNotFoundError.

---

## copy_hook()

```python
def copy_hook(
    target_root: Path,
    profile_path: Path,
) -> bool:
```

**Behavior**:
- Reads the profile file and extracts constraint text (everything after frontmatter `---`).
- Loads `templates/hook-prompt-template.md` and renders with `constraints` variable.
- Reads `target_root / ".claude/settings.json"` (or creates if missing).
- Adds/updates the PreToolUse hook entry under `hooks` key.
- Returns True if hook was written, False if skipped.

**Error handling**: If profile_path doesn't exist, returns False.

---

## deploy_to_linked_repos()

```python
def deploy_to_linked_repos(
    primary_root: Path,
    config: DotnetAiConfig,
    tool_version: str,
    dry_run: bool = False,
) -> list[dict]:
```

**Behavior**:
- Iterates `config.repos` fields (command, query, processor, gateway, controlpanel).
- For each non-None local path: check initialization, version-check, deploy tooling.
- Returns a list of result dicts: `{"repo": path, "status": "deployed"|"skipped"|"failed", "reason": str}`.
- On failure for one repo, logs and continues to next (per clarification Q1).

**Error handling**: Catches exceptions per-repo, logs them, continues.

---

## copy_agents() — Updated Signature

```python
def copy_agents(
    source_dir: Path,
    target_dir: Path,
    tool_name: str = "claude",
) -> int:
```

**New behavior**: If `tool_name` has an entry in `AGENT_FRONTMATTER_MAP`, parse universal frontmatter from each source file and transform to tool-specific format. If no mapping exists, log warning and skip.

**Returns**: Count of agents deployed.

---

## copy_skills() — Updated Signature

```python
def copy_skills(
    source_dir: Path,
    target_dir: Path,
    detected_paths: dict[str, str] | None = None,
) -> int:
```

**New behavior**: If `detected_paths` is provided, resolve `${detected_paths.*}` tokens in SKILL.md frontmatter. If a token references a missing key, remove the entire `paths:` line.

**Returns**: Count of skills deployed.
