# Research: Architecture Profiles, Multi-Repo Deployment, and Enforcement Optimization

**Date**: 2026-04-02 | **Branch**: `015-arch-enforcement-multi-repo`

## R1: Profile-to-Project-Type Mapping Strategy

**Decision**: Use a simple dict in copier.py mapping project_type strings to profile source paths.

**Rationale**: The mapping is static (12 entries) and changes only when new project types are added. A dict lookup is simpler and more testable than dynamic path construction.

**Alternatives considered**:
- Convention-based path resolution (e.g., `profiles/{mode}/{type}.md`) — rejected because mode/type hierarchy doesn't map 1:1 (generic types aren't under microservice/).
- Profile class with registration — over-engineering for 12 static entries.

**Implementation**:
```python
PROFILE_MAP = {
    # microservice mode
    "command": "profiles/microservice/command.md",
    "query-sql": "profiles/microservice/query-sql.md",
    "query-cosmos": "profiles/microservice/query-cosmos.md",
    "processor": "profiles/microservice/processor.md",
    "gateway": "profiles/microservice/gateway.md",
    "controlpanel": "profiles/microservice/controlpanel.md",
    "hybrid": "profiles/microservice/hybrid.md",
    # generic mode
    "vsa": "profiles/generic/vsa.md",
    "clean-arch": "profiles/generic/clean-arch.md",
    "ddd": "profiles/generic/ddd.md",
    "modular-monolith": "profiles/generic/modular-monolith.md",
    "generic": "profiles/generic/generic.md",
}
FALLBACK_PROFILE = "profiles/generic/generic.md"
```

---

## R2: AGENT_FRONTMATTER_MAP Design

**Decision**: Use a nested dict in agents.py with lambdas for value-dependent transformations and plain dicts for enum-style mappings.

**Rationale**: Keeps the mapping declarative and co-located with AGENT_CONFIG. Lambdas handle the two fields that need value transformation (expertise list → skills list, max_iterations int → maxTurns int). Enum-style mappings (role → disallowedTools, complexity → effort+model) use nested dicts for direct lookup.

**Alternatives considered**:
- Transformation functions per tool — more flexible but harder to read and test as a unit.
- External YAML config for mappings — adds file I/O complexity for no benefit (mappings are code, not user config).
- Class-based strategy pattern — over-engineering for a single tool (v1.0 only supports claude).

**Implementation**: See spec Part 5 for the exact AGENT_FRONTMATTER_MAP structure. The `copy_agents()` function in copier.py will:
1. Parse YAML frontmatter from source agent file.
2. Look up `AGENT_FRONTMATTER_MAP[tool_name]`.
3. For each universal field (role, expertise, complexity, max_iterations), apply the mapping.
4. Merge all transformed fields into a single dict.
5. Serialize as YAML frontmatter + original markdown body.

---

## R3: Hook Prompt Template Strategy

**Decision**: Use a Jinja2 template file (`templates/hook-prompt-template.md`) that is rendered at deployment time with profile constraints injected.

**Rationale**: The hook prompt must be a static string in settings.json (prompt hooks can't read files at runtime). Using Jinja2 is consistent with the existing `render_template()` function in copier.py. The template contains the haiku instructions, file-scope filter, and a `{{ constraints }}` placeholder.

**Alternatives considered**:
- String concatenation in Python — fragile, hard to maintain prompt wording.
- f-string template — doesn't support multi-line cleanly, can't be reviewed as a standalone file.

**Constraint extraction**: The `copy_hook()` function reads the deployed profile file, extracts lines between frontmatter end (`---`) and file end, strips markdown headers, and injects as the `constraints` variable.

---

## R4: Multi-Repo Deployment Architecture

**Decision**: Reuse existing copy_* functions with target_root parameter. Add `deploy_to_linked_repos()` in copier.py that orchestrates the per-repo deployment loop.

**Rationale**: The copy functions (copy_commands, copy_rules, copy_agents, copy_skills) already work correctly. The only new logic is: (1) iterating linked repos, (2) checking initialization/version, (3) git branch creation/commit, (4) writing linked_from. Reuse avoids duplication and ensures secondary repos get identical tooling.

**Alternatives considered**:
- Separate deployment script — splits logic across files, harder to test.
- Subprocess call to `dotnet-ai init` in secondary repos — requires the package to be installed there, adds complexity.

**Git operations**: Branch creation and commits use `subprocess.run(["git", ...], cwd=repo_path)` with list args. The `cwd` parameter targets the secondary repo. Operations:
1. `git status --porcelain` — check for dirty working directory.
2. `git checkout -b {branch}` or `git checkout {branch}` — create or switch to branch.
3. `git add .claude/ .dotnet-ai-kit/` — stage deployed files.
4. `git commit -m "chore: deploy dotnet-ai-kit tooling"` — commit.

---

## R5: Detected Paths Storage

**Decision**: Store as `Optional[dict[str, str]]` field on DetectedProject. Keys are logical category names (aggregates, events, handlers, etc.), values are relative paths from project root.

**Rationale**: A flat dict is simple to serialize to YAML, simple to access in copier.py, and maps directly to the `${detected_paths.*}` token syntax. No need for a nested model — categories are fixed strings, not dynamic.

**Alternatives considered**:
- Separate pydantic model (DetectedPaths) — adds a class for what's just a string→string dict.
- List of path objects — loses the category key, harder to reference in token resolution.

**Token resolution in copy_skills()**: Read `detected_paths` from project.yml. For each skill file, scan frontmatter for `${detected_paths.*}` patterns. Use regex substitution: `re.sub(r'\$\{detected_paths\.(\w+)\}', lambda m: paths.get(m.group(1), ''), content)`. If the resolved value is empty, remove the entire `paths:` line from frontmatter.

---

## R6: Command Context Fork Fields

**Decision**: Add `context: 'fork'` and `agent: {agent-name}` to YAML frontmatter of dai.review.md, dai.verify.md, and dai.analyze.md.

**Rationale**: Claude Code supports `context` field in command frontmatter. `'fork'` runs the command in a subagent context. The `agent` field specifies which agent type handles execution. This is a simple frontmatter addition — no Python code changes needed.

**Alternatives considered**:
- Custom subagent spawning in command body — more complex, less maintainable.
- No forking — leaves context pollution as-is, degrades long-session performance.

---

## R7: Branch Safety in AI Commands

**Decision**: Add branch creation instructions to the markdown body of dai.specify.md, dai.plan.md, and dai.tasks.md command files. These are AI-driven operations where the AI executes git commands.

**Rationale**: The Python CLI (cli.py) is not involved in specify/plan/tasks phases — these are slash commands executed by the AI. The AI reads the command file's instructions and executes git commands accordingly. Branch logic must be in the command instructions, not in Python code.

**Branch naming**:
- Brief projections: `chore/brief-{NNN}-{name}` (reuse if exists)
- Tooling deployment (CLI): `chore/dotnet-ai-kit-setup` or `chore/dotnet-ai-kit-upgrade-{version}`

**Safety checks** (added to command instructions):
1. Check current branch: `git rev-parse --abbrev-ref HEAD`
2. If on main/master/develop: create/switch to chore branch
3. If chore branch exists: switch to it (reuse)
4. If dirty working directory: warn and skip auto-commit
