---
name: find-code-simplifications
description: Audit a diff, directory, or repository for evidence-backed reductions in existing code, configuration, dependencies, tests, or behavior-owned documentation, and safely apply proven candidates when requested. Use for 代码做减法, 删除无用或重复代码, 去过度设计, or reducing maintenance cost while preserving required behavior. Do not use for ordinary implementation, general code review, product feature cuts, prose-only editing, or style-only refactoring.
---

# Find Code Simplifications

Prefer a few well-proven candidates over a long list of guesses. A simplification should remove real maintenance cost while preserving the repository's current obligations.

## Workflow

1. Read repository instructions, architecture documentation, decision records, and testing policy.
2. Bound the audit to the requested diff, directory, or whole repository and identify protected seams, compatibility requirements, and product choices that must remain.
3. Survey production code within that scope before tests and docs, starting with the largest or most coupled surfaces.
4. Search exact symbols, configuration keys, events, formats, package names, and wire strings; then read every meaningful caller, including outside the audit scope when needed to establish obligations.
5. Classify consumers as production, support/test/documentation, dynamic or ambiguous, and externally public.
6. Compare simpler alternatives for semantic fit and total maintenance cost; estimate net deletion, behavior tradeoffs, migration cost, and validation needed.
7. Reject weak candidates and report the strongest remaining opportunities with evidence.
8. If the user explicitly requested implementation, select only proven candidates, remove or replace the smallest coherent surface, update affected callers and evidence, and run the validation identified during the audit.

Read `references/candidate-playbook.md` for candidate types, proof requirements, and replacement selection.

## Rules

- Do not call code dead from static-search output alone; account for loaders, reflection, plugins, configuration, generated code, and external consumers.
- A single implementation or a file or line count does not prove that an abstraction is unnecessary. Remove demonstrated maintenance cost, not structure based on size alone.
- Do not treat tests or decision records as untouchable truth, but understand the behavior or rationale they protect before proposing removal.
- Do not disguise a feature decision as cleanup. Surface behavior changes and ask when product intent is not established.
- Use a local TODO only for a small, actionable cleanup. Use the repository's decision format for a durable cross-cutting proposal when one exists.
- Do not implement candidates during an audit-only request.
- An implementation request authorizes local simplification work, not removal of required behavior, unsupported compatibility, or externally consumed APIs whose ownership is unresolved.
- Keep each applied simplification reviewable. Do not mix unrelated cleanup merely because it was found during the same audit.

## Output

For an audit, state each candidate's surface, consumer evidence, proposed simplification, net deletion or complexity reduction, behavior given up, risk, and validation path. Also state important areas surveyed with no credible candidate.

For implementation, report the proven candidate applied, removed or replaced surface, behavior preserved, validation run, net reduction, and any candidates deliberately deferred.
