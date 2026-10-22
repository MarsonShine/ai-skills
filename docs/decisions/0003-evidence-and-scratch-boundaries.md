# 0003: Evidence Lives in workspaces, Scratch Does Not Count

Status: Accepted
Date: 2026-10-19

## Context

- Verification output exists in three places: tracked `workspaces/<task>/`, untracked `x-tmp/`, and ignored `.codex-tmp/`.
- The 2026-09-07 audit evidence is cited by later documents; scratch runs are not.
- No index said which result was current, or at which commit it was produced.

## Decision

Only `workspaces/<task>/` is citable evidence. Each set states its baseline commit and date, what it covers, and its limits. `x-tmp/` and `.codex-tmp/` are scratch: never cited, never committed. `workspaces/README.md` is the index.

## Rejected alternatives

- Commit every evaluation transcript: noise and secrets risk.
- Delete evidence after a run: the next session repeats the work.
- Cite scratch output: it cannot be reproduced or reviewed.

## Consequences

- A result without a baseline commit and limitations is not evidence.
- Evidence is stale when relevant evaluated inputs change; unrelated later commits and timestamps alone do not invalidate it. Reuse retains the original execution date and explains applicability.
- Index maintenance is part of finishing an evaluation.

## Review trigger

Retention and current-state transitions are defined in [the session workflow](../multi-session-workflow.md). Revisit them if retained evidence obscures current facts; preserve unique rationale and repair references before removal.
