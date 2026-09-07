# GPT-6 Astra Audit Evidence

Baseline: `16f105b1f7d9789450f9a159a635ce07cebadecc`. Branch: `GPT6-Astra`. Date: 2026-09-07.

- `structure-results.json`: Unicode character counts, concrete local resource checks, and integrity of the existing 50 routing cases. Counts are not token measurements or routing accuracy.
- `command-results.json`: local invocation checks and the environment override used for the photo-selector wrapper. Synthetic images test command compatibility, not photographic quality.
- `behavior-cases.json`: 20 scenarios inspected against the edited instructions and relevant references. `contract_review` records manual consistency inspection, not generated model behavior.

The plugin validator and UTF-8 skill validator passed for the plugin and all 24 skills. No independent model routing run, before/after task benchmark, paid generation, background removal, or PDF visual-rendering workflow was run.

For a model evaluation, replay each behavior case in a fresh context with only the relevant installed skills and necessary fixtures. Keep credentials, uploads, cleanup, and commits stubbed or in disposable authorized fixtures. Record actual actions, unnecessary questions, scope violations, final artifacts, validation effort, and runtime/model settings. Compare with the baseline using identical tasks and settings. Do not convert these manual records into model pass rates.

For discovery, use the unchanged corpus and procedure in `../skill-routing-evals/README.md`, with the new frontmatter catalog and no skill bodies preloaded. A new task after plugin reinstall is needed to assess the installed catalog; installation alone does not validate model behavior.
