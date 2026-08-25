---
name: maintain-decision-records
description: Maintain repository decision records such as ADRs, RFCs, and Agent Notes. Use when the records themselves must be added, reviewed, consolidated, archived, restored, or pruned under local lifecycle rules. Do not use for code review, general documentation editing, or production behavior changes.
---

# Maintain Decision Records

Reduce decision-document clutter without erasing rationale that can still prevent mistakes. Treat repository rules and the current implementation as authoritative; age and length are discovery signals, not retention criteria.

## Workflow

1. Read the repository instructions, decision-record templates, lifecycle documentation, and any rules under the records directory.
2. Identify the requested scope and the record system in use: ADR, RFC, Agent Note, design decision, or another local format.
3. Trace each record to current code, configuration, public documentation, newer decisions, and inbound links.
4. Classify it as active, fully superseded, partially superseded, implemented with future value, archival candidate, or removable rejection.
5. Apply only transitions the repository defines. If no lifecycle or archive convention exists, report a proposal instead of inventing one.
6. Consolidate unique rationale, alternatives, consequences, compatibility promises, and reintroduction conditions into the current owner before removing an obsolete record.
7. Repair inbound links and run the repository's documentation, link, format, and archive-integrity checks.

Read `references/lifecycle-guidance.md` for classification rules and edge cases.

## Safety Rules

- Never edit a sealed or frozen archive unless local rules explicitly allow it.
- Never archive toward a quota or delete a record solely because it is old, short, or already implemented.
- Keep a rejected record when the rejected approach remains tempting and its rationale still prevents re-litigation.
- Ask before choosing between two viable owners when the repository does not establish precedence.
- Do not change production behavior while performing a records-only maintenance request.

## Output

Report the inspected scope, classification and evidence for each changed record, links repaired, borderline cases left for the user, and checks actually run.
