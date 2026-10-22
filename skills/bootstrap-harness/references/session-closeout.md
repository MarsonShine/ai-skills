# Session Closeout

Keep one current-state owner per repository; it may be `PROGRESS.md` or `docs/status.md`. Do not create a competing state file just to fit a template. Start from repository instructions, that owner and the active task; follow historical links only for a concrete question.

Before ending work, reconcile the task and current state, record applicable verification and any remaining failure, and inspect task-owned temporary artifacts. Keep retained results at the repository's evidence location. An incomplete task needs a resumable handoff; do not claim completion, discard user changes or automatically roll back useful work. Commit/push authorization is separate.

## Read-only Inspection

Run from the skill directory, supplying the target repository:

```text
python scripts/harness.py closeout --root <repository> --state PROGRESS.md --scope PROGRESS.md --scope workspaces/<task>
python scripts/harness.py closeout --root <repository> --state docs/status.md --task docs/tasks/active.md --complete
```

The command emits JSON and exits 1 for inspection errors, 0 otherwise. It needs Python and Git, not a managed block. It does not mutate files, fetch remotes, execute prose commands or delete artifacts. The existing `check` command continues to check managed blocks and support-document presence.

- Current documents require one non-empty `Status`, `Task` and `Next` line. Valid statuses are `idle`, `in_progress`, `blocked`; idle requires `Task: none`, blocked also requires `Blocker`. Archive completed contracts, then return current entries to idle.
- `--task` checks that its status and task identifier agree with the state owner. `--complete` additionally rejects unfinished work. A well-described blocked handoff can pass without `--complete`; that is not a completed task.
- Existing staged/unstaged/untracked changes must match explicit `--scope` file/directory prefixes or `--preserve PATH=reason`. `--base REV` also inspects committed changes since a chosen session base. It does not judge whether a declared scope is appropriate.
- `--scratch PATH` checks an explicitly identified task-owned path, including ignored paths. Existing paths require disposal outside the checker or an explicit preservation reason. It does not scan every ignored directory, infer ownership or clean automatically.
- It checks inline Markdown file links in the selected entry documents, ignoring fenced examples and remote URLs. It does not crawl linked content, verify anchors, reference-style links or remote availability. Long entries produce a consolidation warning, never truncation.

All input paths are repository-relative and may not escape the root. Use exact paths, not glob patterns. Keep preservation reasons free of credentials and sensitive content.

## Human Judgment and Freshness

A structural pass does not establish semantic freshness, business correctness, test sufficiency, clean CI or a complete inventory of temporary files. Record evaluated inputs and relevant environment; later unrelated commits alone do not invalidate reusable evidence. Retain the original execution time when reusing it.

Template updates only affect newly created or restored empty files. Existing non-empty project documents need an explicit incremental migration. The managed-block version is unchanged by these optional closeout fields.
