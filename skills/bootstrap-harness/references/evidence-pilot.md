# Single-Task Acceptance Evidence

Use this route when the user requests an evidence or observability pilot. Select an actual defect or maintenance task with an observable result; do not invent business changes to exercise the process.

## Contract and Evidence

Keep the project's existing task card and add a task identifier plus a small table:

| Acceptance item | Observable pass condition | Verification | Evidence | Result |
| --- | --- | --- | --- | --- |
| A1 | The reported failure produces the required behavior | Focused reproduction or test | Report or artifact reference | Not verified |

Define task-specific conditions before implementation. Record pass, fail or not verified; explain genuinely inapplicable checks. A successful process exit or the existence of a log entry does not establish semantic correctness. An explanation for a skipped required check is not a pass; apply the project's existing waiver authority.

Prefer existing test reports, application logs, CI artifacts or public host telemetry. Associate each cited execution with the task and acceptance item, a distinct run identifier, time, working directory, command or operation, exit/outcome and source state. Record HEAD and relevant dirty inputs or a snapshot reference; HEAD alone does not identify uncommitted code. When reusing build output, establish that it matches the tested inputs.

Separate tool-observed facts from agent or human conclusions, and identify manually supplied information. Preserve failed and repeated runs separately. Reuse still-valid verification rather than rerunning it to populate a new form; reassess evidence when its relevant inputs or environment change.

## Storage and Handoff

Use the adopting project's evidence directory. Keep one summary linking acceptance items to results, code baseline and limitations; task/status/PR documents reference it instead of repeating the verdict. For ai-skills, follow the repository's `workspaces/<task>/` evidence convention.

Keep raw output local or in CI artifacts as appropriate. Shared review needs an accessible artifact or a sufficient sanitized excerpt, not just a local ignored path. Note retention limits. Inspect saved arguments and output for sensitive data; omitting prompts and environment variables alone does not prevent disclosure.

Project-owned task/status documents are not automatically upgraded from templates. `sync` restores missing or blank support files; it preserves non-empty files. `check` does not validate evidence quality or acceptance-table contents. Make any pilot-specific fields an explicit incremental project edit.

## Decide Whether to Automate

After the task, record which facts were missing, repeatedly transcribed or confused across runs. Add a recorder only for a demonstrated gap that existing tools cannot cover economically. A task-specific regression fixture is not a general trace recorder.

If a recorder is justified, define unique execution IDs, start and terminal events, output preservation, failure/cancellation behavior, and recording-error semantics before implementation. Format validation must not claim business correctness or tamper resistance. Agent-supplied decisions remain attributed claims.

Do not infer full agent tracing, model-quality gains or reduced review time from a single successful maintenance pilot. Keep host-session parsing, dashboards and new completion-rate metrics out of the pilot unless separately justified and requested.
