# Loop Decision Matrix

Use this reference when a task is complex enough that the agent should choose an execution loop before acting.

## Decision Table

| Loop type | Use when | Trigger | Stop condition | Cost control |
| --- | --- | --- | --- | --- |
| Turn-based | The user asks for a bounded task, exploration, implementation, review, or one-off artifact. | Current user request. | Task is complete, tests/checks pass, or required context is missing. | Keep scope tight; validate before final response. |
| Goal-based | The desired result has an objective threshold or measurable target. | Current user request plus a goal. | Target is reached or max attempts is hit. | Set max attempts and measurable acceptance criteria. |
| Time-based | The same check or action should repeat on a schedule. | Interval, cron, or scheduled routine. | User cancels, queue is empty, PR is merged, issue is resolved, or routine reaches a defined terminal state. | Use the longest useful interval; prefer event triggers if available. |
| Proactive | Ongoing incoming work should be triaged, routed, fixed, replied to, or escalated. | Event trigger or scheduled scan. | Each subtask reaches its own goal; overall routine continues until disabled. | Split simple work to cheaper deterministic tools; use stronger models only for judgment-heavy steps. |

## Stop Condition Templates

- Code change: "Stop when the requested behavior is implemented, relevant tests pass, and no new lint/build/runtime errors are observed."
- UI change: "Stop when the dev server renders the changed UI, the target interaction works in the browser, screenshots show the expected state, and the console has no new errors."
- Performance goal: "Stop when metric X is at least Y for page/workload Z, or after N attempts with the best result and blockers reported."
- Review task: "Stop when all changed files are inspected, findings are evidence-based with file/line references, and residual risks are listed."
- Recurring monitor: "Stop each run when all new items since the last run are processed or explicitly deferred; stop the routine only when cancelled or the source is closed."
- Document/artifact task: "Stop when the artifact satisfies the requested format, required sections are present, and source facts are preserved."

## Validation Checklist

- Read the authoritative source: repo files, docs, issue text, PR diff, attached content, or external system.
- Run deterministic checks when available: tests, build, lint, typecheck, schema validation, benchmark, export command.
- Inspect the real output for user-facing work: browser screenshot, generated file, rendered document, CLI output, or logs.
- Verify edge cases tied to the request: empty input, permissions, retries, failures, concurrency, time zones, locale, or data boundaries.
- State what was not verified when tools, permissions, or context are missing.

## Cost And Token Boundaries

- Use one loop unless there is a concrete reason to nest loops.
- Set attempt limits for goal-based work; three to five attempts is the default range unless the user specifies otherwise.
- Use longer intervals for time-based work. Match the interval to how often the source realistically changes.
- Use scripts for deterministic repeated transformations.
- Use local indexes and targeted file reads before broad scans.
- Do not spawn multiple agents or workflows unless parallel exploration meaningfully reduces risk or time.

## Example Classifications

- "Add a like button and verify it works" -> Turn-based loop with UI/browser validation.
- "Raise Lighthouse performance to 90+" -> Goal-based loop with metric threshold and max attempts.
- "Every 5 minutes check my PR and fix CI" -> Time-based loop with PR/CI checks and cancellation condition.
- "Continuously triage support bug reports and fix simple ones" -> Proactive loop with routing, per-item goals, and escalation rules.
- "Review this C# PR" -> Turn-based loop plus the C#/.NET review skill from the Copilot index.
