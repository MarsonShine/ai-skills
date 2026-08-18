# Code Review Dimensions

Use only dimensions relevant to the diff. This is a recall aid, not a quota.

## Contracts and Data

- Trace both sides of changed interfaces, formats, schemas, events, and configuration.
- Check input validation at real trust boundaries: files, network, queues, processes, plugins, user input, model/tool JSON, and durable storage.
- Verify derived or cached values update at the documented success point and remain tied to an authoritative source.
- Check compatibility and migration behavior for persisted or externally consumed data.

## Lifecycle and Concurrency

- Look for work published before initialization succeeds, cancellation during awaited setup, multiple terminal outcomes, callback exceptions, incomplete detach, and disposal that returns before workers stop.
- Identify the owner of each process, timer, listener, worker, handle, and mutable state transition.
- Require cleanup tests for new registrations or long-lived resources.

## Enforcement and Security

- Follow every authorization or policy decision to the operation it is meant to block.
- Exercise alternate callers that may bypass UI, schema, prompt, facade, middleware, or listener ordering.
- Check logs and diagnostics for secrets, personal data, tokens, internal paths, and over-broad error detail.

## Bounds and Performance

- Apply limits to the complete retained or emitted value, including wrappers and metadata.
- Probe empty, exact-limit, oversized-single-item, aggregate, and multibyte cases.
- Distinguish measured hot-path regressions from speculative micro-optimization.

## Tests and Real Entry Paths

- Prefer assertions on external state, events, logs, responses, or durable output over restating implementation steps.
- Check that a test fails for the intended regression and includes a negative control where practical.
- Exercise the shipped loader, binary, worker, transport, framework bootstrap, or generated artifact when configuration or packaging is part of the behavior.
- Treat snapshots and expected-output changes as behavior changes requiring semantic review.

## Documentation and User-Visible Text

- Public behavior, defaults, errors, wire fields, and limitations should update their owning docs in the same change.
- Prompts, diagnostics, CLI output, and UI strings are behavior; verify the actual rendered or model-visible result.
- Comments should preserve non-obvious contracts and rationale, not narrate control flow or the review history.
