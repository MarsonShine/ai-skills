# Implementation Choices

Compare alternatives against the actual contract. A shorter spelling or familiar builtin is not evidence that two implementations behave the same.

| Decision | A sufficient small solution | When more machinery is justified |
|---|---|---|
| Reuse a helper | Call the existing helper when its inputs, output, error behavior, and ownership match. | Do not broaden a helper's contract for unrelated callers just to share a few lines. A separate implementation may preserve a real boundary. |
| Use a native control | A native date input can satisfy an ordinary single-date field on the supported platforms. | Date ranges, unavailable dates, required interactions, accessibility behavior, or an explicit component choice may require the existing UI library. Verify those requirements first. |
| Select a library | Reuse an installed, maintained package when it already supplies the required behavior. | A standard-library replacement can need adapters or lose semantics; a new dependency can be justified when neither the installed packages nor a small implementation meets the contract. Count the ongoing footprint, not just the import. |
| Retain an interface | Use the project's existing boundary when it controls dependency lifetime, isolates an external service, or is publicly consumed. | A single implementation is not a deletion proof. Avoid adding a new abstraction solely for a hypothetical second implementation. |
| Cache results | A bounded memoizer is sufficient for stable values when eviction by recency is the whole contract. | Expiration, tenant isolation, invalidation, async behavior, and concurrency are separate requirements. An LRU cache does not provide TTL expiration by itself. |
| Validate input | Reuse validation at the appropriate trust boundary. | Presence of `@` is not equivalent to an established email contract; decoding a token does not verify its signature or authorization. Do not replace required checks with weaker predicates. |
| Simplify lifecycle state | Merge state only when it represents the same fact with the same owner and transitions. | Cancellation, completion, publication rollback, and disposal can protect different outcomes. Cleanup must still wait for owned work to stop before releasing resources. |
| Fix shared behavior | If several entrypoints share a broken normalization rule, fix the common owner and exercise the entrypoints. | A smaller patch in one caller can leave siblings broken. Preserve distinct caller policies where their contracts actually differ. |

## Choosing Evidence

Use the project's current test framework, fixtures, and executable checks where they protect the changed contract. Check normal behavior, the reported failure, representative unseen variants, and relevant boundaries. Expand validation only for a concrete shared risk or a required repository gate.

For a platform replacement, exercise the interactions and supported environments that matter to the request. For an abstraction or dependency change, inspect consumers and residual adapters before concluding that maintenance cost fell. Report unresolved evidence as a limitation rather than treating a successful happy-path check as proof of equivalence.
