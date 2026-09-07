---
name: run-pre-push-checks
description: "Select and run local validation for an outgoing Git change before push or PR readiness, including post-rebase checks. Not for code review, CI repair, or pushing itself."
---

# Run Pre-Push Checks

Match evidence to the outgoing change. Avoid reflexively running the full repository suite when focused checks cover the affected behavior.

## Workflow

1. Confirm repository root, branch, worktree state, and the live upstream or pull-request base.
2. Inspect committed, staged, unstaged, and untracked changes against the verified base.
3. Read repository instructions, scripts, CI workflows, package manifests, and affected tests to discover the supported checks.
4. Map each affected behavior or artifact to the narrowest test, build, static gate, snapshot, documentation check, or real-entry smoke that would fail for its regression.
5. Run each selected check once. Add broader checks only when shared or cross-cutting impact makes narrower evidence unreliable.
6. Stop on failure, diagnose it, and rerun only checks invalidated by the repair.
7. Report commands run, results, untested risks, and what CI still owns.

Read `references/evidence-selection.md` for a change-to-check matrix and history-rewrite rules.

## Boundaries

- Do not duplicate a passing check solely because a commit or push follows.
- Do not lower thresholds, skip tests, or narrow coverage merely to make the change pass.
- Do not claim an environment-specific failure without recording the command, mismatch, and non-platform evidence.
- A successful rebase, stack sync, build, or typecheck does not prove the branch is ready by itself.
- This skill authorizes checks, not commits, pushes, force-pushes, or remote review changes.
