# 0002: One Source for Skill Installation

Status: Accepted
Date: 2026-10-19

## Context

- `AGENTS.md` already requires installing the plugin instead of maintaining user-profile copies.
- The 2026-10-19 check found 7 stale copies, and the 2026-09-03 evaluation assumed installed copies matched the source.
- A runtime can only load what is installed; the repository remains the only editable source.

## Decision

The repository `skills/` tree is the single source. Installed targets are derived: plugin install, junction, or a documented copy with a recorded source commit. Editing an installed skill is not a change to the skill.

## Rejected alternatives

- Hand-maintained copies per tool: they drift silently, as observed.
- Committing generated install trees into this repository: duplicates the source and invites edits in the wrong place.
- Treating a successful install as behavioral validation: installation only changes which text the runtime loads.

## Consequences

- Every install records source commit and date in [docs/install-state.md](../install-state.md).
- Drift is checked by comparing hashes; size differences are only a hint.
- A change is not released until the installed target is refreshed and the next session loads it.

## Review trigger

When a host offers a stable package channel with immutable versions, record the version instead of reimplementing hash checks.
