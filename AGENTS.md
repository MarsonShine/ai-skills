# AGENTS.md

## Repository Purpose

This repository contains reusable AI agent skills. A skill should be small, task-focused, easy for agents to load, and deterministic where possible.

## Core Principle

Do not choose a scripting language by habit. Choose it by the responsibility of the code.

Use Markdown for agent-facing judgment and workflow rules.
Use Python for local file, image, PDF, Excel, data-processing, and batch automation scripts.
Use TypeScript for API clients, schema validation, structured tool interfaces, MCP/tooling layers, web/HTML pipelines, and long-lived engineering code.
Use PowerShell or Shell only as thin OS-specific wrappers, not as the place for complex business logic.

## Skill Structure

Prefer this structure:

```text
skill-name/
  SKILL.md
  references/
  scripts/
  templates/
  assets/
```

`SKILL.md` should stay short. It should explain:

- When the skill should be used
- What the agent should do first
- Which script or reference file to use
- What output format is expected
- What must not be done

Move long checklists, examples, policies, and domain knowledge into `references/`.

Move deterministic or repeatable operations into `scripts/`.

## Plugin Layout

This repository is a Codex plugin source. Keep `.codex-plugin/plugin.json` at the repository root and expose reusable skills through `skills/`.

Only real skills belong directly under `skills/`. Evaluation output, benchmark workspaces, experiments, and generated review artifacts belong under repository-level folders such as `workspaces/` or `docs/`, because the plugin validator treats every direct child of `skills/` as an installable skill.

Use `.agents/plugins/marketplace.json` as the local marketplace entry for this repository. Do not copy maintained skills into user profile skill folders as a long-term workflow; install or reinstall the plugin instead.

## Language Selection Rules

### Use Python when the script mainly does local processing

Choose Python for:

- Image processing
- PDF parsing
- Office document processing
- Excel or CSV processing
- Batch file operations
- Local data transformation
- OCR or media-related processing
- Small one-off automation scripts

Examples in this repository:

- `id-photo-maker`: keep image processing scripts in Python
- `photo-selector`: keep contact sheet and image inspection scripts in Python
- `resume-builder`: keep PDF text extraction in Python

### Use TypeScript when the script mainly handles structured software integration

Choose TypeScript for:

- HTTP API clients
- JSON request and response models
- Configuration validation
- Tool schema definitions
- MCP/tool protocol code
- Long-lived CLI tools
- Web, HTML, CSS, browser, or headless-Chromium workflows
- Agent-facing structured input/output contracts

Examples in this repository:

- `qwen-image-generator`: prefer TypeScript for the DashScope/Qwen API client and response handling
- `markdown-pdf-export`: prefer TypeScript for Markdown/HTML/CSS/browser/PDF orchestration if the tool becomes cross-platform
- `csharp-dotnet-code-checklist`: use TypeScript or C# for repository inspection; avoid Python unless doing simple text scanning

### Use Markdown only when no deterministic script is needed

Keep a skill as Markdown-only when the main work is reasoning, reviewing, translating, planning, or checking.

Examples:

- `business-solution-architect`
- `fact-check-debunker`
- `translate-tech-en-zh`
- checklist-only review skills

Do not add scripts just to make a skill look more technical.

## Token and Context Rules

Keep `SKILL.md` concise. Treat it as a router, not a full manual.

Prefer:

```text
SKILL.md       = short trigger + workflow + output contract
references/   = long guidance loaded only when needed
scripts/      = deterministic work executed by tools
```

Avoid:

- Long duplicated explanations in every skill
- Putting large examples directly in `SKILL.md`
- Repeating the same language-selection rules inside every skill
- Large always-loaded instruction files

## Script Design Rules

Every script should:

- Accept explicit command-line arguments
- Print structured output when useful, preferably JSON
- Fail with clear error messages
- Avoid hidden network calls unless the skill clearly requires them
- Avoid hard-coded secrets
- Avoid changing unrelated files
- Be usable by both humans and agents

For API scripts, prefer:

```text
scripts/
  client.ts
  schema.ts
  cli.ts
```

For local-processing scripts, prefer:

```text
scripts/
  process_file.py
  common.py
```

## Wrapper Rules

PowerShell, Bash, or batch files may be used for platform compatibility.

They should only:

- Locate runtimes
- Pass arguments
- Set environment variables
- Call Python or TypeScript entrypoints

They should not contain complex parsing, API response handling, or business logic.

## When Editing Existing Skills

Before adding or changing scripts, decide:

1. Is this a reasoning-only skill? Keep it Markdown.
2. Is the task local file/media/data processing? Use Python.
3. Is the task API/schema/tooling/web integration? Use TypeScript.
4. Is it OS-specific startup glue? Use PowerShell or Shell as a thin wrapper.
5. Can long instructions be moved from `SKILL.md` into `references/`?

Explain this choice briefly in the PR or commit message when adding a new script language.

## Bug Fixes

Treat a reported failure as evidence of a failure class, not just an example to make pass. Before editing, trace the relevant implementation or data path and available evidence. Briefly distinguish facts from hypotheses and state the evidence-backed cause, violated invariant, likely variants, the lowest appropriate layer that owns the invariant and is shared by affected paths, the proposed fix, and expected impact and risks.

Restore the invariant there. Do not add hard-coded values or narrow conditionals unless they encode a genuine business, domain, security, or compatibility rule and have regression coverage. Do not generalize beyond evidence or refactor unrelated code.

Add or update a focused regression check that captures the invariant, using an appropriate test, evaluation, fixture-backed assertion, or validator. Cover the reported failure, representative unseen variants and boundaries, inverse cases when applicable, normal paths, and regression-sensitive behavior; run focused and appropriate broader checks. If a related variant fails, stop stacking patches and reassess the diagnosis and fix layer.

Report the cause, invariant and owner, behavior change, validation, and remaining uncertainty.

## Quality Bar

A good skill should be:

- Small
- Predictable
- Easy to inspect
- Easy to run
- Low-token
- Clear about what the agent should and should not do

Do not optimize for language uniformity. Optimize for maintainability, determinism, and agent readability.
