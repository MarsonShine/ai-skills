# Session Closeout

Keep one owner for integration state, such as `PROGRESS.md` or `docs/status.md`. In a task worktree, start with the repository instructions and its root `HANDOFF.md`. The integrator maintains the shared entry.

Before ending work, reconcile the task and current state, record applicable verification and any remaining failure, and inspect task-owned temporary artifacts. Keep retained results at the repository's evidence location. An incomplete task needs a resumable handoff; do not claim completion, discard user changes or automatically roll back useful work. Commit/push authorization is separate.

## Project Closeout

Run from the skill directory, supplying the target repository:

```text
python scripts/harness.py closeout --root <repository> --state PROGRESS.md --scope PROGRESS.md --scope workspaces/<task>
python scripts/harness.py closeout --root <repository> --state docs/status.md --task docs/tasks/active.md --complete
```

The command emits JSON and exits 1 for inspection errors, 0 otherwise. It needs Python and Git, not a managed block. It does not mutate files, fetch remotes, execute prose commands or delete artifacts. The existing `check` command continues to check managed blocks and support-document presence.

- Project state documents require one non-empty `Status`, `Task` and `Next` line. Valid statuses are `idle`, `in_progress`, `blocked`; idle requires `Task: none`, blocked also requires `Blocker`. Archive completed contracts, then return current entries to idle.
- `--task` checks that its status and task identifier agree with the state owner. `--complete` additionally rejects unfinished work. A well-described blocked handoff can pass without `--complete`; that is not a completed task.
- Existing staged/unstaged/untracked changes must match explicit `--scope` file/directory prefixes or `--preserve PATH=reason`. `--base REV` also inspects committed changes since a chosen session base. It does not judge whether a declared scope is appropriate.
- `--scratch PATH` checks an explicitly identified task-owned path, including ignored paths. Existing paths require disposal outside the checker or an explicit preservation reason. It does not scan every ignored directory, infer ownership or clean automatically.
- It checks inline Markdown file links in the selected entry documents, ignoring fenced examples and remote URLs. It does not crawl linked content, verify anchors, reference-style links or remote availability. Long entries produce a consolidation warning, never truncation.

All input paths are repository-relative and may not escape the root. Use exact paths, not glob patterns. Keep preservation reasons free of credentials and sensitive content.

## Concurrent Tasks in Separate Worktrees

Use one task per Git working directory. Check the directory with `git rev-parse --show-toplevel` in each session. If both return the same path, the sessions share the task card, modified files and staging area. Give each concurrent task its own registered worktree before editing. A later session can resume the same task in its existing worktree.

Create an untracked `HANDOFF.md` at the root of each task worktree. Give it a task ID unique among active tasks in the repository and retain that ID across sessions. For example:

```markdown
Status: in_progress
Task: T-EXCEL
Next: Run the CSV import tests against the new date-format fixture.
```

Use `Status: blocked` and add `Blocker: <specific dependency>` when work cannot proceed. For completion, set `Status: completed`, add `Evidence: [test results](docs/validation/T-EXCEL/summary.md)` pointing to an existing local evidence file, and use `Next` for the integration or handoff action. Keep the card out of shared branch commits. Archive the essential contract, results and remaining actions under a durable task-specific path before removing the card or worktree.

From the skill directory, typical commands are:

```text
python scripts/harness.py tasks --root <repository>
python scripts/harness.py closeout --root <excel-worktree> --worktree-task --scope HANDOFF.md --scope <excel-module>
python scripts/harness.py closeout --root <excel-worktree> --worktree-task --complete --scope HANDOFF.md --scope <excel-module> --scope docs/validation/T-EXCEL
```

`tasks` discovers local working directories via `git worktree list` and reads their root cards. The JSON summary includes each card's task, status, next action and worktree. Inspect its errors for duplicate active IDs or invalid cards. Concurrent creation can race with a scan, so resolve duplicate IDs before acting on the results. A second clone has its own worktree list.

`--worktree-task` validates the selected root's handoff and Git changes. `--complete` requires a completed card and its evidence. Completing one card leaves the others available for resumption. The integrator can inspect `tasks` on demand and update project state when an integration decision changes.

## Human Judgment and Freshness

A structural pass does not establish semantic freshness, business correctness, test sufficiency, clean CI or a complete inventory of temporary files. Record evaluated inputs and relevant environment; later unrelated commits alone do not invalidate reusable evidence. Retain the original execution time when reusing it.

Template updates only affect newly created or restored empty files. Update existing non-empty project guides explicitly when adopting this workflow. Use the engine's normal managed-block sync for the working agreement.
