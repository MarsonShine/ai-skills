# Simplification Candidate Playbook

## Strong Candidate Families

- Public methods, events, options, registries, or formats with no production consumer.
- Tests and docs as the only consumers of behavior that is not a current obligation.
- Two durable or transient representations of the same authoritative fact.
- Generic interfaces whose unused generality adds maintenance cost for their current consumers.
- Packages or services that contain only support, demo, or test glue.
- Defensive copies, validators, and lifecycle machinery protecting impossible same-process inputs rather than real trust boundaries.
- Hand-written parsers, retry loops, globbing, diffing, or protocol utilities duplicated by existing code, runtime or platform capabilities, or installed dependencies.
- Compatibility paths with no supported producer, durable data, or external consumer remaining.

## Proof Checklist

Search the exact name and its serialized forms. Inspect:

- production source and executable examples;
- configuration and dependency injection;
- dynamic loaders, reflection, registries, and plugin manifests;
- public exports and downstream packages;
- tests, snapshots, docs, migration code, and decision records;
- persisted or wire representations that may outlive source callers.

Reject the candidate when a current production caller exists and removal would be an unowned product choice, or when a recorded defensive constraint still applies.

## Implementation Gate

Apply a candidate only when all of the following are true:

- the user requested implementation rather than an audit-only report;
- production, dynamic, external, persisted, and documentation consumers have been accounted for;
- the required behavior is protected by focused tests, executable checks, or other reproducible evidence;
- any compatibility or migration obligation is either preserved or explicitly retired by its owner; and
- the change can be validated and reported as one coherent simplification.

Update or remove tests and documentation only after establishing which behavior remains required. Re-run the focused evidence first, then the smallest broader check needed for shared surfaces.

## Replacement Selection

Search for simpler ways to preserve the required behavior in this order:

1. Existing repository code that already owns the operation.
2. Runtime builtins or standard-library features.
3. Capabilities of the supported platform or framework.
4. Dependencies already installed in the project.
5. Custom code for the remaining required semantics.

This is a discovery order, not an absolute ranking. Compare semantic fit, supported environments, failure behavior, and ownership costs. Keep the current implementation when reuse needs more glue or weakens an obligation; do not replace a dependency merely to move up the list. Fewer lines or files alone do not establish a better design.

Count implementation, dedicated tests, docs, and glue deleted, then subtract adapters and residual semantics. For dependency changes, check maintenance, adoption, release cadence, transitive footprint, license, supported runtimes, and security posture. A wrapper that preserves the same complexity is not a simplification.

## Lifecycle Analysis

For asynchronous code, map each state flag, readiness promise, cancellation path, callback, disposer, and resource to an owner and transition. Collapse mechanisms only when they represent the same fact. Preserve separate guards for publication rollback, callback containment, first-terminal-outcome arbitration, process ownership, and dispose-to-quiescence when those risks are real.
