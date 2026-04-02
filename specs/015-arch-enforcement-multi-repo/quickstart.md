# Quickstart: Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization

**Branch**: `015-arch-enforcement-multi-repo`

## Implementation Order

```
Phase 1 (Foundation — parallel):
  ├─ Part 1: Create 12 profile files in profiles/
  ├─ Part 5: Add AGENT_FRONTMATTER_MAP + update copy_agents()
  ├─ Part 3: Update command files for branch safety
  └─ Part 7: Add context:'fork' to 3 command files

Phase 2 (Depends on Phase 1 — parallel):
  ├─ Part 6: Add detected_paths to models.py, update copy_skills(), update ~10 SKILL.md files
  └─ Part 4: Create hook template, add copy_hook() to copier.py

Phase 3 (Depends on Phases 1+2 — parallel):
  ├─ Part 2: Add linked_from to models.py, add deploy_to_linked_repos(), extend cli.py
  └─ Tests: All 6 test files
```

## Critical Path

1. **Start with profiles** (Part 1) — all other enforcement depends on them existing.
2. **models.py changes** happen in two phases: `detected_paths` in Phase 2, `linked_from` in Phase 3.
3. **copier.py** gets the most changes: `copy_profile()`, `copy_hook()`, `deploy_to_linked_repos()`, updated `copy_agents()`, updated `copy_skills()`.
4. **cli.py** changes are last — extend `configure()` and `upgrade()` to call new copier functions.

## File-by-File Change Summary

| File | Phase | Changes |
|------|-------|---------|
| profiles/ (12 files) | 1 | Create all profile markdown files |
| agents/ (13 files) | 1 | Replace frontmatter with universal schema |
| agents.py | 1 | Add AGENT_FRONTMATTER_MAP dict |
| copier.py | 1 | Update copy_agents() for frontmatter transform |
| dai.specify.md | 1 | Add branch creation instructions for secondary repos |
| dai.plan.md | 1 | Add branch creation instructions for secondary repos |
| dai.tasks.md | 1 | Add branch creation instructions for secondary repos |
| dai.review.md | 1 | Add context:'fork' + agent field |
| dai.verify.md | 1 | Add context:'fork' + agent field |
| dai.analyze.md | 1 | Add context:'fork' + agent field |
| models.py | 2 | Add detected_paths to DetectedProject |
| copier.py | 2 | Add copy_profile(), update copy_skills() for token resolution |
| ~10 SKILL.md files | 2 | Add when-to-use + paths tokens |
| dai.detect.md | 2 | Add path detection step |
| templates/hook-prompt-template.md | 2 | Create hook prompt template |
| copier.py | 2 | Add copy_hook() |
| models.py | 3 | Add linked_from to DotnetAiConfig |
| copier.py | 3 | Add deploy_to_linked_repos() |
| cli.py | 3 | Extend configure() + upgrade() |
| dai.configure.md | 3 | Add linked repo deployment step |
| tests/ (6 files) | 3 | All new test files |

## Key Implementation Notes

1. **Profile content**: Derive constraints from existing skills. Read skills in `skills/microservice/command/` to write `profiles/microservice/command.md`. Do not invent new rules.

2. **Frontmatter parsing**: Use `yaml.safe_load()` on content between first and second `---` lines. Body is everything after second `---`.

3. **Token resolution regex**: `r'\$\{detected_paths\.(\w+)\}'` — matches `${detected_paths.key}` and captures `key`.

4. **Hook prompt size**: Keep under ~2000 characters. Extract only HARD CONSTRAINTS section from profile, not the full file.

5. **Git subprocess calls**: Always use `subprocess.run(["git", ...], cwd=path, capture_output=True, text=True)`. Check returncode. Never use `shell=True`.

6. **Test patterns**: Follow existing test_copier.py patterns. Use `tmp_path` fixture. Mock subprocess for git operations.
