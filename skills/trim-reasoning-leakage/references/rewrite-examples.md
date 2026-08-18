# Reasoning Leakage Rewrite Examples

Use these to identify a principle, not as text templates.

## Dead Ordinal

Leaked: “The registry rejects duplicates (decision 7: names are global).”

Rewrite: “The registry rejects duplicate names; names are global.” Link the committed decision by name when one exists.

## PR Vantage

Leaked: “This PR adds cursor pagination.”

Rewrite: “The list uses cursor pagination.”

## Fixed Regression

Leaked: “This used to double-encode multibyte labels.”

Rewrite: “Without the byte-length guard, multibyte labels are double-encoded.” Keep the named guard only when that counterfactual protects against regression.

## Reviewer Defense

Leaked: “The cast is safe; the reviewer confirmed the SDK fills these fields.”

Rewrite: “The SDK populates every optional field at this call site; its declared type is broader than the runtime guarantee.” Delete the comment if the invariant is obvious locally.

## Test Walkthrough

Leaked: “The test creates a session, sends two messages, waits, and checks four entries.”

Rewrite: “Two round trips produce four durable entries; the projection deduplicates the shared prefix.”

## Overcorrection Traps

- Do not change “exception pending migration” into “approved exception”; that reverses an obligation.
- Do not remove “hypothetical” or “future” and accidentally claim an unimplemented component exists.
- When half a sentence is narration and half states a real coupling, keep the coupling.
- Keep “measured” when a limit is justified by observed data; the provenance distinguishes evidence from a definition.
