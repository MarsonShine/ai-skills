# Bilingual Pairing Workflow

## Existing Pair Update

1. Use the repository's diff or briefing tool when available to find the smallest aligned units: paragraph, list item, table row, heading section, then whole document.
2. Compare the last synchronized source, current authored side, and current counterpart when metadata supports three-way analysis.
3. Preserve counterpart wording outside changed units.
4. Verify the changed units clause by clause: no added or dropped meaning, terminology follows the glossary, and inline code survives exactly.
5. Read the updated counterpart by itself for naturalness, then compare structures mechanically.
6. Record hashes or sidecars only after semantic review.

Mechanical-only changes inside shared code fences may be copied through a repository-provided tool when it validates the resulting structure.

## New Repository Pair

Create a new pair only when the repository defines its naming, directory, switcher, manifest, and metadata conventions and the user explicitly requests a paired document. Read the entire terminology source before translation. Work section by section, then perform a clause-level comparison and an independent target-language read.

If the repository does not define pairing conventions, ask whether the user wants a standalone translation or wants to establish a new repository-wide convention. Do not decide silently.

## Rename or Delete

Move or delete every required counterpart and sidecar atomically. Repair inbound links, navigation, manifests, and locale routes in the same change. Never modify frozen or sealed pairs unless their lifecycle rules permit it.

## Structural Checks

Compare heading depth and order, fenced block count and language, list kinds and item counts, ordered-list starts, tables, link targets, anchors, inline code, emphasis, images, and switcher links. Mechanical structure checks do not prove translation quality.
