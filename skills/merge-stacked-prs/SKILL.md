---
name: merge-stacked-prs
description: "Verify or land dependent GitHub pull requests in one repository, where a PR uses another open PR branch as its base. Not for independent PRs or ordinary branch merges."
---

# Merge Stacked Pull Requests

Let GitHub's stack object own ordering, checks, retargeting, and merge state. Do not imitate stack semantics by merging and manually retargeting individual pull requests.

## Preflight

1. Require official `gh stack` support. If unavailable, stop rather than falling back to per-PR merges.
2. Fetch live metadata for every candidate: repository, author, state, draft status, base, exact head, review decision, mergeability, and checks.
3. Confirm every head branch is in the same repository and establish the bottom-to-top dependency chain from live bases.
4. Query GitHub's stack object and verify one stack number, trunk, membership, order, and positions. Paginate entries when necessary.
5. If the live chain and official stack conflict, or multiple stack objects are involved, ask the user before changing anything.

## Link and Synchronize

- Link an unstacked same-author chain only when its bases establish an unambiguous order. Ask before linking mixed-author chains.
- Never dissolve, reorder, or rebuild an existing stack without explicit direction.
- Refresh branches only when current merge state or repository rules require it.
- After a cascading rebase or stack synchronization, re-fetch heads and rerun relevant checks for every rewritten layer. Treat earlier approvals, inline anchors, and commit-based evidence as stale until rechecked.
- Never use an unleased force push.

## Merge

Immediately before merging, re-query the stack and require every selected PR to be open, non-draft, correctly ordered, and compliant with repository review and check requirements.

- “Land the stack” means the complete stack.
- A partial landing requires an explicit boundary and includes every layer from the bottom through that boundary.
- Use the official stack merge command for the stack or boundary. Do not issue per-PR merge commands as a fallback or bypass required checks.

## Verify

Wait until every selected PR reports merged; queued is not complete. For a partial landing, verify remaining layers still form the expected stack and recheck their heads and CI. Delete branches only in a separate pass after confirming no open PR still uses each branch as a base.

Report the verified order, exact heads before mutation, synchronization performed, checks rerun, merged PRs, remaining stack, and any branches intentionally retained.
