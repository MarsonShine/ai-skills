---
name: implement-minimal-code
description: "Implement requested software features, bug fixes, and ordinary refactors with the least maintenance cost that satisfies the requirements. Use when the requested deliverable is implementation code: adding a feature, fixing a failure, or refactoring existing code. Normal coding requests do not need to mention minimalism. Do not use for review-only or diagnosis-only requests, planning-only business or architecture work, explicit code-reduction tasks owned by find-code-simplifications, or document/media deliverables that merely need helper code."
---

# Implement Minimal Code

Complete the requested behavior with a small, coherent implementation. Judge simplicity by the code and obligations someone must maintain, not by line or file counts.

## Workflow

1. Read the task, repository instructions, relevant contracts, and the code on the affected path. Identify the behavior to deliver and the constraints it must preserve before choosing a solution.
2. Look for existing code and patterns, standard-library facilities, native platform features, and installed dependencies before adding an implementation. This is a search order, not a ranking that overrides semantics. Compare suitable options by behavior, supported environments, adapters, lifecycle ownership, and maintenance cost.
3. Implement the smallest coherent change that meets those requirements. Add custom code or a dependency when the existing options fall short; avoid speculative extension points and unrelated cleanup. Resolve routine choices within the user's authorization; ask only when an unresolved choice would materially change the required behavior or scope.
4. For a bug fix, establish the cause and violated invariant, inspect affected callers, and restore the invariant at the lowest appropriate shared layer. Cover representative variants and boundaries rather than patching only the reported input or caller.
5. Validate the affected behavior using the repository's existing checks and conventions. Choose checks by risk and shared impact, including regression evidence for bug fixes. A short implementation can still require several checks; routine low-impact edits need no new tests merely to mirror the code.

Read `references/implementation-choices.md` when reuse, a platform replacement, an abstraction, or a short alternative has a non-obvious semantic tradeoff.

## Boundaries

- Preserve explicit features and technology choices, architecture boundaries, compatibility, trust-boundary validation, accessibility, and meaningful failure handling. If an alternative changes those obligations, explain the tradeoff instead of silently substituting it.
- One implementation or caller does not make an interface or wrapper unnecessary. Check its contract, lifecycle, external consumers, and isolation role before changing it.
- Do not force one-liners, fewer files, or a fixed test count. Preserve resource cleanup, cancellation, concurrency, and data integrity even when they make the change longer.
- Leave a short local comment only for a non-obvious constraint or accepted limitation, including its reason and a concrete revisit condition when useful. Follow existing decision-record conventions for durable cross-cutting decisions; do not create a separate shortcut ledger by default.
- Apply this guidance during implementation. A combined review-and-fix request still needs evidence of defects before edits; a simplification audit remains an audit unless implementation was requested. Do not introduce persistent modes, automatic review stages, or extra approval checkpoints.

## Output

Report the resulting behavior, any material choice or accepted limitation, and the validation actually performed. Match the explanation to the user's request. Do not claim token or cost savings without a comparable measured baseline.
