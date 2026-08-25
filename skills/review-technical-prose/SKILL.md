---
name: review-technical-prose
description: Review or edit durable technical prose—Markdown, API docs, JSDoc, comments, prompts, diagnostics, and user-visible strings—while preserving complete contracts. Use for 文档审查, 精简注释, information placement, deduplication, or concision. Do not use for program behavior review, translation, documentation-site synchronization, or decision-record lifecycle work.
---

# Review Technical Prose

Preserve every load-bearing fact, then remove repetition, authoring residue, and decoration. Shorter text is not automatically better.

## Workflow

1. Confirm the requested scope and read applicable repository documentation rules.
2. Identify the owning code, configuration, behavior, or document before judging its prose.
3. Classify each passage as keep, add, trim, restore, move, split, link, or defer.
4. Preserve actors, conditions, timing, ordering, modality, exceptions, ownership, side effects, failures, and consequences.
5. Keep one authoritative home for extended rationale and detailed explanation; repeat only the local contract needed for safe use.
6. Edit source material before generated catalogs, snapshots, or derived documentation, then regenerate them.
7. Run the repository's prose, link, formatting, generation, and behavior checks for visible strings.

Read `references/editorial-standard.md` for placement and coverage guidance. If the problem is specifically authoring-session or reasoning-transcript residue, also use `../trim-reasoning-leakage/SKILL.md`.

## Boundaries

- Review or audit requests report findings without editing unless the user also asks for changes.
- Do not rewrite frozen archives, vendored documentation, generated output, or recorded fixtures at the derivative layer.
- Do not replace precise technical nouns with vague words such as “thing,” “shape,” or “flow” merely to sound simpler.
- Ask when two placements are equally valid and the choice changes long-term ownership.

## Output

Report scope inspected, clear edits or findings, deliberate keeps, deferred choices, derivative files regenerated, and checks actually run.
