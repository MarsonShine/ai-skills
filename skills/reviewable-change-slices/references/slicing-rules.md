# Slicing Rules

Use these rules to turn a large software request into reviewable, buildable delivery units. The aim is not the smallest possible diff; it is the smallest coherent change a human can understand, validate, and redirect independently.

## Find Responsibility Boundaries

Prefer a new slice when work changes a different:

- observable behavior or acceptance criterion;
- security or failure policy;
- subsystem, module, or deployment boundary;
- data migration or compatibility phase;
- public contract;
- operational concern such as telemetry, health, packaging, or CI;
- reversible decision.

A useful slice has one sentence explaining why it exists without joining unrelated clauses with "and."

## Keep Coupled Evidence Together

Do not split:

- an implementation from the tests that prove the same behavior;
- a compile-time contract change from the minimum caller updates needed to build;
- a schema change from the minimum mapping or migration needed to apply it safely;
- a bug fix from its regression test;
- required documentation from the behavior it documents when users would otherwise receive an incomplete change.

Avoid artificial commits that only create a broken intermediate state.

## Split Cross-Cutting Work Safely

For broad migrations and refactors, prefer compatibility phases:

1. introduce a compatible seam or new contract;
2. migrate one consumer group;
3. migrate remaining groups in independently reviewable slices;
4. remove the compatibility path;
5. perform optional cleanup separately.

Each phase should build and should preserve or intentionally change observable behavior with evidence.

For security remediation, separate configuration, authentication, authorization, data migration, endpoint hardening, and operational rollout unless they are inseparable for a safe intermediate state.

For infrastructure work, separate registration/composition, provider alignment, migrations, health checks, container packaging, and observability.

## Order The Ledger

Order slices by:

1. safety prerequisites and failing regression evidence;
2. contracts or seams required by later work;
3. behavior changes;
4. migration and rollout;
5. deletion and cleanup;
6. optional polish.

Make dependencies explicit. A later slice may depend on an earlier one, but the active slice must not quietly implement its dependents.

## Apply The Review Budget

The defaults are at most 8 production files and roughly 400 changed lines of non-generated production code. Tests, docs, lockfiles, migrations, and generated files still count toward human review even when excluded from that numeric production-code signal.

When either limit is likely to be crossed:

1. stop before editing;
2. split by the responsibility rules above;
3. choose the smallest ready slice;
4. if no safe split exists, explain the coupling and ask the user to approve the larger slice.

Do not game the budget by compressing code, moving changes into generated output, or hiding unrelated edits in a mechanical rewrite.

## Respect Existing Work

Inspect the working tree before editing. Treat pre-existing changes as user-owned:

- do not revert them;
- do not stage them with the active slice;
- do not reformat or rename around them without need;
- report overlap before proceeding when isolation is unsafe.

## Interpret User Overrides

Only explicit instructions override the one-slice stop, for example:

- "Do all slices in one pass."
- "Continue through the whole plan without waiting for review."
- "Do not use the atomic-slice workflow for this task."

These are not overrides:

- "Implement the plan."
- "Finish the feature."
- "Keep going" when no slice has yet been delivered.

After a slice report, a user reply such as "continue" authorizes the next slice, not every remaining slice.

## Commit Authorization

Explicit authorization includes requests such as:

- "Commit this change."
- "Use one commit per slice."
- "Implement the next item and commit it."

It does not follow from a generic implementation request. Without authorization, leave the slice as an unstaged working-tree diff and propose a commit title.

Follow the repository's commit convention. If none exists, prefer a concise Conventional Commit title whose scope matches the single responsibility.
