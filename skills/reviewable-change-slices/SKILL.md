---
name: reviewable-change-slices
description: Plan or deliver software work as commit-sized slices with a human checkpoint after each slice. Use when the user explicitly asks for one-slice-per-turn delivery, commit-by-commit review, staged implementation, or a slice ledger. Do not use for ordinary implementation, refactoring, analysis, code review, or a coherent multi-file change.
---

# Reviewable Change Slices

Protect the human owner's ability to understand, review, and redirect a codebase when they have chosen a staged delivery cadence. A long backlog may be planned at once, while each delivered slice remains coherent and independently reviewable.

Default to the user's language.

## Activation Contract

Apply this workflow only when at least one activation signal is present:

- the user explicitly invokes `$reviewable-change-slices`;
- the user asks for one slice or commit at a time with review between deliveries;
- the user asks for a slice ledger, staged migration, or commit-by-commit implementation; or
- repository instructions require human review checkpoints between independent changes.

A large, multi-file, or multi-responsibility request is not sufficient by itself. Ordinary implementation, refactoring, planning, analysis, and code review should use their normal workflows unless the user also chooses staged delivery.

Once activated, default to one validated slice per turn. If the user explicitly requests multiple slices in one pass, keep the slice and commit boundaries but continue through the authorized set before reporting.

## Workflow

1. Read the repository instructions and inspect the relevant code, tests, current diff, and user-provided plan.
2. Separate the work by responsibility, observable behavior, dependency order, and rollback boundary. Keep code and the tests that prove it in the same slice.
3. Present a compact slice ledger for the overall request. For every slice, state its purpose, proposed commit title, acceptance check, and dependencies. Expand only the next slice unless the user authorized a multi-slice pass.
4. Select exactly one ready slice. State its included scope, explicit exclusions, validation, and review budget before editing.
5. Implement only that slice. Do not absorb adjacent cleanup, formatting, renames, dependency upgrades, or another backlog item.
6. Run the smallest sufficient deterministic validation. Repair failures caused by the active slice, but do not switch to a different slice when blocked.
7. Create a commit only when the user explicitly authorized committing. Generic requests to fix, implement, or continue do not grant commit permission.
   - With authorization: stage only the slice, inspect the staged diff, create one commit, and report its hash.
   - Without authorization: leave the validated slice uncommitted and provide the proposed commit title. Do not stage files merely for presentation.
8. Deliver the slice report and end the turn unless the user explicitly authorized multiple slices in the current pass. With that authorization, repeat steps 4–7 for each ready slice and provide one final ledger showing every completed commit and validation result.

For a plan-only request that includes an activation signal, produce the compact slice ledger, identify the first ready slice, and stop without changing files.

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
