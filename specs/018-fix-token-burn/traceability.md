# Traceability — FRs and Findings → Tests

**Generated**: 2026-05-16 (T079)
**Source**: `specs/018-fix-token-burn/spec.md` + `tasks.md`

| FR | Test File | Test Name | Notes |
|---|---|---|---|
| FR-001 | tests/test_session_start_hook.py | test_session_start_hook_lacks_forbidden_phrases | session-start hook prose |
| FR-001 | tests/test_session_start_hook.py | test_session_start_hook_mentions_mcp_first_and_lazy_default | lazy-default language |
| FR-002 | tests/test_hook_exit_codes.py | test_pre_bash_guard_blocks_rm_rf_with_exit_2 | exit 2 not exit 1 |
| FR-003 | tests/test_hook_exit_codes.py | test_pre_commit_lint_blocks_on_format_failure | exit 2 on format fail |
| FR-004 | tests/test_hook_config.py | test_hooks_json_matchers_are_tool_names_only | matcher shape |
| FR-004 | tests/test_hook_config.py | test_dynamic_arch_hook_source_marker_preserved | _source exception |
| FR-005 | tests/test_copier_hooks.py | TestDynamicArchHookV2185::test_handler_if_filters_used_when_v2185 | v2.1.85+ branch |
| FR-005 | tests/test_copier_hooks.py | TestDynamicArchHookFR005::test_dynamic_arch_hook_is_preserved | legacy branch |
| FR-006 | tests/test_skill_frontmatter.py | test_no_forbidden_nested_metadata_fields | lift activation fields |
| FR-007 | tests/test_skill_frontmatter.py | test_top_level_description_is_use_when_trigger | trigger sentence |
| FR-008 | tests/test_skill_frontmatter.py | test_no_alwaysApply_anywhere | skills clean |
| FR-008 | tests/test_rule_frontmatter.py | test_rules_have_no_alwaysApply | rules clean |
| FR-008 | tests/test_profile_frontmatter.py | test_profiles_have_no_alwaysApply | profiles clean |
| FR-009 | tests/test_load_project_migration.py | test_nested_detected_shape / test_legacy_flat_shape | load_project supports both |
| FR-010 | tests/test_path_token_substitution.py | test_all_keys_present_substituted | substitution success |
| FR-011 | tests/test_rule_frontmatter.py | test_non_universal_rules_have_paths | path-scope rules |
| FR-011 | tests/test_rule_frontmatter.py | test_universal_rules_combined_line_budget | universals ≤300 |
| FR-012 | tests/test_command_bodies.py | test_no_load_all_skills_block_in_any_command | bulk-load removed |
| FR-013 | tests/test_copier_agents.py | TestTransformAgentFrontmatter::test_expertise_does_not_lift_to_skills / TestCopyAgentsIntegration::test_transforms_and_copies | inverted contract: `skills:` MUST be absent |
| FR-014 | tests/test_agent_bodies.py | test_no_skills_loaded_section | agent body clean |
| FR-015 | tests/test_agent_bodies.py | test_no_availability_always_line | agent body clean |
| FR-016 | tests/test_arch_narrative_dedup.py | test_no_duplicate_architecture_headings_between_agent_and_profile | dedup |
| FR-017 | tests/test_profile_frontmatter.py | test_profiles_have_top_level_paths | profile path-scope |
| FR-018 | tests/test_mcp_config.py | test_csharp_ls_preserved / test_codebase_memory_mcp_registered_with_min_version_sidecar | mcp shape |
| FR-019 | tests/test_mcp_version_check.py | test_parses_minimum_version_as_meets_minimum / test_below_minimum_does_not_meet | version check |
| FR-020 | tests/test_command_bodies.py | test_operational_commands_carry_mcp_first_block | README + commands |
| FR-021 | tests/test_command_bodies.py | test_operational_commands_carry_mcp_first_block | MCP-first block |
| FR-022 | tests/test_command_bodies.py | test_operational_commands_carry_exact_fallback_line | exact fallback line |
| FR-023 | tests/test_learn_memory_split.py | test_learn_does_not_use_always_loaded_rule_phrase | prose removed |
| FR-024 | tests/test_learn_memory_split.py | test_learn_references_all_six_topic_files | 6 topic files |
| FR-025 | tests/test_budgets.py | test_command_budget | ≤200 lines |
| FR-026 | tests/test_budgets.py | test_rule_budget | ≤100 lines |
| FR-027 | tests/test_budgets.py | test_skill_budget | ≤400 lines |
| FR-028 | scripts/check.py + tests/ | (3-tier suite) — static + unit + smoke split | gated in CI |
| FR-029 | tests/test_ci_config.py | (T086a) | static/unit every PR, smoke gated |
| FR-030 | tests/test_session_start_hook.py | test_session_start_hook_is_under_30_lines | hook size |
| FR-031 | tests/test_upgrade_atomic.py | test_a_successful_upgrade_updates_manifest_and_backs_up + (b,c,d,e,f,g) | atomic + rollback |
| FR-032 | tests/test_manifest.py | test_manifest_roundtrip / test_json_schema_validation / test_root_fields_enforced | manifest schema |
| FR-033 | tests/test_path_token_substitution.py | test_missing_key_raises_deployment_error / test_empty_value_treated_as_missing | DeploymentError |
| FR-033 | tests/test_copier_skills.py | TestResolveDetectedPathTokens::test_unresolved_token_raises_deployment_error | inverted contract |
| FR-034 | tests/test_hook_config.py | test_static_claude_settings_does_not_duplicate_plugin_hooks | settings dedup |
| FR-035 | tests/test_mcp_version_check.py | test_missing_binary_present_false / test_malformed_output_version_none | edge cases |
| FR-036 | tests/test_rule_pattern_dedup.py | test_no_rule_has_a_long_code_block | static check: any code fence >40 lines in rules/*.md is a violation |
| FR-037 | tests/test_budgets.py | test_agent_budget / test_profile_budget | ≤120 / ≤100 |
| FR-038 | tests/test_local_check_entrypoint.py | (T076) | check.py contract |

## Findings

| Finding | Test File | Notes |
|---|---|---|
| F01 (eager skill loading prompt) | tests/test_session_start_hook.py | covered |
| F02 (bulk Skills Loaded blocks) | tests/test_agent_bodies.py + tests/test_command_bodies.py | covered |
| F03 (alwaysApply Cursor noise) | tests/test_skill_frontmatter.py + tests/test_rule_frontmatter.py + tests/test_profile_frontmatter.py | covered |
| F04 (matcher abuse) | tests/test_hook_config.py | covered |
| F05 (hook exit 1) | tests/test_hook_exit_codes.py | covered |
| F06 (token-resolution silent fallback) | tests/test_path_token_substitution.py + tests/test_copier_skills.py | covered |
| F07 (settings.json duplication) | tests/test_hook_config.py::test_static_claude_settings_does_not_duplicate_plugin_hooks | covered |
| F08 (load_project bypass) | tests/test_load_project_migration.py | covered |
| F09 (expertise → skills lift) | tests/test_agent_bodies.py + agents.py change | covered |
| F10 (over-budget commands) | tests/test_budgets.py | covered |
| F11 (architecture narrative duplication) | tests/test_arch_narrative_dedup.py | covered |
| F12 (rule path-scope missing) | tests/test_rule_frontmatter.py::test_non_universal_rules_have_paths | covered |
| F13 (profile path-scope missing) | tests/test_profile_frontmatter.py::test_profiles_have_top_level_paths | covered |
| F14 (no manifest / no rollback) | tests/test_upgrade_atomic.py | covered |
| F16 (Claude Code v1 hook fallback) | tests/test_copier_hooks.py | covered |
| F17 (MCP version sidecar) | tests/test_mcp_config.py + tests/test_mcp_version_check.py | covered |
| F18 (monolithic constitution) | tests/test_learn_memory_split.py | covered |
