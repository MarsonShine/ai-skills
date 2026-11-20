## Working Agreement

- Keep one current task per working tree. Give independent concurrent tasks separate Git worktrees and distinct task IDs; a new chat in the same directory shares that directory's changes.
- Before editing, state the task's in-scope paths, out-of-scope work, and acceptance command.
- A change outside the declared scope is a scope violation: revert it or split it into a new task.
- Done means the acceptance command passed and its output is recorded. Code inspection is not evidence.
- For a parallel task, keep its ID, status and next action in the worktree-root `HANDOFF.md`. Check that tree with `closeout --worktree-task`. Archive its result before retiring the tree.
- The integrator owns `docs/status.md` and `docs/tasks/active.md`; single-task work keeps the existing workflow. A small single-task edit may report its acceptance check without a separate task card.
- Project facts belong in `README.md` and the `## Project` section. Do not copy commands into this block.
- This block is generated. Change the baseline and run `harness sync`; do not edit it by hand.
