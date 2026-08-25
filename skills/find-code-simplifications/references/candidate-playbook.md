# Simplification Candidate Playbook

## Strong Candidate Families

- Public methods, events, options, registries, or formats with no production consumer.
- Tests and docs as the only consumers of behavior that is not a current obligation.
- Two durable or transient representations of the same authoritative fact.
- Generic interfaces expanded for one internal consumer.
- Packages or services that contain only support, demo, or test glue.
- Defensive copies, validators, and lifecycle machinery protecting impossible same-process inputs rather than real trust boundaries.
- Hand-written parsers, retry loops, globbing, diffing, or protocol utilities already covered by a maintained dependency or runtime builtin.
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

## Dependency Replacement

Compare the maintained dependency or builtin against the exact current surface. Count implementation, dedicated tests, docs, and glue deleted, then subtract adapters and residual semantics. Check maintenance, adoption, release cadence, transitive footprint, license, supported runtimes, and security posture. A wrapper that preserves the same complexity is not a simplification.

## Lifecycle Analysis

For asynchronous code, map each state flag, readiness promise, cancellation path, callback, disposer, and resource to an owner and transition. Collapse mechanisms only when they represent the same fact. Preserve separate guards for publication rollback, callback containment, first-terminal-outcome arbitration, process ownership, and dispose-to-quiescence when those risks are real.
