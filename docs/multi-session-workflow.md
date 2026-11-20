# State, Evidence and Session Handoff

Start with `AGENTS.md`. In the integration checkout, read [current state](../PROGRESS.md) and follow the active task. In a task worktree, read its root `HANDOFF.md` and follow its `Next` action. Open module docs, decisions and historical runs when a concrete question requires them.

## Owners and Lifecycle

| Material | Single owner | At completion or replacement |
| --- | --- | --- |
| Integration state and next action | `PROGRESS.md`, maintained by the integrator | Replace current facts and link the relevant result |
| Task contract and retained evidence | `workspaces/<task>/README.md` | Mark completed/blocked; keep baseline, acceptance, outcomes and limitations |
| Task state, blocker and next action in a worktree | Worktree-root `HANDOFF.md`, maintained by the session doing that task | Preserve its unique contract and results in `workspaces/<task>/` before removal |
| Current installation and drift | `docs/install-state.md` | Update after installation; other entrypoints link here |
| Current behavior and rationale | Module documentation and accepted decisions | Consolidate unique reasoning before marking a decision superseded |
| Historical evaluations | `workspaces/README.md` index | Label applicability by evaluated inputs; do not load transcripts by default |
| Disposable files | Task-owned paths under `.codex-tmp/` or the OS temporary directory | Remove only identified disposable files; preserve unclassified or user-owned material |

Current state should fit roughly one page. Length is a review signal, not permission to truncate constraints. Use `Status`, `Task` and `Next` fields for unambiguous current state; `idle` uses `Task: none`. A finished contract remains in its workspace, not in the startup entrypoint.

## End of a Session

1. Inspect the diff against the session's starting state; explain unrelated/pre-existing changes rather than reverting them.
2. Record sufficient verification for affected behavior, with code/configuration/environment inputs and links to evidence. Preserve pending CI, known failures and unrun checks as such.
3. Update the entry this session owns. A worktree task updates its `HANDOFF.md`, while an integrator updates `PROGRESS.md`. Completed work points to its result; unfinished work names the blocker, remaining edits and exact next action.
4. Remove only disposable artifacts created or explicitly adopted by the task. Move necessary evidence out of scratch first. Ignored files are not automatically disposable.
5. Confirm the next session can locate its task and validation entrypoint. Commit and push only under the user's authorization.

A resumable incomplete task is a valid handoff, not a completed feature. A dirty tree may be intentional: identify its owner and preservation reason. Do not reset files merely to produce clean Git output. Check commands do not run arbitrary validation commands copied from task prose.

## Evidence Freshness

Record the tested revision and relevant dirty inputs or a snapshot. Evidence becomes stale when the code, dependencies, configuration, environment or contract it evaluates changes. An unrelated documentation commit or a rebase does not by itself invalidate a passing result; inspect the effective input diff and rerun only affected checks. A review decision may need reassessment even when a test result remains applicable.

Do not stamp reused results with a new execution date. Preserve the original result and explain why its inputs still apply. File age and Git commit time are investigation signals, not proof of validity or invalidity.

## Archive and Retention

Retain a compact result, reproduction path and unique reasoning while they explain current behavior or protect against repeated mistakes. Consolidate duplicated facts into their current owner and repair incoming links. Mark fully superseded evidence historical; delete only when it adds no unique evidence or rationale and the lifecycle review identifies every reference. Never delete to meet a quota or solely because of age.

Raw logs may remain in CI with its retention limits; shared review must retain an accessible artifact or a sufficient sanitized excerpt. Archive does not mean injecting history into every new session.

## Concurrent Work and Recovery

Use a separate Git worktree and a unique task ID for each concurrent task. Two sessions in the same working directory share the task card and Git index. A replacement session resumes the existing ID in the same worktree. Keep each `HANDOFF.md` untracked and stage task files explicitly. Before removing a worktree, preserve required evidence at its durable path.

From the repository root, run `python skills/bootstrap-harness/scripts/harness.py tasks --root .` for a read-only view of local worktree tasks and duplicate active IDs. Run `closeout --worktree-task` against one worktree, adding `--complete` once its card links to its completed evidence. The [card format and examples](../skills/bootstrap-harness/references/session-closeout.md) describe both modes. Only the integrator updates `PROGRESS.md`.

A recovery exercise should begin without chat history, find the current task, identify applicable evidence and name the next operation using the startup map. Record reading volume and factual mistakes separately from model-performance claims. Occasional manual maintenance can review stale indexes and unused constraints; scheduling requires an explicit request.
