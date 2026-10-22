# Harness Layout

## Four Layers

| Layer | Location | Responsibility |
| --- | --- | --- |
| Global trigger | `~/.dsh/AGENTS.md`, `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md` | Detect a missing block and propose `init` |
| Engine | `~/.agents/harness/` (`harness.py` + `templates/`) | Generate, adopt, sync, and check blocks |
| Project | `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` | Canonical block, adapters, project facts |
| Skill | this skill | Tell the agent when to call the engine |

The engine and its templates must work without the skill and without the ai-skills repository. The skill only routes.

## Adapters

- `AGENTS.md` is canonical for Codex and DSH.
- `CLAUDE.md` contains `@AGENTS.md`; do not duplicate the block there.
- `.github/copilot-instructions.md` embeds the same block because Copilot does not reliably follow file pointers.
- Add another adapter only when a host demonstrably ignores `AGENTS.md`.

Every embedded block carries `<!-- harness:managed vN sha256:... -->`. The hash covers the body between the markers, not the marker. `check` fails on a hash mismatch and only warns when the version is older.

## Support Documents

`check` also fails when the task card, status page, harness recovery guide, or PR template is missing or blank. `sync --write` restores these files from templates only when missing or blank; existing non-empty files remain byte-identical. Restoring a template does not recover lost task results: recover those from Git or backups.

Template changes do not migrate existing project documents. Add any new fields deliberately in the adopting project, preserving its content. `check` verifies file presence and non-empty content, not acceptance criteria, evidence links, or business correctness.

## Safety

- `init` requires a missing or empty `AGENTS.md`; `adopt` inserts the block after the first heading and preserves existing text.
- No command commits, pushes, or overwrites `README.md`.
- Auto mode (`init --auto`) refuses dirty trees, merge/rebase, `.harness-ignore`, and submodules.
- The managed block is generated. Edits belong in `templates/AGENTS.managed.md`, followed by `sync`.
- Project commands belong in `README.md` and `## Project`; duplicating them in the block creates drift.

## Recovery Without the CLI

1. Keep the managed block in `AGENTS.md` and the same block at the top of `.github/copilot-instructions.md`.
2. Keep `CLAUDE.md` containing `@AGENTS.md`.
3. Keep `docs/status.md` and `docs/tasks/active.md` updated by hand.
4. When the engine is available again, run `sync --write` to restore markers and hashes.
