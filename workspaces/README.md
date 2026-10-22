# Workspaces

Tracked evaluation evidence and reusable case sets. Skills live in `skills/`; nothing in this directory is installable.

## Index

| Workspace | Recorded baseline | Contents | Status |
| --- | --- | --- | --- |
| [session-closeout](session-closeout/README.md) | ai-skills `26d1c79`, MS `b6d581a`, 2026-10-22 | state, lifecycle, packaging and resumption work | In progress |
| [harness-evidence-pilot](harness-evidence-pilot/README.md) | baseline `af63286`, fix `837c3dd`, 2026-10-22 | support-document regression evidence and MS integration pilot `b6d581a` | Completed; scoped execution evidence, not a model evaluation |
| [gpt6-astra-audit](gpt6-astra-audit/README.md) | `16f105b`, 2026-09-07 | structure, command, and behavior JSON | Historical; later skill edits invalidate it |
| [skill-routing-evals](skill-routing-evals/README.md) | none (cases only) | 50 catalog-routing cases | Reusable case set; no result committed |
| [implement-minimal-code-evals](implement-minimal-code-evals/README.md) | 2026-09-03 run | 7 cases, baseline and candidate outputs, `RESULTS.md` | Historical |
| [verification-strategy-evals](verification-strategy-evals/README.md) | 2026-10-13 run | 10 cases, `results.json`, `RESULTS.md` | Historical |
| [csharp-dotnet-code-checklist-workspace](csharp-dotnet-code-checklist-workspace/iteration-1/benchmark.md) | iteration-1 | benchmark plus three reviews with and without the skill | Historical |

## Rules

- A result is citable only if it names the baseline commit or date, the scope, and its limitations.
- Mark evidence stale when the evaluated skill, description, or reference changes. Do not reuse a pass across versions.
- `x-tmp/` and `.codex-tmp/` are scratch. Do not cite, commit, or treat them as evidence.
- Structural checks and manual contract reviews are not model pass rates. Keep the distinction visible.
- Put a short `README.md` in each new workspace: purpose, baseline, how to rerun, and what the result does not establish.
