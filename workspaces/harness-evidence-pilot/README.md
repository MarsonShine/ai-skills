# Harness support-document evidence pilot

Task ID: T-20261022-HARNESS-DOCS
Status: completed
Source: the observability-plan review identified that `sync/check` do not cover auxiliary project documents.
Baseline: ai-skills `af63286`; MS.Microservice `b8b2d75`.

## Contract

Restore the working agreement's required task, status, recovery and PR documents when missing or empty, report their absence in `check`, and preserve existing non-empty project content.

In scope: the bootstrap engine, focused regression checks, its recovery instructions, and a pilot in MS.Microservice using a disposable copy of its harness files.
Out of scope: business changes, full agent tracing, a new recorder, automatic document migration, managed-block changes, and repository-wide workflow enforcement.

| ID | Acceptance | Evidence | Result |
| --- | --- | --- | --- |
| A1 | `check` rejects each missing or empty required support document | Regression suite R1/R2 | Passed |
| A2 | `sync --write` restores these documents and the resulting project passes `check` | Regression suite R2; MS P2-01/P2-02 | Passed |
| A3 | Existing non-empty project documents remain byte-identical; dry run writes nothing | Regression suite R2; MS P2-01/P2-02 | Passed |
| A4 | The MS project passes the updated check and evidence links resolve | MS P1/P3: project check, 19 relative links | Passed |

## Execution evidence

Recorded 2026-10-22 on Windows, Python 3.12. All commands ran from the ai-skills root. Source state: `af63286` plus this slice's engine, tests, CI and documentation changes; no subsequent engine edits before R2.

| Run | Command | Execution fact |
| --- | --- | --- |
| R1 | `python -B -X utf8 scripts/test_bootstrap_harness.py` with the baseline engine | exit 1: eight missing/empty subcases incorrectly returned 0; recovery failed with FileNotFoundError; 4 tests ran |
| R2 | `python -B -X utf8 scripts/test_bootstrap_harness.py` with the fixed engine | exit 0: 4 tests passed, including the eight subcases, restoration, byte preservation and dry-run behavior |
| R3 | `python scripts/check_skill_catalog.py` | exit 0: 25 skills, frontmatter and catalog match |

Reviewer conclusion: R1 reproduces the omission at the common document owner; R2 restores the required-file invariant without migrating project content. The missing-file assertion error in R1 is a failed recovery expectation, not a successful test.

## Reproduction and limits

Run R2 and R3 from a checkout of this slice. To reproduce R1, keep the tests but use the engine from `af63286` in an isolated checkout. The regression tests create and clean temporary fixtures, not project files.

The fix and regression evidence are committed in ai-skills `837c3dd`. The adopting project pilot is committed in MS.Microservice `b6d581a`, under `docs/validation/T-20261022-HARNESS-DOCS/`: `summary.md`, `replay.py` and two independently retained result JSON files. From that project's root, run `python docs/validation/T-20261022-HARNESS-DOCS/replay.py --skills-root <ai-skills-checkout>` to reproduce the six-step baseline/fixed-engine comparison. The candidate engine SHA-256 in both recorded runs is `ce64fd39fde8c04e8aadb22511efccf49e64aa997e28cb338afb39f442266d03`.

These checks establish support-document presence and non-destructive restoration, not document freshness, acceptance quality, business correctness or full agent tracing. Local raw console output is not a shared artifact; the summaries, retained fixture results and regression suite preserve the required facts and reproduction steps. No .NET business code changed or business/infrastructure tests ran.

## Pilot Decision

Existing command output plus a scoped reproducible fixture covered this task's execution facts. No repeated collection gap justified a general recorder, so no `trace.py`, universal event schema, host parser or completion-rate metric was introduced. The bootstrap skill offers this workflow only when an evidence pilot is requested; review and pre-push skills retain their existing evidence-reuse rules.

Mapping observations to acceptance criteria and judging freshness still requires reviewer reasoning. The pilot was executed and assessed by the same agent; it is not independent human review and provides no measured claim about review time, model success rate or API cost.
