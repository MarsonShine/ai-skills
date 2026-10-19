# Multi-Session Workflow

Use this when work continues across sessions, parallel worktrees, or more than one agent. A task that fits one session does not need a handoff.

## State Files

| File | Owns | Updated by |
| --- | --- | --- |
| [`PROGRESS.md`](../PROGRESS.md) | Integration state: branch, baseline, validation, blockers, next | The integrator, after merging |
| [`workspaces/<task>/HANDOFF.md`](../workspaces/) | Task handoff for one branch or worktree | The session doing that task |
| [`docs/install-state.md`](install-state.md) | Installed copies and drift | Whoever installs |

## Handoff Fields

- branch and base commit;
- done and not done, with paths;
- validation actually run, its result, and what was not run;
- blockers;
- next action.

Keep it short enough to read in a minute. A handoff is not a design document.

## Worktrees

- One branch per slice. Do not edit `PROGRESS.md` from a worktree: two writers produce a conflict and the last merge silently wins.
- Write `HANDOFF.md` at the worktree root for work in progress. Move durable evidence into `workspaces/<task>/`.
- The integrator merges the slice first, then updates `PROGRESS.md` and deletes the handoff.
- Never merge a branch whose validation is missing or stale; record the exact command and result in the handoff.

## Staleness

- A handoff older than its branch's last commit is stale.
- Evidence older than the code it evaluates is stale.
- If a check cannot run, say so. Do not copy an earlier pass into a new baseline.

## Recovery Check

A new session should be able to read `PROGRESS.md`, open the referenced workspace or handoff, run one listed command, and continue. If that takes more than three lookups, the state file is incomplete.
