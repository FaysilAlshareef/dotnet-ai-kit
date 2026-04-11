#!/usr/bin/env bash
# Session Start Bootstrap — Remind agent to check skills before every action.
# This hook runs at session start via hooks.json SessionStart event.

cat <<'EOF'
[dotnet-ai-kit] Skills active. Before any action, check if a skill applies:
  - Building/fixing? → skills/workflow/systematic-debugging
  - Completing work? → skills/workflow/verification-gate
  - Review feedback? → skills/workflow/receiving-review-feedback
  - Feature branch?  → skills/workflow/git-worktree-isolation
  - Full list: skills/ directory (124 skills across 14 categories)

Rule: If a skill MIGHT apply, load it BEFORE acting. Even a small chance = load it.
EOF
