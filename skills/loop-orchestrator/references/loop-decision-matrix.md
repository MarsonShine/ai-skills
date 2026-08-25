# Loop Decision Matrix

Use this reference only after the request has a real repetition signal: repeated attempts toward a measurable target, a schedule, or an ongoing event source. Complexity or multiple steps alone do not make a task a loop.

## Decision Table

| Loop type | Use when | Trigger | Stop condition | Cost control |
| --- | --- | --- | --- | --- |
| Goal-based | The desired result has an objective threshold and repeated attempts can improve it. | Current request plus an attempt. | Target is reached, an invariant fails, or max attempts is hit. | Set max attempts and measurable acceptance criteria. |
| Time-based | The same check or action should repeat on a schedule. | Interval, cron, or scheduled routine. | User cancels, queue is empty, PR is merged, issue is resolved, or routine reaches a defined terminal state. | Use the longest useful interval; prefer event triggers if available. |
| Proactive | Incoming work or events should be processed continuously. | Event trigger, queue item, webhook, or scheduled scan. | Each item reaches a terminal state; the routine continues until disabled. | Bound concurrency, retries, queue age, and escalation behavior. |

## Stop Condition Templates

- Performance goal: "Stop when metric X is at least Y for page/workload Z, or after N attempts with the best result and blockers reported."
- Repeated repair: "Stop when the target check passes, a non-retryable failure occurs, or N repair attempts have been validated and reported."
- Recurring monitor: "Stop each run when all new items since the last run are processed or explicitly deferred; stop the routine only when cancelled or the source is closed."
- Proactive queue: "Stop each item when it is completed, escalated, or rejected; stop the routine only when disabled or the queue source closes."

## Loop Validation Checklist

- Validate the result of each attempt or run with domain-appropriate evidence.
- Preserve a cursor, checkpoint, or idempotency key when repeated runs could revisit the same work.
- Define behavior for empty input, duplicate events, missed schedules, transient failures, permanent failures, and exhausted retries when applicable.
- Verify one safe representative terminal path before treating the loop as operational.
- State which lifecycle behavior could not be exercised in the current environment.

## Cost And Token Boundaries

- Use one loop unless there is a concrete reason to nest loops.
- Set attempt limits for goal-based work; three to five attempts is the default range unless the user specifies otherwise.
- Use longer intervals for time-based work. Match the interval to how often the source realistically changes.
- Use scripts for deterministic repeated transformations.
- Bound concurrency and retry backoff for event-driven work.
- Escalate when the next attempt would exceed the agreed cost, time, or external-impact boundary.

## Example Classifications

- "Raise Lighthouse performance to 90+, trying at most four revisions" -> Goal-based loop with a metric threshold and attempt limit.
- "Every 5 minutes check my PR and stop after it merges" -> Time-based loop with a terminal repository state.
- "Continuously triage new support reports and escalate uncertain cases" -> Proactive loop with per-item terminal states.

## Non-Matches

- Implementing a bounded feature and running its tests.
- Reviewing a specific change once.
- Producing a plan, report, or artifact in one request.
- Running the ordinary validation required to complete a one-off task.
