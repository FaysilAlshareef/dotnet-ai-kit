# CLI Contract Changes: Tool-Wide Quality Hardening

**Branch**: `016-tool-quality-hardening` | **Date**: 2026-04-04

## init() — Profile and Hook Deployment

### New behavior (after existing step 7 — deploy skills/agents)

```
Step 7b: Deploy architecture profile (if project type known)
  FOR each tool in ai_tools:
    IF project.yml exists OR --type was provided:
      profile_path = copy_profile(target, tool, project_type, package_dir, confidence)
      IF tool == "claude" AND profile_path:
        copy_hook(target, profile_path, package_dir)
```

### New behavior: Auto-default to Claude

```
IF no --ai flag AND no AI tool directories detected:
  ai_tools = ["claude"]
  print info: "No AI tool detected. Defaulting to Claude Code."
  # Remove exit code 3 behavior
```

---

## check() — Extended Reporting

### Rich table: AI Tools (new columns)

| Column | Source | Format |
|--------|--------|--------|
| Skills | `len(list(skills_dir.glob("**/SKILL.md")))` | integer |
| Agents | `len(list(agents_dir.glob("*.md")))` | integer |
| Profile | `(rules_dir / "architecture-profile.md").is_file()` | "deployed" / "—" |
| Hook | Check settings.json for `_source: "dotnet-ai-kit-arch"` | "deployed" / "—" |

### Config panel: New rows

| Row | Source | Format |
|-----|--------|--------|
| Linked from | `config.linked_from` | path string or "N/A" |
| Detected paths | `project.detected_paths` | "{count} categories" or "not detected" |
| Linked repos | `config.repos.*` fields | Per-role: path + status |

### JSON output: New fields

```json
{
  "tools": {
    "claude": {
      "status": "configured",
      "commands": 27,
      "rules": 15,
      "skills": 120,
      "agents": 13,
      "profile": true,
      "hook": true
    }
  },
  "linked_from": null,
  "detected_paths": {"aggregates": "src/Core/Aggregates", ...},
  "linked_repos": [
    {"role": "command", "path": "../CommandService", "status": "deployed"}
  ]
}
```

---

## configure() — Full Re-deployment + Init Guard

### New gate (at function start)

```
IF NOT (target / ".dotnet-ai-kit").is_dir():
  print error: "dotnet-ai-kit is not initialized. Run 'dotnet-ai init' first."
  raise SystemExit(1)
```

### New behavior (after command re-copy, before profile deployment)

```
Step N: Re-deploy rules, skills, agents
  FOR each tool in ai_tools:
    copy_rules(rules_source, target, tool_config)
    copy_skills(skills_source, target, tool_config, detected_paths)
    copy_agents(agents_source, target, tool_config, tool_name)
```

---

## upgrade() — Warning Messages

### Replace silent exception swallowing

```
# BEFORE (4 locations):
except Exception:
    pass

# AFTER:
except Exception as exc:
    err_console.print(f"[yellow]Warning: {operation} failed: {exc}. "
                      f"Run 'dotnet-ai configure' to retry.[/yellow]")
```

Locations: detected_paths loading, copy_profile, copy_hook, deploy_to_linked_repos.

---

## deploy_to_linked_repos() — Style and Staging Fixes

### Secondary command style

```
# BEFORE:
copy_commands(commands_dir, repo_path, tool_config, config)

# AFTER:
sec_config = load_secondary_config(config_path)  # read secondary's config.yml
sec_style_config = config.model_copy()
sec_style_config.command_style = sec_config.get("command_style", "both")
copy_commands(commands_dir, repo_path, tool_config, sec_style_config)
```

### Dynamic git add

```
# BEFORE:
git add .claude/ .dotnet-ai-kit/

# AFTER:
staged_dirs = {".dotnet-ai-kit/"}
FOR each tool in config.ai_tools:
  tool_config = get_agent_config(tool)
  staged_dirs.add(tool_config.get("rules_dir", "").split("/")[0] + "/")
  # Adds: .claude/, .cursor/, .github/ etc.
git add {" ".join(sorted(staged_dirs))}
```
