# Documentation & Planning Docs Gap Analysis

**Date**: 2026-04-04
**Scope**: All 18 planning/ docs + README.md + CHANGELOG.md vs actual codebase state
**Purpose**: Full inventory of what needs updating in docs as part of spec-017

---

## Actual Codebase State (ground truth)

| Asset | Actual Count/State |
|-------|-------------------|
| Rules | **15** (multi-repo.md added in 017 → will be **16**) |
| Agents | 13 |
| Skills | 120 across 17 categories |
| Commands | 27 |
| Knowledge docs | 16 |
| Templates (dirs) | 13 project dirs + config-template.yml + hook-prompt-template.md |
| Permission configs | 4 |
| Python source files | 9 (utils.py added in 017 → will be **10**) |
| Tests passing | **280** (will be ~295 after 017) |
| CLI commands | init, check, upgrade, configure, extension-add, extension-remove, extension-list (changelog added in 017 → **8**) |
| CLI version | 1.0.0 |
| Extension commands | `extension-add`, `extension-remove`, `extension-list` (NOT `extension add/remove/list`) |

### Skill categories (actual):
microservice:33, core:12, api:11, data:8, docs:8, architecture:7, cqrs:6, devops:5, security:5, workflow:5, infra:4, testing:4, observability:3, quality:3, resilience:3, unknown:2, detection:1

### New functions added in specs 015/016 (not in any planning doc):
- `copy_profile()` — deploys architecture profile markdown to rules dir
- `copy_hook()` — injects PreToolUse enforcement hook into settings.json
- `deploy_to_linked_repos()` — orchestrates full tooling deploy to secondary repos
- `_get_tool_status()` — shared helper for check command (JSON + rich table)
- `FeatureBrief` model — cross-repo feature projection
- `linked_from` config field — marks secondary repos

### Config schema changes (not in any planning doc):
- `integrations:` section removed from config-template.yml (deferred)
- `permissions.level` → `permissions_level` (flat key, not nested)
- `linked_from` new top-level key
- `repos:` section now supports `github:org/repo` URL format with normalization

---

## File-by-File Gap Report

---

### `planning/01-vision.md` — MINOR GAPS

| Gap | Details |
|-----|---------|
| v1.0 Additions section incomplete | Lists 8 late additions. Missing: 6 new enforcement rules (arch-enforcement spec 015), architecture profile deployment, PreToolUse enforcement hook, multi-repo deploy tooling (`deploy_to_linked_repos`), `linked_from` field, `FeatureBrief` model, branch safety sections in commands, secondary repo command_style awareness, `_get_tool_status` helper, check command now shows Skills/Agents/Profile/Hook columns |
| Rule count | Says "9 always-loaded coding conventions" in How It Works section. Actual: 15 (will be 16) |
| v1.1 Planned section | Still accurate — no changes needed |

---

### `planning/02-skills-inventory.md` — NO GAPS

Core microservice skills are described. No counts to update. Content is evergreen.

---

### `planning/03-agents-design.md` — MINOR GAPS

| Gap | Details |
|-----|---------|
| AGENT_FRONTMATTER_MAP | Doc may describe the transformation but not the deployed state. No breaking gaps. |

---

### `planning/04-commands-design.md` — MINOR GAPS

| Gap | Details |
|-----|---------|
| Section G alias table | `/dai.config`, `/dai.crud`, `/dai.page` ARE correctly documented here (line 1039-1050). The bug was in the code, not this doc. |
| COMMAND_SHORT_ALIASES code sample | Line ~1063 mentions short alias generation but does not show the 10-entry (now 13-entry) dict. Should be updated to 13 entries. |
| Usage/Examples | The 14 commands being fixed in spec-017 will gain Usage blocks. The design doc can reference this as complete. |
| Branch safety sections | 5 commands now have "Secondary Repo Branch Safety" sections. Doc does not mention this pattern. |

---

### `planning/05-rules-design.md` — MEDIUM GAPS

| Gap | Line | Details |
|-----|------|---------|
| Rule count heading | 12 | Says "15 rules". After spec-017: **16 rules**. |
| Missing multi-repo.md | — | `multi-repo.md` not listed. Add as rule #16. |
| Missing 9 rules from original 6 | The doc describes 6 rules in Phase 1. Ten were added later (api-design, async-concurrency, data-access, observability, performance, security, tool-calls, configuration, naming, testing, error-handling, existing-projects, localization, coding-style). Only 6 are described in detail. |
| Budget note | Says "~600 lines total". Actual: 15 rules × avg ~55 lines = ~825 lines. Says "~900 lines total" in constitution. Update to match. |

---

### `planning/06-build-roadmap.md` — MAJOR GAPS

| Gap | Line | Details |
|-----|------|---------|
| All 15 v1.0 phases say "Planned" | 5-19 | Every phase: "Planned". Should be "**Complete**". |
| Phase 1.2 says "6 rules" | ~35 | Delivered 15 rules (will be 16). |
| Phase 13 says "13 templates" | ~178 | Actual: 13 project dirs (correct count). |
| No mention of spec-015/016 work | — | Architecture enforcement, multi-repo tooling deploy, profile/hook system, `deploy_to_linked_repos`, `linked_from`, `FeatureBrief` — none documented. |
| No mention of spec-017 additions | — | `utils.py`, `changelog` command, `--permissions` on init, `multi-repo.md`, `CatalogInstallError` not listed. |
| Phase 16 (v1.1) | — | Still accurate as future work. |

---

### `planning/07-project-structure.md` — MAJOR GAPS

| Gap | Line | Details |
|-----|------|---------|
| `src/dotnet_ai_kit/` tree incomplete | ~20 | Lists only `__init__.py`, `agents.py`, `extensions.py`. Missing: `cli.py`, `models.py`, `config.py`, `copier.py`, `detection.py`. After 017: also `utils.py`. |
| `rules/` tree | ~116 | Shows 6 rules. Should show all 15 (will be 16). |
| `templates/` count | ~116 | Says "13 templates". Correct for dirs, but also has `config-template.yml` and `hook-prompt-template.md` in the dir. |
| `skills/` category list | — | Not detailed in structure doc. Now 17 categories. |
| New directories/files | — | Missing: `profiles/` (12 profile markdown files), `prompts/` (1 prompt file), `specs/` (feature spec dirs), `.specify/` |
| Test files | — | Says 6 test files. Now 13 test files. |
| Planning doc index | ~154-165 | All 18 planning docs listed. Still accurate. |
| `15-template-content.md` note | ~161 | Says "11 project template file structures". Actual: 13 dirs in templates/. |

---

### `planning/08-multi-repo-orchestration.md` — MAJOR GAPS

| Gap | Details |
|-----|---------|
| Tooling deployment | Entire concept of `deploy_to_linked_repos()` — deploying commands/rules/skills/agents to secondary repos — is absent. This is a major spec-015 feature. |
| Architecture profile | `copy_profile()` — deploying an architecture-specific profile.md to secondary repo's rules dir — not documented. |
| Enforcement hook | `copy_hook()` — PreToolUse hook injection into secondary repo's settings.json — not documented. |
| `linked_from` field | Config field marking secondary repos as linked — not documented. |
| `FeatureBrief` model | Cross-repo feature brief projection (writing feature-brief.md to each secondary repo) — not documented. |
| Branch safety pattern | `chore/brief-NNN-name` branch naming in clarify/implement/plan/specify/tasks commands — not documented. |
| Secondary repo command_style | Secondary repos use their own `command_style` from their config.yml — not documented. |
| `sec_ai_tools` | Secondary repos deploy to their own ai_tools (not primary's) — not documented. |
| Version check | Skipping secondary repos with newer CLI version than primary — not documented. |
| Dirty working directory check | Skip on dirty secondary repos — not documented. |

---

### `planning/09-review-and-coderabbit.md` — MINOR GAPS

No breaking gaps. CodeRabbit integration is still planned/optional. Content is accurate.

---

### `planning/10-permissions-config.md` — MINOR GAPS

| Gap | Details |
|-----|---------|
| `permissions.level` key | Doc shows `permissions.level: "standard"` nested syntax. Actual model uses flat `permissions_level: standard`. |
| bypassPermissions warning | `--json` mode now includes warnings array for full level. Not documented. |
| `--global` flag | May be mentioned. Confirm still accurate. |

---

### `planning/11-expanded-skills-inventory.md` — MINOR GAPS

| Gap | Details |
|-----|---------|
| Category counts | May show older counts. Actual: workflow:5 (not 7 as README shows), api:11 (not 7 as README shows). See actual breakdown above. |

---

### `planning/12-version-roadmap.md` — MAJOR GAPS

| Gap | Line | Details |
|-----|------|---------|
| All v1.0 phases say "Planned" | 17-31 | Every phase status: "Planned". Should be "**Complete**". |
| Phase 13 template count | 29 | Says "11 project scaffolds". Actual: 13 template dirs. |
| `dotnet-ai changelog` | — | Not listed as a CLI command. Added in spec-017. |
| `dotnet-ai init --permissions` | — | `--permissions` flag not documented. Added in spec-017. |
| v1.0 Late Additions | 51-64 | Missing: arch enforcement rules (015), profile/hook system (015), multi-repo tooling deploy (015), `linked_from`/`FeatureBrief` (015), quality hardening (016), configure guard (016), check table columns (016), secondary repo deploy loop fix (016), 3 alias fixes (017), `utils.py` (017), `CatalogInstallError` (017), `multi-repo.md` rule (017). |
| Known Limitations section | — | "Extension catalog install not yet available" — should be updated to note the friendly error message now shown instead of crash. |

---

### `planning/13-handoff-schemas.md` — MINOR GAPS

| Gap | Details |
|-----|---------|
| `FeatureBrief` schema | `feature-brief.md` written to secondary repos during `specify` (spec-015). Not in handoff schemas. Add schema for this artifact. |
| `event-flow.md` | Generated by `plan` step. May need clarification on ownership. |

---

### `planning/14-generic-skills-spec.md` — NO GAPS

Skill content specifications. Evergreen, no counts to update.

---

### `planning/15-template-content.md` — MINOR GAPS

| Gap | Details |
|-----|---------|
| Template count in title | Says "13 project template file structures". May need "15 template files total (13 dirs + config-template.yml + hook-prompt-template.md)". |

---

### `planning/16-cli-implementation.md` — MAJOR GAPS

| Gap | Line | Details |
|-----|------|---------|
| `src/` tree | 12-21 | Shows 3 files. Missing: `cli.py`, `models.py`, `config.py`, `copier.py`, `detection.py`. After 017: also `utils.py`. |
| Config schema | 260-295 | Shows `integrations: coderabbit:` section. **Removed** from actual config (deferred). |
| Config schema | 277 | Shows `permissions.level` nested. Actual: `permissions_level` flat key. |
| Config schema | — | Missing `linked_from` field. |
| Config schema | — | Missing `repos.*` github: URL normalization. |
| Extension commands | 114, 300-303 | Shows `dotnet-ai extension add/remove/list`. Actual registered commands: `extension-add`, `extension-remove`, `extension-list` (hyphenated). |
| `dotnet-ai check` output | 413+ | Shows "27 commands, 15 rules" in check output. Now shows: commands, rules, **skills, agents, profile, hook** columns. Also shows linked_from, detected_paths, linked_repos in config panel. |
| `dotnet-ai init` output | ~400 | Shows "Copied: 27 commands → .claude/commands/. Copied: 15 rules → .claude/rules/". Also now copies skills, agents, optionally profile+hook. |
| Error table | ~380 | "AI tool not detected → exit 3". Fixed: now auto-defaults to claude. |
| New copier functions | — | `copy_profile()`, `copy_hook()`, `deploy_to_linked_repos()`, `_get_tool_status()` — none documented. |
| `COMMAND_SHORT_ALIASES` | ~239 | References command_style but not the alias dict. 13-entry dict not shown. |
| `init --permissions` flag | — | Not documented. Added in spec-017. |
| `dotnet-ai changelog` | — | Not documented. Added in spec-017. |
| `configure` guard | — | `configure` now exits code 1 if `.dotnet-ai-kit/` not present (unless `--dry-run`). |
| `configure` re-deploy | — | `configure` now re-deploys rules/skills/agents after saving config. Not documented. |
| Validation rules | 292 | `permissions.level` validator references wrong key name. |
| `CatalogInstallError` | — | Catalog install now shows friendly message (not crash). Not documented. |

---

### `planning/17-code-generation-flows.md` — MINOR GAPS

| Gap | Details |
|-----|---------|
| `--dry-run` / `--list` flags | Spec-016 renamed second `--dry-run` occurrence to `--list` in code-gen commands. |
| Artifact ownership | `service-map.md` owned by specify, `event-flow.md` owned by plan — not reflected if doc shows otherwise. |

---

### `planning/18-microservice-skills-spec.md` — NO GAPS

Skill content specs. Evergreen.

---

### `README.md` — MAJOR GAPS

| Gap | Line | Details |
|-----|------|---------|
| Badge/header line | 17 | `15 rules` → **16 rules** (after 017), `14 templates` → actual is 13 project dirs |
| Plugin install text | 75 | "15 rules" → **16 rules** |
| Test count in structure | 489 | "158 test functions" → **280 tests** (295+ after 017) |
| Rule count in structure | 481 | "15 always-loaded convention rules" → **16 rules** (after 017) |
| Template count in structure | 485 | "13 project templates" — correct for dirs, but mention config-template + hook-prompt-template too |
| Rules section | 217-229 | Shows 9 rules in table. There are 15 rules (16 after 017). Table is severely incomplete. |
| Extension commands | 450-456 | Shows `dotnet-ai extension install {name}`. Actual: `dotnet-ai extension-add --dev ./path` (no catalog). |
| Skill category table | 175-194 | Counts are wrong: API shows 7 (actual 11), Core shows 7 (actual 12), Workflow shows 7 (actual 5), Architecture shows 6 (actual 7), Security shows 3 (actual 5). |
| New CLI features | — | Missing: `--permissions` on init, `dotnet-ai changelog`, configure guard, multi-repo tooling deployment, profile/hook system. |
| Unknown Limitations | — | Should note extension catalog shows friendly message (not crash). |
| Multi-repo features | 367-376 | Correct in intent. Could mention `deploy_to_linked_repos` deploys tooling too. |

---

### `CHANGELOG.md` — MAJOR GAPS

| Gap | Line | Details |
|-----|------|---------|
| Test count | 46 | "158 test functions across 6 test files" → **280 passing across 13 test files** |
| Rule count | 26 | "15 always-loaded coding convention rules" → **15 currently, 16 after 017** |
| Missing spec-015 additions | — | Architecture enforcement rules (6 new), `copy_profile()`, `copy_hook()`, `deploy_to_linked_repos()`, `linked_from`, `FeatureBrief`, branch safety in commands, secondary repo awareness |
| Missing spec-016 additions | — | `check` command new columns (Skills/Agents/Profile/Hook), configure guard, configure re-deploys, check linked repos, check linked_from, `COMMAND_SHORT_ALIASES` alias fixes (3 corrected in 017), `_get_tool_status` helper, `after_remove` hook execution, detected_paths validator |
| Missing spec-017 additions | — | `utils.py` + `parse_version()`, `CatalogInstallError`, `multi-repo.md` rule, `dotnet-ai changelog`, `init --permissions`, atomic config writes, verbose except blocks, configure dry-run guard, upgrade --force profile/hook, extension-list empty state, bypassPermissions in JSON, check --verbose enrichment, rule name conflict detection, DotnetAiConfig unknown key warning, 14 command Usage+Examples blocks |
| Extension command names | — | Should use `extension-add`/`extension-remove`/`extension-list` (hyphenated) throughout |
| Known Limitations | 79-82 | "Extension catalog install is not yet available" — update: "catalog installs show a user-friendly error with --dev guidance" |

---

## Priority Summary

### Must update before v1.0.0 release (user-facing accuracy):

| Doc | Severity | Changes needed |
|-----|----------|----------------|
| `README.md` | **HIGH** | Test count (158→280+), rule counts (15→16), skill category table (7 wrong counts), rules table (only shows 9 of 15), extension command names (install→extension-add), skill counts in badge |
| `CHANGELOG.md` | **HIGH** | Test count, spec-015/016/017 entries, extension command names, remove catalog limitation note |
| `planning/16-cli-implementation.md` | **HIGH** | Config schema (remove integrations, fix permissions key, add linked_from), extension command names, check output, init output, error table, new functions, init --permissions, changelog command |
| `planning/12-version-roadmap.md` | **HIGH** | All v1.0 phases Planned→Complete, template count, late additions (015/016/017), init --permissions, changelog |
| `planning/06-build-roadmap.md` | **HIGH** | All phase statuses Planned→Complete, rule count 6→15/16 |
| `planning/07-project-structure.md` | **HIGH** | src/ tree (missing 5 files + utils.py), rules list (6→15/16), test files (6→13) |
| `planning/05-rules-design.md` | **MEDIUM** | Rule count 15→16, add multi-repo.md |
| `planning/08-multi-repo-orchestration.md` | **MEDIUM** | Add tooling deploy, profile, hook, linked_from, FeatureBrief, branch safety |
| `planning/04-commands-design.md` | **LOW** | COMMAND_SHORT_ALIASES dict (10→13 entries) |
| `planning/10-permissions-config.md` | **LOW** | permissions.level→permissions_level key name |
| `planning/13-handoff-schemas.md` | **LOW** | Add FeatureBrief schema |
| `planning/17-code-generation-flows.md` | **LOW** | --list flag, artifact ownership |

### Can defer to v1.1 (content/process docs):
- `planning/01-vision.md` — late additions list
- `planning/11-expanded-skills-inventory.md` — category counts
- `planning/15-template-content.md` — file count note
- `planning/09-review-and-coderabbit.md` — no gaps
- `planning/02-skills-inventory.md` — no gaps
- `planning/14-generic-skills-spec.md` — no gaps
- `planning/18-microservice-skills-spec.md` — no gaps
- `planning/03-agents-design.md` — no breaking gaps
