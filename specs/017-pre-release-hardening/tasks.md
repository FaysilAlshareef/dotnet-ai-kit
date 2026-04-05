---
description: "Task list for 017-pre-release-hardening"
---

# Tasks: Pre-Release v1.0.0 Hardening

**Input**: Design documents from `specs/017-pre-release-hardening/`
**Spec**: 11 user stories (P1×3, P2×5, P3×3) · 50 FRs · 3 severity tiers + docs sync
**Tests**: New tests added per story — no TDD required (bug-fix sprint, behaviour already defined)
**Baseline**: 280 tests passing · 0 ruff errors

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no shared state)
- **[Story]**: Maps to user story (US1–US11)
- All file paths are relative to repo root

---

## Phase 1: Setup

**Purpose**: Create the `utils.py` shared module that `copier.py` and `extensions.py` both depend on. Blocking prerequisite for US1, US2, US3, US6.

- [x] T001 Create `src/dotnet_ai_kit/utils.py` with: (a) `parse_version(version_str)` — strips pre-release suffix (`-beta`, `-rc1`) before splitting on `.`; non-numeric parts → 0; empty string → `(0,)`. See data-model.md interface spec. (b) Two public constants: `HOOK_MODEL: str = "claude-haiku-4-5-20251001"` and `HOOK_TIMEOUT_MS: int = 15_000` with comment `# Update when a new Haiku model is released`. These are placed in utils.py so both copier.py (hook deployment) and cli.py (check --verbose) can import them without cross-module private symbol access.
- [x] T002 [P] Update `src/dotnet_ai_kit/copier.py`: add `from dotnet_ai_kit.utils import parse_version`; remove `_parse_version()` function; replace all `_parse_version(` call-sites with `parse_version(`
- [x] T003 [P] Update `src/dotnet_ai_kit/extensions.py`: add `from dotnet_ai_kit.utils import parse_version`; remove `_parse_version_tuple()` function; replace all `_parse_version_tuple(` call-sites with `parse_version(`
- [x] T004 Create `tests/test_utils.py`: add `test_parse_version_basic` (`"1.2.3"` → `(1,2,3)`), `test_parse_version_pre_release` (`"1.0.0-beta"` → `(1,0,0)`), `test_parse_version_non_numeric` (`"1.a.0"` → `(1,0,0)`), `test_parse_version_empty` (`""` → `(0,)`); also add `test_hook_constants` — assert `HOOK_MODEL` is a non-empty string and `HOOK_TIMEOUT_MS` is a positive int
- [x] T005 Run `pytest tests/test_utils.py` and `ruff check src/dotnet_ai_kit/utils.py` — both must pass before proceeding

**Checkpoint**: `utils.py` live, `_parse_version` and `_parse_version_tuple` deleted from both callers.

---

## Phase 2: Foundational

**Purpose**: No cross-story foundational work beyond Phase 1. All user stories can now proceed independently after Phase 1.

---

## Phase 3: US1 — Short Aliases Work (Priority: P1) 🎯 MVP

**Goal**: `dai.config.md`, `dai.crud.md`, `dai.page.md` deployed on init.

**Independent Test**: `dotnet-ai init --ai claude --style short` in a temp dir → verify `dai.config.md`, `dai.crud.md`, `dai.page.md` exist in `.claude/commands/`; `dai.configure.md`, `dai.add-crud.md`, `dai.add-page.md` absent.

- [x] T006 [US1] Add 3 entries to `COMMAND_SHORT_ALIASES` dict in `src/dotnet_ai_kit/copier.py`: `"configure": "config"`, `"add-crud": "crud"`, `"add-page": "page"` — dict must now have 13 entries total (was 10)
- [x] T007 [US1] Extend `test_command_short_aliases_produce_correct_filenames` in `tests/test_copier.py` to assert `dai.config.md`, `dai.crud.md`, `dai.page.md` are produced; assert `dai.configure.md`, `dai.add-crud.md`, `dai.add-page.md` are NOT produced
- [x] T008 [US1] Run `pytest tests/test_copier.py -k alias` to confirm T007 passes

**Checkpoint**: All 27 documented short aliases now deploy correctly.

---

## Phase 4: US2 — Extension Catalog Friendly Message (Priority: P1)

**Goal**: `dotnet-ai extension-add jira` exits non-zero with yellow "Note:" message and "--dev" guidance, no traceback.

**Independent Test**: Run `dotnet-ai extension-add anything` without `--dev` → check exit code ≠ 0, output contains "not yet supported" and "--dev", no line starting with `Traceback`.

- [x] T009 [US2] Add `class CatalogInstallError(ExtensionError):` at top of `src/dotnet_ai_kit/extensions.py` (near line 20, after existing exception classes). Docstring: "Raised when catalog-based installation is attempted but not yet supported."
- [x] T010 [US2] In `install_extension()` in `src/dotnet_ai_kit/extensions.py`: change `raise ExtensionError("Catalog-based extension install...")` → `raise CatalogInstallError("Catalog-based installs are not yet supported. Use --dev to install from a local path: dotnet-ai extension-add --dev ./my-ext")`
- [x] T011 [US2] In `extension_add()` in `src/dotnet_ai_kit/cli.py`: add `from dotnet_ai_kit.extensions import CatalogInstallError`; add `except CatalogInstallError as exc:` block BEFORE the existing `except ExtensionError` — print `[yellow]Note:[/yellow] {exc}` to `console`, then `raise typer.Exit(code=1)`
- [x] T012 [P] [US2] Add `test_extension_add_catalog_gives_friendly_message` in `tests/test_extensions.py`: call `install_extension("jira", dev=False, project_root=tmp_path)`, assert `CatalogInstallError` raised, message contains "--dev"
- [x] T013 [P] [US2] Add `test_extension_add_catalog_exits_nonzero` in `tests/test_cli.py`: invoke `extension-add jira` via CliRunner, assert exit code 1, "not yet supported" in output, "Error:" NOT at start of output line
- [x] T014 [US2] Run `pytest tests/test_extensions.py tests/test_cli.py -k catalog` — both must pass

**Checkpoint**: `CatalogInstallError` raised; CLI shows yellow Note: not red Error:.

---

## Phase 5: US3 — Hook Model Constants (Priority: P1)

**Goal**: `_HOOK_MODEL` and `_HOOK_TIMEOUT_MS` module constants in copier.py; no inline literals in `copy_hook()`.

**Independent Test**: Grep `copy_hook` body for `"claude-haiku"` → no matches. Grep module top for `_HOOK_MODEL` → found.

- [x] T015 [US3] In `src/dotnet_ai_kit/copier.py`: add `from dotnet_ai_kit.utils import HOOK_MODEL, HOOK_TIMEOUT_MS` at the top (after the existing imports). Remove any local `_HOOK_MODEL` / `_HOOK_TIMEOUT_MS` definitions from copier.py if they were added separately — the canonical values live in `utils.py` (T001).
- [x] T016 [US3] In `copy_hook()` in `src/dotnet_ai_kit/copier.py`: replace inline `"claude-haiku-4-5-20251001"` → `HOOK_MODEL` and `15000` → `HOOK_TIMEOUT_MS`
- [x] T017 [US3] Run `python -c "from dotnet_ai_kit.utils import HOOK_MODEL, HOOK_TIMEOUT_MS; assert HOOK_MODEL; assert HOOK_TIMEOUT_MS == 15000"` to verify constants live in utils.py and are importable

**Checkpoint**: Single change point for hook model updates.

---

## Phase 6: US4 — 14 Commands Get Usage + Examples (Priority: P2)

**Goal**: All 27 command files have `## Usage` and `**Examples:**` blocks.

**Independent Test**: `grep -L "## Usage" commands/*.md` returns empty string.

Each command task: insert 8-line Usage+Examples block immediately after the description paragraph and before the first `##` step/section. For files at 200 lines, trim internal steps first (merge sub-steps) to stay ≤ 200. See `contracts/command-files.md` for exact content per command.

- [x] T018 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/analyze.md` (currently 197 lines → trim 5 lines from Step 3/4 sub-steps, add 8 → ≤200)
- [x] T019 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/clarify.md` (185 → 193)
- [x] T020 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/configure.md` (143 → 151)
- [x] T021 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/detect.md` (146 → 154)
- [x] T022 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/do.md` (179 → 187)
- [x] T023 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/implement.md` (196 → trim 4 lines from Step 5 branches, add 8 → ≤200)
- [x] T024 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/init.md` (117 → 125)
- [x] T025 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/learn.md` (129 → 137)
- [x] T026 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/plan.md` (143 → 151)
- [x] T027 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/pr.md` (162 → 170)
- [x] T028 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/review.md` (188 → 196)
- [x] T029 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/specify.md` (200 → trim 8 lines from Step 2 sub-steps + Step 6 checklist, add 8 → 200)
- [x] T030 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/tasks.md` (200 → trim 8 lines from Step 3 sub-bullets + Step 5 per-repo examples, add 8 → 200)
- [x] T031 [P] [US4] Add `## Usage` + `**Examples:**` to `commands/verify.md` (186 → 194)
- [x] T032 [US4] Verify all 27 files have `## Usage`: run `python -c "import os; files=[f for f in os.listdir('commands') if f.endswith('.md') and '## Usage' not in open('commands/'+f, encoding='utf-8').read()]; print(files); assert not files"`

**Checkpoint**: `grep -L "## Usage" commands/*.md` returns empty.

---

## Phase 7: US5 — Config Typo Warnings (Priority: P2)

**Goal**: Unknown top-level keys in config.yml produce a logged WARNING.

**Independent Test**: Load `DotnetAiConfig(foo="bar")` → WARNING log containing "foo".

- [x] T033 [US5] In `src/dotnet_ai_kit/models.py`: add `import logging` (if not present); add `_KNOWN_CONFIG_KEYS: frozenset[str] = frozenset({"version", "company", "naming", "repos", "permissions_level", "ai_tools", "command_style", "linked_from"})` above `DotnetAiConfig`; add `from pydantic import model_validator` to pydantic imports
- [x] T034 [US5] Add `warn_unknown_keys` `@model_validator(mode="before")` `@classmethod` method to `DotnetAiConfig` class: iterate dict keys, log WARNING for any key not in `_KNOWN_CONFIG_KEYS`. Return values unchanged. Keep `extra="ignore"` in `ConfigDict`.
- [x] T035 [US5] Add `test_dotnet_ai_config_warns_on_unknown_top_level_key(caplog)` in `tests/test_models.py`: construct `DotnetAiConfig(**{"foo": "bar", "company": {"name": "Acme"}})`, assert WARNING in caplog containing "foo"
- [x] T036 [US5] Run `pytest tests/test_models.py -k unknown_top` — must pass

**Checkpoint**: `load_config()` on config with typo key emits WARNING naming the bad key.

---

## Phase 8: US6 — Secondary Repo Gets Its Own Tools (Priority: P2)

**Goal**: `deploy_to_linked_repos()` deploys to secondary's `ai_tools`, not primary's.

**Independent Test**: Set up primary=claude, secondary=cursor; run deploy; verify `.cursor/rules/` populated in secondary, `.claude/commands/` absent.

- [x] T037 [US6] In `src/dotnet_ai_kit/copier.py` `deploy_to_linked_repos()`: find the inner `for tool_name in config.ai_tools:` loop that is INSIDE the secondary repo block (not the outer iteration); change it to `for tool_name in sec_ai_tools:` — `sec_ai_tools` is already extracted from secondary config in the 016 fix
- [x] T038 [US6] Add `test_deploy_loop_uses_secondary_ai_tools` in `tests/test_multi_repo_deploy.py`: configure primary with `ai_tools: [claude]`, secondary with `ai_tools: [cursor]`; mock secondary config; assert cursor tool dirs are targeted (not claude dirs)
- [x] T039 [US6] Run `pytest tests/test_multi_repo_deploy.py -k secondary_ai_tools` — must pass

**Checkpoint**: Secondary repo receives cursor-format files when configured as cursor.

---

## Phase 9: US7 — upgrade --force Refreshes Profile/Hook (Priority: P2)

**Goal**: `upgrade --force` unconditionally re-deploys profile and hook.

**Independent Test**: Run `upgrade --force` with mismatched version; assert `copy_profile()` and `copy_hook()` called.

- [x] T040 [US7] In `src/dotnet_ai_kit/cli.py` `upgrade()`: find the `if was_upgraded:` (or similar version-comparison guard) block that wraps the profile/hook deployment section; change it to `if was_upgraded or force:` so that `upgrade --force` unconditionally re-deploys profile and hook even when the version file already matches
- [x] T041 [US7] Add `test_upgrade_force_redeploys_profile` in `tests/test_cli.py`: patch `copy_profile` and `copy_hook`; set up a project where version already matches; run `upgrade --force`; assert both `copy_profile` and `copy_hook` were called
- [x] T041b [US7] Run `pytest tests/test_cli.py -k upgrade_force` — must include the new test and all must pass

**Checkpoint**: `upgrade --force` always refreshes profile and hook.

---

## Phase 10: US8 — bypassPermissions Warning in JSON (Priority: P2)

**Goal**: `configure --json` with `permissions_level = "full"` includes `"warnings"` in JSON output.

**Independent Test**: Run `configure --no-input --company Acme --permissions full --json` → parse JSON → `"warnings"` key present, contains "bypassPermissions".

- [x] T042 [US8] In `src/dotnet_ai_kit/cli.py` `configure()`: in the JSON output block, after setting `data["status"] = "ok"`, add: `if config.permissions_level == "full": data["warnings"] = ["bypassPermissions enabled — all operations run without confirmation"]`
- [x] T043 [US8] Add `test_configure_json_full_permissions_includes_warnings` in `tests/test_cli.py`: invoke `configure --no-input --company Acme --permissions full --json`; parse JSON; assert `"warnings"` in data and data["warnings"][0] contains "bypassPermissions"
- [x] T044 [US8] Run `pytest tests/test_cli.py -k json_full_permissions` — must pass

**Checkpoint**: CI pipelines see bypassPermissions warning in JSON output.

---

## Phase 11: US9 — Config File Survives Process Kill (Priority: P3)

**Goal**: `save_config()` and `save_project()` use atomic write (`tmp` → `replace`).

**Independent Test**: After `save_config()` succeeds, no `.tmp` file remains in config directory.

- [x] T045 [P] [US9] In `src/dotnet_ai_kit/config.py` `save_config()`: replace `path.write_text(yaml.dump(data), encoding="utf-8")` with atomic pattern: `tmp = path.with_suffix(".tmp"); tmp.write_text(yaml.dump(data), encoding="utf-8"); tmp.replace(path)`
- [x] T046 [P] [US9] In `src/dotnet_ai_kit/config.py` `save_project()`: apply same atomic write pattern
- [x] T047 [US9] Add `test_save_config_no_tmp_after_success` in `tests/test_config.py`: call `save_config(config, path)`, assert `path.with_suffix(".tmp")` does NOT exist; assert `path` exists and is valid YAML
- [x] T048 [US9] Run `pytest tests/test_config.py -k atomic` — must pass

**Checkpoint**: Config writes are atomic on all platforms.

---

## Phase 12: US10 — dotnet-ai changelog Command (Priority: P3)

**Goal**: `dotnet-ai changelog` exits 0 and prints something meaningful.

**Independent Test**: Run `dotnet-ai changelog` in any directory → exit 0, non-empty output.

- [x] T049 [US10] In `src/dotnet_ai_kit/cli.py` add `@app.command("changelog")` function: check `_get_package_dir() / "CHANGELOG.md"` — if exists, print its content and `return`; else run `subprocess.run(["git", "tag", "--sort=-version:refname"], capture_output=True, text=True)`, take first 5 tags, for each run `git log {tag} --format="%ai" -1`, print formatted list and `return`; if no CHANGELOG and no tags, print `"No changelog available."` and `return`. Do NOT raise `typer.Exit` — returning `None` from a Typer command is idiomatic exit 0.
- [x] T050 [US10] Add `test_changelog_command_exits_0` in `tests/test_cli.py`: invoke `changelog` via CliRunner; assert exit code 0
- [x] T051 [US10] Run `pytest tests/test_cli.py -k changelog` — must pass

**Checkpoint**: `dotnet-ai changelog` works, exits 0.

---

## Phase 13: US11 — init --permissions Flag (Priority: P3)

**Goal**: `dotnet-ai init --ai claude --permissions standard` applies permissions without separate configure call.

**Independent Test**: Run `init --ai claude --permissions standard` in .NET project → `.claude/settings.json` has standard allow-list applied.

- [x] T052 [US11] In `src/dotnet_ai_kit/cli.py` `init()`: add `permissions: Optional[str] = typer.Option(None, "--permissions", help="Permission level (minimal/standard/full).")` parameter; after config creation but before saving, if `permissions` is not None, validate it is in `("minimal", "standard", "full")` (raise `typer.BadParameter` if not), then set `config.permissions_level = permissions`
- [x] T053 [US11] Verify `copy_permissions()` is called with the configured level during init (it already is in the existing init flow — confirm the level is respected)
- [x] T054 [US11] Add `test_init_with_permissions_flag_applies_level` in `tests/test_cli.py`: init with `--ai claude --permissions standard`, verify `.claude/settings.json` has content consistent with standard level
- [x] T055 [US11] Add `test_init_permissions_invalid_value_exits_error` in `tests/test_cli.py`: init with `--permissions extreme`, assert non-zero exit and error message
- [x] T056 [US11] Run `pytest tests/test_cli.py -k permissions_flag` — must pass

**Checkpoint**: `init --permissions standard` applies standard allow-list without requiring configure.

---

## Phase 14: Polish — Remaining FRs Not Tied to User Stories

**Purpose**: FR-013 through FR-025, FR-028, FR-029 — quality/safety improvements.

- [x] T057 [P] In `src/dotnet_ai_kit/agents.py`: add `import logging` and `logger = logging.getLogger(__name__)` at module level; in `get_agent_config()` after confirming key is in AGENT_CONFIG, add: `if key not in SUPPORTED_AI_TOOLS: logger.warning("Tool '%s' is recognised but not fully supported in v1.0. Full support planned for v1.1.", tool)` (FR-015)
- [x] T058 [P] In `src/dotnet_ai_kit/copier.py` `_resolve_detected_path_tokens()`: before the `continue` that removes a `paths:` line with empty token, add `logger.debug("Removing paths: line — token %s resolved to empty", key)` (FR-013)
- [x] T059 [P] In `src/dotnet_ai_kit/extensions.py` `after_remove` hook block: change `logger.warning(...)` in the `except (subprocess.CalledProcessError, FileNotFoundError)` block to `raise ExtensionError(f"Extension '{name}' was removed from registry but cleanup hook '{hook_cmd}' failed: {exc}. Manual cleanup may be required.")` (FR-016)
- [x] T060 [P] In `src/dotnet_ai_kit/extensions.py` `_check_conflicts()`: after the command name conflict check, add rule file name collision check — build `existing_rule_names` from all installed extensions' `rules` lists; compare with new extension's rule names; if overlap, raise `ExtensionError(f"Rule file name conflict: {', '.join(sorted(conflicts))}")` (FR-017)
- [x] T061 [P] Add `category: workflow` to `metadata:` block of `skills/workflow/plan-artifacts/SKILL.md` (FR-018)
- [x] T062 [P] Add `category: workflow` to `metadata:` block of `skills/workflow/plan-templates/SKILL.md` (FR-018)
- [x] T063 In `src/dotnet_ai_kit/cli.py` `check()`: after `console.print(table)`, in the `if verbose:` path, iterate `config.ai_tools` and call `_get_tool_status(tool_name, tool_config, target)` for each; if `ts["profile"]` is True, print `console.print(f"  Profile: {tool_config.get('rules_dir', '')}/architecture-profile.md")`; if `ts["hook"]` is True, print `console.print(f"  Hook: model={HOOK_MODEL}, timeout={HOOK_TIMEOUT_MS // 1000}s")` — where `HOOK_MODEL` and `HOOK_TIMEOUT_MS` are imported from `src/dotnet_ai_kit/utils.py` (see T001b below). Do NOT import private constants from copier. (FR-019)
- [x] T064 In `src/dotnet_ai_kit/cli.py` `configure()`: move the init guard `if not (target / ".dotnet-ai-kit").is_dir()` block so it runs only when `not dry_run` — wrap the guard in `if not dry_run:` (FR-020)
- [x] T065 In `src/dotnet_ai_kit/cli.py` `extension_list_cmd()`: if `extensions` list is empty, print `"No extensions installed. Use 'dotnet-ai extension-add --dev <path>' to install one."` and return (FR-022)
- [x] T066 In `src/dotnet_ai_kit/cli.py`: for each of the 5 `except Exception: pass` blocks, add `_verbose_log(verbose, f"Skipping {context}: {exc}")` — contexts: "detected paths from project.yml" (line ~463), "hook deployment" (line ~567), "detected paths in configure" (line ~1642), "profile type from project.yml" (line ~1683), "hook deployment in configure" (line ~1709) (FR-025)
- [x] T067 Create `rules/multi-repo.md`: event contract ownership, branch naming `chore/brief-NNN-name`, deploy order (command→processor→query→gateway→controlpanel), no circular cross-repo dependencies. Must be ≤100 lines with MUST/MUST NOT language. See quickstart.md template. (FR-029)
- [x] T068 [P] Add `test_remove_extension_raises_on_hook_failure` in `tests/test_extensions.py`: mock `subprocess.run` to raise `CalledProcessError`; assert `ExtensionError` raised (not just warning logged) (FR-016 test)
- [x] T069 [P] Add `test_extension_add_raises_on_rule_name_conflict` in `tests/test_extensions.py`: install first extension with `rules/conventions.md`; attempt to install second extension with same rule filename; assert `ExtensionError` raised (FR-017 test)
- [x] T070 [P] Add `test_check_verbose_shows_profile_detail` in `tests/test_cli.py`: init with `--type command`, run `check --verbose`, assert profile path string appears in output (FR-019 test)
- [x] T071 [P] Add `test_configure_dry_run_without_init_shows_preview` in `tests/test_cli.py`: run `configure --dry-run` in temp dir without init; assert exit code ≠ 1 (FR-020 test)
- [x] T072 [P] Add `test_extension_list_empty_shows_message` in `tests/test_cli.py`: run `extension-list` in fresh dir; assert "No extensions installed" in output (FR-022 test)
- [x] T073 Run `pytest --tb=short -q` — must show ≥295 passing, 0 failing
- [x] T074 Run `ruff check src/ tests/` — 0 errors
- [x] T075 Run `ruff format --check src/ tests/` — 0 errors

**Checkpoint**: All Python code changes verified. 295+ tests green, ruff clean.

---

## Phase 15: Documentation Sync

**Purpose**: Update README, CHANGELOG, and 8 planning/ docs to reflect actual codebase state. See `specs/017-pre-release-hardening/docs-gap-analysis.md` for full gap details.

### README.md (FR-030–035)

- [x] T076 `README.md` line 17: update badge stat `15 rules` → `16 rules`
- [x] T077 `README.md` line 75: update plugin install line `15 rules` → `16 rules`
- [x] T078 `README.md` lines 175–194: update skill category table — fix: api:11 (was 7), core:12 (was 7), workflow:5 (was 7), architecture:7 (was 6), security:5 (was 3); remove "unknown" row if present
- [x] T079 `README.md` line 489: update test count from "158 test functions" → "280 tests (295+ with v1.0.0 hardening)"
- [x] T080 `README.md` lines 450–456: update extension commands from `dotnet-ai extension install {name}` → `dotnet-ai extension-add --dev ./my-ext`; note catalog installs show a user-friendly message
- [x] T081 `README.md` lines 217–229: expand rules table to show all 16 rules (currently only 9 listed) — add the 7 missing existing rules plus the new `multi-repo` rule
- [x] T082 `README.md` line 481: update "15 always-loaded convention rules" → "16 always-loaded convention rules"

### CHANGELOG.md (FR-036–041)

- [x] T083 `CHANGELOG.md` line 46: update "158 test functions across 6 test files" → "280 tests across 13 test files"
- [x] T084 `CHANGELOG.md`: add spec-015 Added entries: architecture enforcement (6 new rules), architecture profile deployment (`copy_profile()`), PreToolUse enforcement hook (`copy_hook()`), `deploy_to_linked_repos()` for tooling sync, `linked_from` config field, `FeatureBrief` model, branch safety sections in 5 commands, secondary repo command_style awareness
- [x] T085 `CHANGELOG.md`: add spec-016 Added entries: `check` command Shows Skills/Agents/Profile/Hook columns + linked repos; configure guard (exit 1 without init); configure re-deploys rules/skills/agents; `_get_tool_status()` helper; `after_remove` hook execution; `detected_paths` unknown key validator; `COMMAND_SHORT_ALIASES` 3 alias fixes (`configure→config`, `add-crud→crud`, `add-page→page`); `--list` flag in code-gen commands
- [x] T086 `CHANGELOG.md`: add spec-017 Added entries: `utils.py` + `parse_version()`; `CatalogInstallError` friendly message; `multi-repo.md` rule #16; `dotnet-ai changelog` command; `init --permissions` flag; atomic config writes; verbose logging for skipped operations; configure dry-run guard; upgrade --force refreshes profile/hook; extension-list empty state; bypassPermissions in JSON; check --verbose enrichment; rule name conflict detection; DotnetAiConfig unknown key warning; 14 command Usage+Examples blocks; 2 skill category fields fixed
- [x] T087 `CHANGELOG.md` lines mentioning extension commands: update all occurrences of `extension add/remove/list` → `extension-add/extension-remove/extension-list`
- [x] T088 `CHANGELOG.md` Known Limitations: update "Extension catalog install is not yet available; only --dev local path installs work" → "Extension catalog installs show a user-friendly message with --dev guidance; actual catalog support planned for v1.1"

### planning/ docs (FR-042–050)

- [x] T089 [P] `planning/05-rules-design.md` line 12: update "## Rule Files (15 rules)" → "## Rule Files (16 rules)"; add `multi-repo.md` entry as rule #16 with description of its 4 topic areas
- [x] T090 [P] `planning/06-build-roadmap.md`: update all 15 rows in the v1.0 phases table from `Planned` → `Complete`; update Phase 1.2 rule count from 6 → 16; add note about spec-015/016/017 additions at bottom of v1.0 section
- [x] T091 `planning/07-project-structure.md`: update `src/dotnet_ai_kit/` tree to list all 10 files (add `cli.py`, `models.py`, `config.py`, `copier.py`, `detection.py`, `utils.py`); update `rules/` list from 6 sample rules to all 16; update test file count from 6 → 13
- [x] T092 `planning/08-multi-repo-orchestration.md`: add new section "## Tooling Deployment to Secondary Repos" covering `deploy_to_linked_repos()`, architecture profile via `copy_profile()`, PreToolUse hook via `copy_hook()`, `linked_from` config field, `FeatureBrief` cross-repo projection, `chore/brief-NNN-name` branch safety, secondary repo ai_tools awareness, dirty working directory check
- [x] T093 [P] `planning/10-permissions-config.md`: update config schema example — change `permissions:\n  level: "standard"` → `permissions_level: "standard"` (flat key matching actual pydantic model)
- [x] T094 `planning/12-version-roadmap.md`: (a) mark all 15 v1.0 phase rows `Complete`; (b) expand v1.0 Late Additions section with spec-015/016/017 items; (c) add `dotnet-ai changelog` to CLI commands section; (d) add `init --permissions` flag to init documentation; (e) update template count from "11 scaffolds" → "13 scaffold directories"
- [x] T095 [P] `planning/13-handoff-schemas.md`: add `feature-brief.md` schema section — document the `FeatureBrief` artifact written to secondary repos during `specify`: fields (feature_id, feature_name, phase, source_repo, this_repo_role, projected_date, required_changes, events_produced, events_consumed)
- [x] T096 `planning/16-cli-implementation.md`: (a) update `src/` tree to list all 10 source files; (b) remove `integrations: coderabbit:` from config schema (deferred to v1.1); (c) fix `permissions.level` → `permissions_level` in schema and validation rules; (d) add `linked_from` field to config schema; (e) update extension command examples from `extension add/remove/list` → `extension-add/extension-remove/extension-list`; (f) update `dotnet-ai check` output example to show Skills/Agents/Profile/Hook columns + linked repos panel; (g) update `dotnet-ai init` output to show skills/agents/profile copy lines; (h) fix error table: "AI tool not detected → exit 3" → "No AI tool detected → defaults to claude"; (i) add `init --permissions` flag to init command docs; (j) document `dotnet-ai changelog` as a registered command; (k) update COMMAND_SHORT_ALIASES to 13 entries in any code sample; (l) add note on configure guard (exits 1 if no init, unless --dry-run); (m) add note on configure re-deploying rules/skills/agents
- [x] T097 [P] `planning/04-commands-design.md`: update COMMAND_SHORT_ALIASES code sample (near line 1063) to show 13-entry dict including `configure→config`, `add-crud→crud`, `add-page→page`

**Checkpoint**: All docs accurate. No stale counts, no wrong command names, no "Planned" phases.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately. T002 and T003 can run in parallel after T001.
- **Phase 3–13 (User Stories)**: All depend on Phase 1 completion. After Phase 1, US1–US11 can run in parallel (different primary files per story).
- **Phase 14 (Polish)**: Most tasks are independent of user stories. T063 (check --verbose) depends on T001 (`HOOK_MODEL`/`HOOK_TIMEOUT_MS` in utils.py) — ensure Phase 1 is complete first.
- **Phase 15 (Docs)**: Fully independent of Python changes. Can run in parallel with Phases 3–14.

### File Conflict Map (cannot parallelize same file)

| File | Stories | Notes |
|------|---------|-------|
| `src/dotnet_ai_kit/copier.py` | US1(T006), US3(T015-T016), US6(T037), Phase14(T058) | Do US1+US3 in one copier edit session |
| `src/dotnet_ai_kit/cli.py` | US2(T011), US7(T040), US8(T042), US10(T049), US11(T052), Phase14(T063-T066) | All cli.py edits can batch |
| `src/dotnet_ai_kit/extensions.py` | US2(T009-T010), Phase14(T059-T060) | Batch extensions.py edits |
| `tests/test_cli.py` | Multiple stories | Append all new test functions in one pass |
| `tests/test_extensions.py` | US2(T012), Phase14(T068-T069) | Batch |

### Parallel Opportunities

Within Phase 1: T002 ∥ T003 (different files)
Within Phase 4 (US4 commands): T018–T031 all [P] (14 independent files)
Within Phase 14: T057 ∥ T058 ∥ T059 ∥ T060 ∥ T061 ∥ T062 (all different files)
Within Phase 15: T076–T088 (README/CHANGELOG) ∥ T089–T097 (planning/) ∥ each planning doc independent

---

## Parallel Examples

```bash
# Phase 1 — after T001, run in parallel:
Task: "Update copier.py to use parse_version (T002)"
Task: "Update extensions.py to use parse_version (T003)"

# Phase 4 — all 14 command files in parallel:
Task: "Add Usage+Examples to analyze.md (T018)"
Task: "Add Usage+Examples to clarify.md (T019)"
# ... T020-T031 all simultaneously

# Phase 14 — independent polish tasks:
Task: "agents.py unsupported tool warning (T057)"
Task: "copier.py token debug logging (T058)"
Task: "extensions.py after_remove raises (T059)"
Task: "extensions.py rule conflict check (T060)"
Task: "skill category fields (T061, T062)"

# Phase 15 — docs fully parallel with code:
Task: "README.md all updates (T076-T082)"
Task: "planning/06-build-roadmap.md (T090)"
Task: "planning/07-project-structure.md (T091)"
```

---

## Implementation Strategy

### MVP (Phases 1–5 only — US1+US2+US3 — critical bugs)

1. Phase 1: Create utils.py (T001–T005)
2. Phase 3: Fix 3 broken aliases (T006–T008)
3. Phase 4: Extension catalog friendly message (T009–T014)
4. Phase 5: Hook model constants (T015–T017)
5. **STOP AND VALIDATE**: `pytest` green, grep confirms alias files, grep confirms no inline model literal
6. Release to unblock users who can't type `/dai.config`

### Incremental Delivery

- After MVP: Add US4 (14 commands) — all [P], fast
- Then US5+US6+US7+US8 (P2 stories) — mixed file changes
- Then US9+US10+US11 (P3 stories)
- Then Phase 14 (polish)
- Then Phase 15 (docs) — can start this at any time in parallel

### Full Sprint (all tasks in dependency order)

T001 → T002∥T003 → T004 → T005 → (all US phases in parallel by file) → T073 → T074 → T075 → (all docs phases in parallel)

---

## Task Count Summary

| Phase | Tasks | Parallelizable |
|-------|-------|----------------|
| Phase 1: Setup (utils.py) | 5 | 2 |
| Phase 3: US1 — Aliases | 3 | 0 |
| Phase 4: US2 — Catalog message | 6 | 2 |
| Phase 5: US3 — Hook constants | 3 | 0 |
| Phase 6: US4 — 14 commands | 15 | 14 |
| Phase 7: US5 — Config warnings | 4 | 0 |
| Phase 8: US6 — Deploy loop | 3 | 0 |
| Phase 9: US7 — upgrade --force | 3 | 0 |
| Phase 10: US8 — JSON warnings | 3 | 0 |
| Phase 11: US9 — Atomic writes | 4 | 2 |
| Phase 12: US10 — changelog | 3 | 0 |
| Phase 13: US11 — --permissions | 5 | 0 |
| Phase 14: Polish | 19 | 10 |
| Phase 15: Docs (README+CHANGELOG) | 13 | 5 |
| Phase 15: Docs (planning/) | 9 | 5 |
| **Total** | **98** | **40** |
