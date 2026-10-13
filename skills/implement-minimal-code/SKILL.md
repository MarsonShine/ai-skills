---
name: implement-minimal-code
description: "Implement software features, bug fixes, and ordinary refactors with minimal maintenance cost. Not for review/diagnosis-only requests, planning, explicit code-reduction audits, or document/media helper scripts."
---

# Implement Minimal Code

Complete the requested behavior with a small, coherent implementation. Judge simplicity by the code and obligations someone must maintain, not by line or file counts.

## Workflow

1. Read the task, repository instructions, relevant contracts, and the code on the affected path. Identify the behavior to deliver and the constraints it must preserve before choosing a solution.
2. Look for existing code and patterns, standard-library facilities, native platform features, and installed dependencies before adding an implementation. This is a search order, not a ranking that overrides semantics. Compare suitable options by behavior, supported environments, adapters, lifecycle ownership, and maintenance cost.
3. Implement the smallest coherent change that meets those requirements. Add custom code or a dependency when the existing options fall short; avoid speculative extension points and unrelated cleanup. Resolve routine choices within the user's authorization; ask only when an unresolved choice would materially change the required behavior or scope.
4. For a bug fix, establish the cause and violated invariant, inspect affected callers, and restore the invariant at the lowest appropriate shared layer. Select relevant variants and boundaries from that failure mechanism and shared impact.
5. Choose the smallest sufficient verification that can detect errors in the affected behavior. Reuse existing checks and still-valid results; establish credible regression evidence for bug fixes. Separately decide whether new or extended automated tests fill a concrete protection gap worth maintaining. Preserve explicit testing requirements, established TDD workflows, and required repository gates; neither patch size nor a fixed test count determines sufficient evidence.
6. Stop when required gates pass and affected behavior has sufficient evidence. Broaden or repeat checks only for changes that invalidate evidence, failures, or unresolved material risks. Keep recovery from verification-tool failures proportional to the changed behavior's risk; do not turn a low-impact edit into building or debugging a replacement test harness. When validation is unavailable, report the gap rather than substituting an unrelated passing check.

Read `references/implementation-choices.md` when reuse, a platform replacement, an abstraction, or a short alternative has a non-obvious semantic tradeoff.

Read `references/verification-strategy.md` when evidence sufficiency, test persistence, platform limitations, or the scope of additional checks is uncertain.

## Boundaries

- Preserve explicit features and technology choices, architecture boundaries, compatibility, trust-boundary validation, accessibility, and meaningful failure handling. If an alternative changes those obligations, explain the tradeoff instead of silently substituting it.
- One implementation or caller does not make an interface or wrapper unnecessary. Check its contract, lifecycle, external consumers, and isolation role before changing it.
- Do not force one-liners, fewer files, or a fixed test count. Preserve resource cleanup, cancellation, concurrency, and data integrity even when they make the change longer.
- Keep public API/XML comments brief about purpose, parameters, and key constraints; keep `summary` to one or two sentences and use other tags or remarks for necessary caller contracts. Internal comments explain non-obvious reasons, invariants, or accepted limitations rather than restating code; include a concrete revisit condition when useful. Follow existing decision-record conventions for durable cross-cutting decisions; do not create a separate shortcut ledger by default.
- When implementation requires documentation, put usage, setup, parameters, and material limitations in the README; put substantial algorithms, flows, errors, boundaries, and tradeoffs in technical docs, linked from the README. Explain necessary unfamiliar concepts before implementation details, without duplicating tutorials or creating documents for trivial changes.
- Apply this guidance during implementation. A combined review-and-fix request still needs evidence of defects before edits; a simplification audit remains an audit unless implementation was requested. Do not introduce persistent modes, automatic review stages, or extra approval checkpoints.

## Output

Briefly report the resulting behavior, validation actually performed, why tests were added or existing evidence was sufficient, and material unverified risks. Do not create a separate verification report by default. Match the explanation to the user's request. Do not claim token or cost savings without a comparable measured baseline.
