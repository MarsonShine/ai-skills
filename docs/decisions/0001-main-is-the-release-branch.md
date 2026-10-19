# 0001: main Is the Only Release Branch

Status: Accepted
Date: 2026-10-19

## Context

- Between 2026-09-03 and 2026-10-13, 7 commits landed on `GPT6-Astra` while `main` stayed at `16f105b`.
- The plugin manifest was rebuilt on `GPT6-Astra` (`0.2.0+codex.20261013120707`), but a clone of `main` installed six-week-old skills.
- Installed copies at `%USERPROFILE%\.dsh\skills` matched neither branch exactly; 7 of 24 were older.

## Decision

`main` is the only branch that may be installed, published, or used as a validation baseline. A feature branch either merges into `main` before release or is explicitly declared as not installable. When the history is linear, fast-forward; do not rewrite published commits.

## Rejected alternatives

- Keep `GPT6-Astra` as the release channel: two current truths and silent drift.
- Tag builds from a branch without merging: the tag cannot be reproduced from `main`.
- Squash the branch on merge: loses the per-slice history that records why each change exists.

## Consequences

- Install instructions and CI refer to `main`.
- `GPT6-Astra` remains as a record until deleted; it is no longer a source.
- Releasing from an unmerged branch is a process error, not a supported mode.

## Review trigger

If release stabilization needs immutable versions, add annotated tags on `main`; do not reintroduce a long-lived install branch.
