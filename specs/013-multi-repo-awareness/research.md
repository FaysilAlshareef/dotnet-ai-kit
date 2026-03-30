# Research: Multi-Repo Awareness

**Feature**: 013-multi-repo-awareness | **Date**: 2026-03-30

## R1: GitHub URL Normalization Patterns

**Decision**: Use regex to normalize three input formats to `github:org/repo`.

**Patterns to handle**:
- `https://github.com/org/repo` → `github:org/repo`
- `https://github.com/org/repo.git` → `github:org/repo`
- `git@github.com:org/repo.git` → `github:org/repo`
- `github:org/repo` → keep as-is (already normalized)

**Rationale**: These are the three standard GitHub URL formats. The `github:org/repo` internal format is already used by the `implement.md` clone logic (`gh repo clone {org/repo}`), so normalizing to this format keeps the downstream logic unchanged.

**Alternatives considered**:
- Store full URLs as-is → rejected because downstream clone logic already expects `github:org/repo`
- Support GitLab/Bitbucket URLs → out of scope for v1.0 (Claude Code only); can be extended later

**Implementation**: Add regex patterns to `validate_repo_path` in `ReposConfig`:
```python
GITHUB_HTTPS_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/.]+?)(?:\.git)?/?$")
GITHUB_SSH_RE = re.compile(r"^git@github\.com:([^/]+)/([^/.]+?)(?:\.git)?$")
```

## R2: Sibling Repo Auto-Detection Strategy

**Decision**: Scan `../` for directories with `.git/` + `.sln`/`.slnx`/`.csproj`, classify using quick code pattern matching.

**Classification heuristics** (in order of confidence):
| Pattern | Detected Type | Confidence |
|---------|--------------|------------|
| `AggregateRoot` or `EventSourcedAggregate` in `*.cs` | command | high |
| `IRequestHandler<Event<` or `EventHandler` with projection patterns | query | high |
| `Blazor` in `.csproj` or `*.razor` files exist | controlpanel | high |
| gRPC `Protos/` dir + client registration patterns | gateway | medium |
| `IHostedService` + event listener patterns | processor | medium |
| None of the above | unclassified | low |

**Rationale**: Quick heuristics (grep for key patterns) are fast (<1s per repo) and accurate enough for suggestions. The user confirms/overrides each suggestion.

**Alternatives considered**:
- Run full `/dai.detect` on each sibling → too slow (reads multiple files per repo)
- Use repo naming convention only → unreliable; not all teams follow `{company}-{domain}-{side}`

**Implementation**: In the slash command (configure.md), the AI assistant performs the scan using Glob/Grep tools. In the CLI (cli.py), use `pathlib.Path("../").iterdir()` + `subprocess.run(["grep", ...])`.

## R3: Brief Projection Auto-Commit Safety

**Decision**: Auto-commit briefs in secondary repos. Skip commit (leave files unstaged) if the secondary repo has uncommitted changes in the working tree.

**Safety checks before auto-commit**:
1. Check `git status --porcelain` in target repo
2. If output is empty (clean): safe to commit
3. If output is non-empty: write brief file but skip `git add` + `git commit`, warn user

**Rationale**: Auto-commit ensures team visibility (the whole point of briefs). Skipping on dirty state prevents accidental inclusion of unrelated changes in the brief commit.

**Alternatives considered**:
- Always auto-commit (even with dirty state) → risky, could bundle unrelated changes
- Never auto-commit → defeats team visibility purpose
- Stash, commit, unstash → complex, risk of stash conflicts

## R4: Token Budget Strategy for Near-Limit Commands

**Decision**: Replace existing placeholder content rather than append. Use concise bullet-point format for new sections.

**Files at risk** (>180 lines after edits):
- `specify.md` (178 → ~198): Replace comment blocks in Step 4 with brief projection steps
- `tasks.md` (197 → ~200): Replace the 3-line `spec-link.md` section with brief projection (net ~same)
- `implement.md` (182 → ~198): Add to existing Step 5a/5b bullets, don't create new steps
- `review.md` (181 → ~195): Add Check 9 as compact bullet format matching existing checks
- `analyze.md` (191 → ~200): Add Pass 11 matching existing pass format (3-4 lines)

**Rationale**: Constitution mandates ≤200 lines per command. These are hard limits.

**Mitigation**: If any file exceeds 200 lines, remove HTML comments (advisory notes to AI) which don't affect functionality.

## R5: FeatureBrief Pydantic Model Design

**Decision**: Add a simple pydantic v2 model for programmatic brief validation in the CLI.

**Fields**:
- `feature_name: str` — feature display name
- `feature_id: str` — NNN-short-name format
- `projected_date: str` — ISO date
- `phase: str` — enum: specified, planned, tasks-generated, implementing, implemented, blocked
- `source_repo: str` — source repo directory name
- `source_path: str` — local path or github:org/repo
- `source_feature_path: str` — relative path to source feature dir
- `role: str` — this repo's role description
- `tasks: list[dict]` — task ID, description, file path, status

**Rationale**: Pydantic validation ensures briefs are well-formed when loaded. The model mirrors the markdown structure for round-trip consistency.

**Alternatives considered**:
- No model (parse markdown directly) → fragile, error-prone
- Full dataclass instead of pydantic → inconsistent with existing models.py patterns
