# Contract: cli.py Changes

## configure() — Extended

**New steps added after existing deployment**:

```
existing: copy_commands, copy_rules, copy_agents, copy_skills, copy_permissions
new:      copy_profile(target, tool, project_type, confidence)
new:      copy_hook(target, profile_path)  # only if "claude" in ai_tools
new:      deploy_to_linked_repos(primary_root, config, version)
```

**Profile deployment**: Reads `project.yml` from `.dotnet-ai-kit/` to get project_type. If file doesn't exist (detection not run yet), deploys generic fallback profile.

**Hook deployment**: Only when `"claude"` is in `config.ai_tools`. Calls `copy_hook()` with the just-deployed profile path.

**Multi-repo deployment**: Only when `config.repos` has non-None local paths. For each, calls `deploy_to_linked_repos()`. Results are displayed via rich table or JSON output.

---

## upgrade() — Extended

**New steps added after existing re-deployment**:

```
existing: re-copy commands, rules, agents, skills; re-apply permissions
new:      copy_profile(target, tool, project_type, confidence)
new:      copy_hook(target, profile_path)  # only if "claude" in ai_tools
new:      deploy_to_linked_repos(primary_root, config, version)  # branch: chore/dotnet-ai-kit-upgrade-{version}
```

**Version check for linked repos**: Uses `deploy_to_linked_repos()` which handles version comparison internally.

---

## Git Operations in deploy_to_linked_repos()

All git commands use `subprocess.run(["git", ...], cwd=repo_path, capture_output=True, text=True)`.

**Branch creation**:
```python
# Check for dirty working directory
result = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, ...)
if result.stdout.strip():
    # warn and skip

# Create or checkout branch
branch_name = "chore/dotnet-ai-kit-setup"  # or upgrade-{version}
subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, ...)
# If branch exists, falls back to: git checkout {branch_name}

# After deployment, stage and commit
subprocess.run(["git", "add", ".claude/", ".dotnet-ai-kit/"], cwd=repo_path, ...)
subprocess.run(["git", "commit", "-m", "chore: deploy dotnet-ai-kit tooling"], cwd=repo_path, ...)
```
