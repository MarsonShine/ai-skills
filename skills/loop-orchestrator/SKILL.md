---
name: loop-orchestrator
description: Design bounded execution loops for recurring, scheduled, monitored, event-driven, or repeated-attempt work. Use when cadence, measurable stop conditions, retry limits, or cost boundaries matter. Do not use for one-off coding, review, planning, validation, or human-gated commit/slice delivery unless a separate schedule, monitor, or retry loop is requested.
---

# Loop Orchestrator

Use this skill only when work must repeat across attempts, time, or incoming events. Make the trigger, stop condition, validation method, and cost boundary explicit without taking over the task's domain workflow.

Default to the user's language. For Chinese input, respond in Chinese.

## Core Workflow

1. Confirm that the request needs a loop.
   - Goal signal: the user wants repeated attempts until a measurable target is reached or an attempt limit is exhausted.
   - Time signal: the same check or action must run on a schedule or at an interval.
   - Event signal: new items from an ongoing external source must be processed continuously or whenever an event arrives. A human review checkpoint in bounded staged delivery is not an event loop.
   - If none applies, return to the ordinary bounded workflow without emitting a loop contract.

2. Classify the loop.
   - Goal-based loop: success can be measured objectively and repeated attempts are useful.
   - Time-based loop: the same work should run at an interval or schedule.
   - Proactive loop: a long-running workflow reacts to incoming work or events.
   - Read `references/loop-decision-matrix.md` only when the loop type, cadence, or stopping rule is not obvious, or when defining a reusable automation.

3. Define the operating contract.
   - Trigger: what starts each run.
   - Work unit: what one attempt, scheduled run, or event handler processes.
   - Stop condition: what completes one run and what terminates the overall loop.
   - Validation: what observable evidence proves progress or success.
   - Cost boundary: maximum attempts, useful interval, tool/model limits, and escalation point.
   - State: what cursor, checkpoint, or result must persist between runs.

4. Use the platform's real execution mechanism.
   - Prefer an available goal, automation, monitoring, or event tool over a textual promise to repeat work later.
   - Configure only the loop lifecycle here. Preserve separately selected domain instructions for the work performed inside each run.
   - Follow the active runtime's permissions and authorization boundaries; this skill grants no additional authority.

5. Validate the loop itself.
   - Confirm that repeated runs do not silently duplicate completed work.
   - Exercise the terminal condition or a safe representative stop path.
   - Record what happens after transient failure, permanent failure, or exhausted attempts.

## Response Shape

When a loop contract helps the user verify the workflow, keep it concise:

```markdown
Loop: [goal-based | time-based | proactive]
Trigger: [attempt, schedule, or event]
Stop condition: [concrete completion condition]
Validation: [checks to run]
Cost boundary: [attempt limit / interval / tool boundary]
```

Do not add this template to bounded one-off tasks.

## Quality Rules

- Prefer the simplest loop that can succeed.
- Never leave the stop condition implicit on repeated, scheduled, or ongoing work.
- Set a finite attempt or cost limit for goal-based loops.
- Prefer deterministic checks, tests, screenshots, logs, metrics, or real interaction over self-assessment.
- Convert repeated deterministic work into scripts or tool calls when that is cheaper and more reliable than reasoning repeatedly.
- Avoid nested loops unless the inner and outer stop conditions are independently necessary.
- Route human-gated commit or slice delivery to its staged-delivery workflow unless the request also has a real schedule, monitor, or retry loop.
- Do not reinterpret an ordinary bounded task as a loop merely because it has several steps or requires validation.
