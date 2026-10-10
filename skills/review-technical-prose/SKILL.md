---
name: review-technical-prose
description: "Review or edit technical prose for complete contracts, placement, duplication, and concision. Not for translation, code review, document synchronization, or authoring-session residue alone."
---

# Review Technical Prose

Preserve every load-bearing fact, then remove repetition, authoring residue, and decoration. Shorter text is not automatically better.

## Workflow

1. Confirm the requested scope, intended readers, and artifact type; read applicable repository documentation rules.
2. Identify the owning code, configuration, behavior, or document before judging its prose.
3. Check that the intended reader can follow the explanation: introduce necessary unfamiliar concepts before using them and connect them to the implementation with a concrete example when useful. Do not require generic background for readers who already know it.
4. Classify each passage as keep, add, trim, restore, move, split, link, or defer. Separate README usage and material limitations, maintainer design detail, and brief code comments; avoid repeating tutorials or creating unnecessary documents.
5. Preserve actors, conditions, timing, ordering, modality, exceptions, ownership, side effects, failures, and consequences.
6. Keep one authoritative home for extended rationale and detailed explanation; repeat only the local contract needed for safe use.
7. Edit source material before generated catalogs, snapshots, or derived documentation, then regenerate them.
8. Run the repository's prose, link, formatting, generation, and behavior checks for visible strings.

Read `references/editorial-standard.md` for placement and coverage guidance. If the problem is specifically authoring-session or reasoning-transcript residue, also use `../trim-reasoning-leakage/SKILL.md`.

## Boundaries

- Review or audit requests report findings without editing unless the user also asks for changes.
- Do not rewrite frozen archives, vendored documentation, generated output, or recorded fixtures at the derivative layer.
- Do not replace precise technical nouns with vague words such as “thing,” “shape,” or “flow” merely to sound simpler.
- Ask when two placements are equally valid and the choice changes long-term ownership.

## Output

Report the actual files or modules inspected, clear edits or findings, deliberate keeps, deferred choices, derivative files regenerated, and checks actually run. Do not describe a scoped review or rewrite as covering the whole repository.
