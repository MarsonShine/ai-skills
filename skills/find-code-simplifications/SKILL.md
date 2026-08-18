---
name: find-code-simplifications
description: Find non-obvious, evidence-backed opportunities to remove, fold, demote, or replace code, APIs, configuration, abstractions, packages, tests, and documentation. Use for simplification audits, dead or duplicated surface analysis, speculative-feature cleanup, dependency replacement studies, and requests to reduce maintenance cost without changing required behavior.
---

# Find Code Simplifications

Prefer a few well-proven candidates over a long list of guesses. A simplification should remove real maintenance cost while preserving the repository's current obligations.

## Workflow

1. Read repository instructions, architecture documentation, decision records, and testing policy.
2. Define the audit scope and any protected seams, compatibility requirements, or product choices that must remain.
3. Survey production code before tests and docs, starting with the largest or most coupled surfaces.
4. Search exact symbols, configuration keys, events, formats, package names, and wire strings; then read every meaningful caller.
5. Classify consumers as production, support/test/documentation, dynamic or ambiguous, and externally public.
6. Estimate net deletion, behavior tradeoffs, migration cost, and validation needed.
7. Reject weak candidates and report the strongest remaining opportunities with evidence.

Read `references/candidate-playbook.md` for candidate types, proof requirements, and dependency-swap checks.

## Rules

- Do not call code dead from static-search output alone; account for loaders, reflection, plugins, configuration, generated code, and external consumers.
- Do not treat tests or decision records as untouchable truth, but understand the behavior or rationale they protect before proposing removal.
- Do not disguise a feature decision as cleanup. Surface behavior changes and ask when product intent is not established.
- Use a local TODO only for a small, actionable cleanup. Use the repository's decision format for a durable cross-cutting proposal when one exists.
- Do not implement candidates during an audit-only request.

## Output

For each candidate, state the surface, consumer evidence, proposed simplification, net deletion or complexity reduction, behavior given up, risk, and validation path. Also state important areas surveyed with no credible candidate.
