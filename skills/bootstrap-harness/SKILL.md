---
name: bootstrap-harness
description: "Set up or synchronize a repository's agent working agreement: a managed AGENTS.md block, Claude/Copilot adapters, and status or active-task files. Use when adopting a new project, checking harness drift, or repairing a missing block."
---

# Bootstrap Harness

Install one working agreement across repositories without copying rules by hand. The managed block is generated; project facts stay local.

## Workflow

1. Run `python scripts/harness.py status` to see missing, outdated, or hand-edited blocks.
2. New or empty repository: `python scripts/harness.py init --write`.
3. Existing repository: `python scripts/harness.py adopt --write`, then fill `## Project` with the real stack, commands, and boundaries.
4. After a baseline change: `python scripts/harness.py sync --write`.
5. Run `python scripts/harness.py check`; report created, updated, skipped, version, and hash state.

All write commands are dry runs without `--write`. Review the diff; do not commit or push.

Read `references/harness-layout.md` when choosing adapters, explaining the layers, or recovering without the CLI.

## Boundaries

- Do not overwrite a non-empty `AGENTS.md`; use `adopt`.
- Do not touch `README.md` or project-owned sections; the block links to them.
- Do not copy project commands into the managed block.
- Do not run `init` in a merge, rebase, submodule, or dirty tree; auto mode requires a clean tree.
