# Pre-Push Evidence Selection

## Change-to-Check Matrix

- **Package or module behavior:** focused owning unit/integration tests; include affected source in coverage when the repository supports scoped coverage.
- **Shared interface or schema:** tests for providers and consumers, typecheck, compatibility fixtures, and migration or serialization checks.
- **Public exports, package manifests, build config, workers, bins, or generated bundles:** build plus the real built-artifact smoke and relevant package hygiene.
- **Documentation, code-linked comments, generated catalogs, or decision records:** documentation generation, link/fragment validation, formatting, and repository doc gates.
- **Model-, CLI-, editor-, terminal-, or UI-visible output:** focused snapshots or a real runnable scenario that observes the exact output.
- **Database, queue, process, or external provider behavior:** focused integration/e2e checks when dependencies and credentials are available; never expose secrets.
- **Only formatting changes:** formatter or repository diff check, unless formatting changes generated or user-visible behavior.

## Discovering Tests

Use the project's dependency graph or test-related command when available, then inspect the selected tests. Dynamic loading, configuration, subprocesses, workers, built artifacts, and external providers often require explicit tests that static relationships cannot discover.

## Full Rehearsal

Run the complete local approximation only when the user requests it, CI is being diagnosed, or the change is genuinely repository-wide. CI remains responsible for exhaustive platform and environment matrices unless repository instructions say otherwise.

## History Rewrites

Before an authorized force-push, fetch and record the exact remote head. Use lease-protected publication so concurrent remote movement aborts the push. After any rewritten push, re-fetch live heads and re-audit review threads, approvals, mergeability, and checks because commit hashes and inline anchors may have changed.

When a stack synchronization publishes rewritten branches before local validation is possible, validate each affected layer immediately afterward and block merging until all selected evidence passes.
