# Verification Strategy Behavior Evaluations

These ten small probes compare verification decisions before and after the skill changes. They belong to the repository workspace, not the installed plugin. They are a reusable case set, not a new evaluation framework or a cost benchmark.

## Prepare a Run

1. Use a separate workspace and fresh agent context for each case and condition. Keep the model, reasoning effort, tool access, task, starter files and actual environment the same. Select the corresponding baseline or candidate instruction/skill snapshot; do not expose the other run or its output.
2. Materialize `starter_files`. If `starter_reference` exists, first copy only that named case's `starter_files` from the repository-relative JSON file, then apply this case's files. Never inherit the old prompt's JSON output, single-file or disabled-tool restrictions.
3. Give the acting agent the case `prompt`, materialized files, environment facts and project rules. Put project rules into the fixture's repository instructions. Let the agent inspect files, execute available tools and edit the files its task needs. Review and planning cases retain their stated scope.
4. Keep `evaluator`, this README, independent checkers and other runs outside the acting agent's context and accessible workspace. Environment statements must reflect the host; do not advertise unavailable tools.
5. Perform any `preparation` steps before starting the agent. For `pre-push-reuse`, run the real gate and save its output and input digests in `prior-check.json`; a fabricated result invalidates the probe. Preserve the prepared workspace and interpreter so evidence is eligible for reuse.

For downstream skill probes, keep the fixture's repository instructions identical and vary only the applicable skill snapshots. The source repository's `AGENTS.md` is not a global plugin instruction; assess its maintenance rules separately rather than injecting them into unrelated application fixtures. Record the exact snapshots or hashes supplied. Prefer normal skill discovery and on-demand reference loading; if a skill is selected explicitly or references are supplied eagerly, label that departure in the result.

## Observe and Check

Save the actual tool transcript, exit codes, resulting file diff and final response for each run. Use the hidden criteria after the agent finishes; do not turn them into instructions for the task. Existing independent checker commands run from this repository with `RUN_DIR` pointing at the case workspace. Checker output is evaluator evidence, not evidence that the acting agent performed that check.

Judge each run on:

- Whether the requested behavior or deliverable is correct.
- Whether executed or validly reused checks observe the affected behavior, and whether required gates and explicit TDD are respected.
- Whether retained tests fill a credible regression gap, and whether extra test files, mocks, dependencies or helpers have an identifiable purpose.
- Whether high-risk behavior has sufficient evidence and checking stops once it is sufficient.
- Whether the final report distinguishes executed, reused, proposed and unavailable validation.

Record test additions, repeat commands and elapsed time as observations. Fewer tests alone is not success: the covered bug may need no additional tests, the shared interface and authorization cases have real protection gaps, and explicit TDD requires a failing-test-first trace. A review should identify a behavior defect rather than count test files; a business plan should tie verification to its actual risks.

Do not install large toolchains just for these probes. Run available local Python/Node checks and browser inspection where relevant. iOS and CEF3 cases on a host without their target runtimes evaluate reasoning, verification choice and honest reporting only. A modern Node pass does not establish old-browser compatibility; source inspection does not establish UIKit lifecycle behavior. Track these limitations separately from implementation quality.

## Compare and Stop

Start with one baseline/candidate pair to confirm that the runner materializes files correctly and preserves tool access. Run the other cases once, compare quality before effort observations, and investigate failures or ambiguous differences. Repeat only where variance or an unresolved result warrants it. Keep outputs under a run-specific repository workspace or temporary location; do not install them as skills.

A compact result row can record `case | condition | behavior | actual/reused validation | retained-test rationale | extra infrastructure | limitations`, with links to the transcript and diff. Do not require the acting agent to create an evidence ledger. Synthetic probes and structural validation cannot establish production quality, general security, or a percentage cost saving.
