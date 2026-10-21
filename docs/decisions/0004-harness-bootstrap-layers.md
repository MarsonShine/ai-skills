# 0004: Bootstrap the Harness from One Versioned Baseline

Status: Accepted
Date: 2026-10-21

## Context

- Working rules had to be copied into every repository; the same WIP, scope, and evidence rules were repeated by hand.
- Global-only instructions are invisible to reviewers and CI, and each host reads a different file.
- A private manifest such as `.harness.json` has no meaning to any agent and adds a tool-specific artifact.
- A fresh repository without any installed tool has no way to discover the rules.

## Decision

Use four layers:

1. A small global trigger in each host (`~/.dsh/AGENTS.md`, `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`) that detects a missing block and proposes initialization.
2. An engine at `~/.agents/harness/` (`harness.py` plus templates) that renders, adopts, syncs, and checks the block.
3. Project files: a canonical managed block in `AGENTS.md`, a `@AGENTS.md` adapter in `CLAUDE.md`, the same block at the top of `.github/copilot-instructions.md`, plus `docs/status.md` and `docs/tasks/active.md`.
4. An optional `bootstrap-harness` skill that tells the agent when to call the engine.

The block carries its version and body hash in an HTML comment. No manifest file is required. Project facts stay in `README.md` and the `## Project` section.

## Rejected alternatives

- Copy the full rules into every repository: guaranteed drift.
- Keep rules only in user-level instructions: not reviewable, not enforceable in CI, inconsistent across hosts.
- Symlink one shared `AGENTS.md`: project facts differ, and symlinks are unreliable across platforms and agents.
- Store state in `.harness.json`: no agent reads it, and it looks tool-specific.
- Automatically overwrite existing `AGENTS.md`: destroys project-specific constraints.

## Consequences

- A baseline change is one edit, then `sync --write` per repository.
- `check` fails on a hand-edited block and only warns when the baseline version is older.
- Initialization works without the skill when the global trigger and engine are installed; without either, the project doc records the manual recovery steps.
- Adapters are generated from one body, so the agent-dependent file layout does not duplicate rules by hand.

## Review trigger

When a host ignores `AGENTS.md`, add an adapter instead of copying rules into another prose file. If repository count grows enough to need version pinning per project, add a release tag for the engine rather than a new manifest.
