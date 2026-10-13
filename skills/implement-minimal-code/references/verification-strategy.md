# Verification Strategy

Decide how to verify the current behavior and whether to retain new automated tests separately. Respect explicit user requirements, established TDD workflows, and mandatory project checks in both decisions.

## Match Evidence to the Risk

Identify what could fail in the changed contract and which observation would reveal it. Consider consequence, shared consumers, reversibility, and uncertainty; a one-line authorization or persistence change can carry substantial risk. Use only relevant dimensions, without scoring every task or generating a verification plan by default.

- For a local presentation change, inspect the rendered result and affected interaction when available. A source-string assertion does not prove layout or usability.
- For a behavior fix, verify the reported failure and representative cases arising from the same mechanism. Existing coverage, a focused reproduction, or an appropriate integration check may suffice; do not enumerate unrelated inputs or every category of boundary.
- For shared contracts, permissions, concurrency, lifecycle, or durable state, observe the relevant consumer behavior, rejection, ordering, cleanup, or persisted result. A build or happy-path smoke alone does not establish these properties.
- For platform or compatibility behavior, use the supported runtime when it is needed to observe the failure. Static inspection and substitute runtimes can support a narrower claim; disclose what still needs the target environment.

## Decide What to Keep

Inspect existing checks before adding tests. A passing suite counts as evidence only for the behavior it exercises. Ask which credible regression an additional assertion would catch that current coverage misses. For a bug, a failure before the fix and success afterward is strong evidence when practical; do not build a costly replay system merely to obtain it.

Extend an existing test or fixture when it provides durable protection economically. Add a new test boundary or helper only when it exposes a real missing behavior. Do not add duplicate assertions, implementation-mirroring tests, broad mock hierarchies, dependencies, or a parallel test harness solely to make a small change appear tested. Conversely, missing infrastructure does not remove a significant risk or a mandatory check.

Temporary reproductions and manual observations can establish current behavior without becoming permanent test files. Retain automated coverage when its credible future detection value warrants its setup and maintenance cost, including for small fixes. Neither test count nor the ratio of test lines to production lines is a quality target.

## Stop and Report

Stop when mandatory checks pass and the affected behavior has sufficient evidence with no unresolved material risk requiring further investigation. Reuse results while the relevant source, dependencies, configuration, and environment remain valid. A later commit or push alone does not invalidate them; changed inputs, failures, and new concrete risks can.

When a verification tool fails, try a targeted recovery only when a concrete hypothesis and the behavior's risk justify it. Prefer an existing simpler method that observes the same property. If attempts stop producing relevant evidence, report the limitation instead of expanding into a custom harness or repeated environment repair. A blocked mandatory check or material risk remains unresolved; user-requested tooling repair is a separate authorized scope.

Report actual checks and their outcomes, the reason for adding or reusing tests, and material unverified behavior briefly. When a required environment is unavailable, state the missing check and its consequence. Do not label it passed, silently lower the requirement, or compensate with unrelated checks.
