# AGENTS.md

This repository is the source of a Codex plugin containing small, task-focused, reusable agent skills.

## Scope and Completion

Follow the user's task, format, and existing authorization over skill defaults, within the active runtime's permissions. Continue authorized work through implementation and relevant validation; a skill's optional template or suggested budget must not create an extra approval gate. Preserve explicitly requested review checkpoints.

Read applicable instructions and the files or contracts relevant to the affected path. Load reference material when it resolves a concrete question; do not require a full repository survey for every edit.

If a skill rule blocks otherwise requested work, identify the exact file and rule, explain what remains blocked, and complete independent authorized work. Ask only for missing decisions or authorization that materially affect the result.

## Plugin and Skill Layout

- Keep `.codex-plugin/plugin.json` at the repository root, skills under `skills/`, and the local marketplace entry at `.agents/plugins/marketplace.json`.
- Only installable skills belong directly under `skills/`. Put evaluations, benchmark workspaces, experiments, and generated review artifacts in repository-level `workspaces/` or `docs/`.
- Install or reinstall the plugin instead of maintaining copies in user profile skill folders. See `docs/skill-development-guide.md` when packaging or installation is part of the task.

Use only the directories needed by a skill:

```text
skill-name/
  SKILL.md
  references/
  scripts/
  templates/
  assets/
```

Keep `SKILL.md` a short entrypoint: precise trigger, useful first action, resource routing, output contract, and essential constraints. Names and descriptions are always discoverable; keep descriptions concise and distinguish likely neighboring tasks. Put substantial conditional guidance in `references/`, and read it only when relevant. Do not add scripts or reference routers to reasoning-only skills without a concrete benefit.

## Choose Languages by Responsibility

| Responsibility | Language |
| --- | --- |
| Agent judgment, reviews, translation, plans, workflow rules | Markdown |
| Local file, image, PDF, Office, Excel/CSV, OCR, data transformation, batch processing | Python |
| API clients, schemas, structured tool contracts, MCP, long-lived CLIs, web/HTML/CSS/browser orchestration | TypeScript |
| Runtime discovery, argument forwarding, environment setup, OS entrypoints | Thin PowerShell or Shell wrappers |

For example, photo processing stays Python; DashScope integration and Markdown/HTML/browser-to-PDF orchestration use TypeScript. .NET repository inspection can use TypeScript or C#; use Python only for simple local text scanning. Do not move parsing, API response handling, or business logic into shell wrappers.

When introducing a script language, explain the responsibility-based choice briefly in the PR or commit message. Avoid unrelated language migrations.

## Script Contracts

- Accept explicit command-line arguments and use structured output, preferably JSON, when useful.
- Fail with clear errors; no hidden network calls or hard-coded secrets.
- Change only intended files and remain usable by both humans and agents.
- Split clients, schemas, and CLI entrypoints, or local processing and shared helpers, only when the responsibilities warrant it.

## Bug Fixes and Validation

Treat a reported failure as evidence of a failure class. Trace the relevant implementation/data path and distinguish facts from hypotheses. Establish the evidence-backed cause, violated invariant, representative variants, and lowest appropriate shared owner before editing. Explain the proposed behavior change and material risks briefly.

Restore the invariant at that owner. Do not add special-case values or narrow conditionals unless they encode a real domain, security, or compatibility rule with regression coverage. Do not refactor unrelated code or generalize beyond evidence.

For a bug fix, add or update focused regression evidence using an appropriate test, evaluation, fixture, or validator. Cover the reported case, representative unseen variants and boundaries, inverse cases when applicable, normal paths, and regression-sensitive behavior. If related variants still fail, reassess the cause and fix layer instead of stacking patches.

Run checks appropriate to affected behavior and required repository gates. Reuse passing results while their inputs remain valid; broaden or repeat only for new changes, failures, or unresolved risks. Do not add tests that merely mirror wording or implementation for reversible, low-impact edits.

Report the resulting behavior, validation performed, and material uncertainty. For bug fixes, also state the cause, invariant, and owner. Structural skill validation is not evidence of improved model behavior or reduced API cost.
