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

- **READMEs:** user-facing purpose and behavior, deployment prerequisites, working examples, parameters, relevant extension points, and necessary limitations, including user/model-visible effects. Prefer examples and tables where useful. Keep constraints that change correct use visible; move extended algorithms, extreme-case analysis, and test detail to design documentation.
- **Technical design docs:** maintainer-facing responsibilities, dependencies, implementation principles, data flow, algorithms, errors, boundaries, and tradeoffs. Explain prerequisites needed to follow that implementation, connect terminology to code, and link to the README instead of duplicating its usage tutorial. Follow the repository's location, normally `docs/`; do not split a trivial explanation into another file.
- **Public API/XML docs:** brief purpose, parameters, key distinctions, and constraints. Keep `summary` to one or two sentences. Preserve needed return, failure, ownership, timing, cancellation, and durability contracts in appropriate tags or remarks; extended implementation walkthroughs belong in design docs.
- **Internal comments:** non-obvious invariants, reasons, race ordering, ownership, security, and surprising failure behavior. Do not restate code or turn comments into an implementation article.
- **Technical articles:** establish the intended reader, explain needed concepts before relying on them, and connect mechanisms to concrete examples and their limits. A general subject tutorial is unnecessary when a short definition and example suffice.
- **Tests:** only non-obvious fixture, entry-path, platform, or observation rationale.
- **Decision records:** unique rationale, alternatives, consequences, verification evidence, and known gaps.
- **Prompts and visible strings:** exact wording is behavior; inspect rendered or model-visible output.
- **Diagnostics:** failing subject, violated rule, and corrective action.

## Duplication and Length

Search distinctive phrases and keep one home for extended explanation. Replace duplicates with links when the local reader can still use the interface safely. Treat word budgets as discovery and design constraints, never as permission to delete obligations.

Check prerequisite knowledge as well as completeness. An explanation that starts with specialized terms the intended reader cannot interpret is missing context even when its facts are correct. Add only the definitions, component relationships, or input/output example needed to understand the mechanism; retain precise technical names rather than replacing them with vague language.

## Calibration Examples

**Too vague:** “The worker cleans up during shutdown.”

**Complete:** “Shutdown requests worker cancellation and waits for the worker to release its child processes before disposal resolves.”

**Control-flow narration:** “First normalize the label, then truncate it, then wrap it.” Delete this when the code already shows it.

**Useful test rationale:** “Two round trips must produce four durable entries; the projection deduplicates the shared prefix.”

**Local contract plus linked rationale:** State the caller-visible behavior and failure locally, then link the algorithm or history instead of repeating it.
