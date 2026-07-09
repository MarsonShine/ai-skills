---
name: loop-orchestrator
description: Classify complex user requests into the right execution loop, define stop conditions, validation checks, token/cost boundaries, and whether to execute or only plan based on current permissions. Use for multi-step coding tasks, automation, monitoring, scheduled work, quality gates, repeated iteration, vague complex goals, or any request where Codex should decide between turn-based, goal-based, time-based, or proactive loops. Do not use for simple factual questions or tiny one-step edits.
---

# Loop Orchestrator

Use this skill to turn a complex request into a bounded agent loop before acting. The goal is to avoid vague "keep working" behavior by making the trigger, stop condition, validation method, and cost boundary explicit.

Default to the user's language. For Chinese input, respond in Chinese.

## Core Workflow

1. Decide whether a loop is needed.
   - If the request is simple, answer or perform it directly without mentioning loop theory.
   - If the request is multi-step, iterative, recurring, open-ended, quality-sensitive, or automation-like, classify it before acting.

2. Classify the loop.
   - Turn-based loop: one user request drives exploration, edits, validation, and a final response.
   - Goal-based loop: success can be measured objectively and repeated attempts are useful.
   - Time-based loop: the same work should run at an interval or schedule.
   - Proactive loop: a long-running workflow reacts to new work items and may coordinate multiple agents or tools.
   - Read `references/loop-decision-matrix.md` when the classification is not obvious or when writing a reusable plan.

3. Define the operating contract.
   - Trigger: what starts each run.
   - Stop condition: what counts as complete or when to stop trying.
   - Validation: how to inspect the real result, not just the code or text.
   - Cost boundary: max attempts, interval, model/tool choice, and when to ask the user.
   - External context: files, repositories, docs, browser, test tools, APIs, MCP servers, or automations needed.

4. Apply the permission policy.
   - If active instructions forbid mutation, the session is in Plan Mode, the environment is read-only, or approvals/tools are unavailable, output a concrete loop plan only.
   - If permissions allow execution and the user clearly asked for action, execute the chosen loop: gather context, act, validate, repair failures, and report the result.
   - If the requested loop requires scheduled or recurring automation in Codex, first search for the automation tool and use the platform tool instead of inventing raw schedule directives.

5. Reuse repository skills when useful.
   - For domain-specific tasks, read `references/skill-routing-index.md`.
   - If the index contains a matching sibling skill, read that skill's `SKILL.md` before acting and apply its rules as supplementary guidance.
   - Treat the index paths as relative to this skill directory after the repository is installed as a plugin.

## Response Shape

For execution-capable requests, keep the loop framing concise:

```markdown
Loop: [turn-based | goal-based | time-based | proactive]
Stop condition: [concrete completion condition]
Validation: [checks to run]
Cost boundary: [attempt limit / interval / tool boundary]
```

Then continue with the work.

For plan-only requests, output:

```markdown
### Loop Plan
- Loop type:
- Trigger:
- Stop condition:
- Validation:
- Cost boundary:
- Tools / skills:
- Execution steps:
- Acceptance criteria:
```

For simple requests, do not output the template.

## Quality Rules

- Prefer the simplest loop that can succeed.
- Never leave the stop condition implicit on iterative or recurring work.
- Prefer deterministic checks, tests, screenshots, logs, metrics, or real interaction over self-assessment.
- Convert repeated deterministic work into scripts or tool calls when that is cheaper and more reliable than reasoning repeatedly.
- Ask the user only when a missing decision materially changes scope, risk, cost, or external side effects.
- When a run fails, update the loop contract if the failure reveals a reusable lesson.
