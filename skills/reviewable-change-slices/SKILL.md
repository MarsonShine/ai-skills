---
name: reviewable-change-slices
description: Break multi-part software plans and implementation requests into SRP-aligned, reviewable change slices, then deliver exactly one validated slice per turn and stop for human review. Use by default for broad fixes, refactors, migrations, remediation backlogs, or any coding task with multiple independently reviewable responsibilities, unless the user explicitly opts out. Do not use for read-only analysis or genuinely tiny single-responsibility edits.
---

# Reviewable Change Slices

Protect the human owner's ability to understand, review, and redirect a codebase. A long backlog may be planned at once, but implementation must advance through small, coherent delivery boundaries.

Default to the user's language.

## Activation Contract

Apply this workflow unless the user explicitly says to avoid slicing, complete multiple slices without stopping, or use another delivery cadence. A broad instruction such as "implement this plan" is not an opt-out.

If the request is read-only or is already one genuinely small responsibility, handle it directly without adding ceremony.

## Workflow

1. Read the repository instructions and inspect the relevant code, tests, current diff, and user-provided plan.
2. Separate the work by responsibility, observable behavior, dependency order, and rollback boundary. Keep code and the tests that prove it in the same slice.
3. Present a compact slice ledger for the overall request. For every slice, state its purpose, proposed commit title, acceptance check, and dependencies. Expand only the next slice in detail.
4. Select exactly one ready slice. State its included scope, explicit exclusions, validation, and review budget before editing.
5. Implement only that slice. Do not absorb adjacent cleanup, formatting, renames, dependency upgrades, or another backlog item.
6. Run the smallest sufficient deterministic validation. Repair failures caused by the active slice, but do not switch to a different slice when blocked.
7. Create a commit only when the user explicitly authorized committing. Generic requests to fix, implement, or continue do not grant commit permission.
   - With authorization: stage only the slice, inspect the staged diff, create one commit, and report its hash.
   - Without authorization: leave the validated slice uncommitted and provide the proposed commit title. Do not stage files merely for presentation.
8. Deliver the slice report and end the turn. Do not start the next slice, even when time, context, or tool budget remains. Continue only after the human replies.

For a plan-only request, produce the compact slice ledger, identify the first ready slice, and stop without changing files.

Read [references/slicing-rules.md](references/slicing-rules.md) when the boundary is ambiguous, the change crosses layers, the plan has more than three responsibilities, or a candidate slice exceeds the default review budget.

## Review Budget

Unless repository rules or the user define a smaller limit, split again before editing when a slice is likely to exceed either:

- 8 production files; or
- roughly 400 changed lines of non-generated production code.

These limits are review signals, not permission to split tightly coupled code from its tests or leave the repository unbuildable. If an indivisible safe change must exceed them, explain why and ask before proceeding.

## Review Corrections

Treat review feedback as a new follow-up slice. Do not amend, rebase, squash, or rewrite an already delivered commit unless the user explicitly requests it.

## Slice Report

Report:

- active slice and proposed commit title;
- behavior delivered and files changed;
- validation actually run and its result;
- commit hash, or `not committed — authorization not provided`;
- explicit exclusions and residual risks;
- the next slice, clearly marked `not started`.
