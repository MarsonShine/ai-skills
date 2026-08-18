# Technical Prose Editorial Standard

## Preserve the Complete Proposition

Before editing, enumerate the factual clauses in a passage:

- who acts and what happens;
- conditions, timing, and order;
- must, may, should, or never;
- negative guarantees and exceptions;
- ownership and side effects;
- failure behavior and user consequence.

Remove adjectives, repetition, and narration only when those clauses remain clear. Keep non-obvious rationale locally when omitting it could cause misuse; otherwise link to its authoritative explanation.

## Place Detail at Its Owner

- A parent overview explains its own subject fully and summarizes direct children.
- A tutorial leads an identified reader through ordered work to an observable result.
- A reference supports lookup within a declared scope without requiring sequential reading.
- Generated catalogs are edited through their generator or source metadata.
- A mixed tutorial/reference document should be split when both forms are substantial.

## Coverage by Surface

- **Public API docs:** returns, distinctions, failures, side effects, ownership, timing, cancellation, and durability.
- **Internal comments:** non-local invariants, race ordering, ownership, security, and surprising failure behavior.
- **Module docs:** role, responsibilities, dependencies, and non-obvious architecture choices.
- **Tests:** only non-obvious fixture, entry-path, platform, or observation rationale.
- **READMEs:** configuration, behavior, limitations, failures, extension points, and user/model-visible effects.
- **Decision records:** unique rationale, alternatives, consequences, verification evidence, and known gaps.
- **Prompts and visible strings:** exact wording is behavior; inspect rendered or model-visible output.
- **Diagnostics:** failing subject, violated rule, and corrective action.

## Duplication and Length

Search distinctive phrases and keep one home for extended explanation. Replace duplicates with links when the local reader can still use the interface safely. Treat word budgets as discovery and design constraints, never as permission to delete obligations.

## Calibration Examples

**Too vague:** “The worker cleans up during shutdown.”

**Complete:** “Shutdown requests worker cancellation and waits for the worker to release its child processes before disposal resolves.”

**Control-flow narration:** “First normalize the label, then truncate it, then wrap it.” Delete this when the code already shows it.

**Useful test rationale:** “Two round trips must produce four durable entries; the projection deduplicates the shared prefix.”

**Local contract plus linked rationale:** State the caller-visible behavior and failure locally, then link the algorithm or history instead of repeating it.
