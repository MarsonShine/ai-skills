---
name: trim-reasoning-leakage
description: "Remove authoring-session, plan, or PR/review residue from durable prose so it stands alone. Not for general copyediting, correctness review, or code simplification."
---

# Trim Reasoning Leakage

Durable prose should be verifiable from the repository and its intentional external references, without access to a private chat, draft plan, or review conversation.

## Test Every Suspect Passage

Ask whether a reader at the current repository state can resolve every reference and verify every claim without the authoring session. If not, preserve each factual clause in repository terms and remove the transcript around it. Delete a passage outright only when it contains no useful proposition.

The workflow below preserves complete propositions without loading another skill. Read `references/leakage-patterns.md` when taxonomy or search probes help, and `references/rewrite-examples.md` for borderline edits. Use `../review-technical-prose/SKILL.md` only when the request also needs broader contract or information-placement review.

## Workflow

1. Confirm scope and read repository exclusions. Do not edit vendored code, frozen archives, generated output, or recorded fixtures at the derivative layer.
2. Search for known patterns, then read dense prose without a pattern in hand; search probes intentionally over-match and still miss cases.
3. Trace generated text to its owner and update the source before regenerating.
4. Enumerate the passage's actors, conditions, obligations, exceptions, ownership, failure behavior, and consequences.
5. Rewrite surviving facts in present repository terms. Move real future work to the repository's TODO, issue, or decision mechanism.
6. Re-run searches, resolve remaining citations, and run checks for touched docs, generated text, translations, prompts, or snapshots.

## Boundaries

- Keep resolvable issue and standard references, required suppression reasons, measured provenance, runtime old/new states, and sanctioned history inside decision records or postmortems.
- Do not turn a future or hypothetical design into a claim that it already exists.
- Do not replace an obligation with an endorsement or delete provenance from a measured limit.
- Treat model-visible and user-visible wording as behavior; require its normal validation instead of silently changing it.
