# Quickstart: Tool-Wide Quality Hardening

**Branch**: `016-tool-quality-hardening` | **Date**: 2026-04-04

## Implementation Order

Work through parts in severity order. Each part is independently testable.

### Part 1 — Build Packaging Fix (CRITICAL)
**Files**: `pyproject.toml`
**Effort**: Small (2 lines added)
**Test**: Build wheel, inspect contents for `profiles/` and `prompts/`.

### Part 2 — Command Branch Safety (CRITICAL)
**Files**: `commands/clarify.md`, `commands/implement.md`
**Effort**: Small (copy 12-line section from specify.md into each)
**Test**: Line count check, text comparison with specify.md.

### Part 3 — CLI Lifecycle Gaps (HIGH)
**Files**: `src/dotnet_ai_kit/cli.py`, `src/dotnet_ai_kit/config.py`
**Effort**: Medium (4 sub-changes across 2 files)
**Test**: CLI integration tests for init profile, check output, YAML error, upgrade warnings.

### Part 4 — Command File Quality (MEDIUM)
**Files**: 12 command files in `commands/`
**Effort**: Medium (5 sub-changes, mostly text edits)
**Test**: Line counts, flag uniqueness, step ordering validation.
**Note**: copier.py change for COMMAND_SHORT_ALIASES + test.

### Part 5 — Deployment Pipeline (MEDIUM)
**Files**: `src/dotnet_ai_kit/cli.py`, `src/dotnet_ai_kit/copier.py`
**Effort**: Medium (3 sub-changes)
**Test**: Mock-based tests for configure re-deploy, secondary style, git add dirs.

### Part 6 — Config/Model Hardening (MEDIUM)
**Files**: `src/dotnet_ai_kit/models.py`, `templates/config-template.yml`, `src/dotnet_ai_kit/cli.py`
**Effort**: Small-Medium (3 sub-changes)
**Test**: Validator test, template field check, configure-without-init test.

### Part 7 — Skill Activation (MEDIUM)
**Files**: ~72 skill SKILL.md files
**Effort**: Large (bulk frontmatter edits, 69+ files)
**Test**: Grep counts for when-to-use and paths tokens.

### Part 8 — Extension System + Cleanup (MEDIUM)
**Files**: `src/dotnet_ai_kit/extensions.py`, `src/dotnet_ai_kit/cli.py`
**Effort**: Small (2 sub-changes)
**Test**: Extension hook test, init auto-default test.

## Verification

After all parts:
```bash
# Run full test suite
pytest --cov=dotnet_ai_kit

# Lint check
ruff check src/ tests/

# Format check
ruff format --check src/ tests/

# Build and inspect wheel
python -m build
unzip -l dist/*.whl | grep -E "profiles|prompts"

# Skill activation counts
grep -rl "when-to-use" skills/ | wc -l   # target: 80+
grep -rl "detected_paths" skills/ | wc -l  # target: 9+
```
