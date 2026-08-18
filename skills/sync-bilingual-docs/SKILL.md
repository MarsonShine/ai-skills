---
name: sync-bilingual-docs
description: Synchronize repository-managed bilingual document pairs only when the user explicitly invokes $sync-bilingual-docs or makes an unambiguous pair-maintenance request such as “同步已有双语文档对”, “同时更新仓库中的中英文配对文件”, or “保持已配对的两种语言文件一致”. Preserve minimal counterpart edits, structure, terminology, links, and pairing metadata. Never use for requests phrased only as 翻译文档, 英译中, 中译英, translate this, pasted text, article or URL translation, or standalone translation; route those to a general translation skill.
---

# Synchronize Bilingual Repository Documents

## Strict Invocation Boundary

Use this skill only for an existing repository pairing workflow and only after an explicit request to synchronize both sides. Do not infer it from a translation request, a bilingual file, or the presence of localization folders.

Route ordinary English-to-Chinese text, article, file, or URL translation to `../translate-tech-en-zh/SKILL.md`. If the user wants a new standalone translation rather than a maintained pair, this skill must not run.

## Workflow

1. Read repository instructions, localization rules, terminology sources, pair manifests, sidecar metadata, generators, and validation commands.
2. Confirm the exact pair and identify which side contains the authored change for this update. If both sides changed independently, stop and ask how conflicts should be reconciled.
3. Classify the task as minimal counterpart update, creation of a repository-defined pair, rename, or deletion.
4. For an update, translate only the changed semantic units and preserve reviewed wording elsewhere.
5. Keep headings, lists, tables, code fences, inline code, links, anchors, and terminology aligned according to repository rules.
6. Update hashes, manifests, switchers, or sidecars only after semantic equivalence is confirmed.
7. Run scoped pair validation, then the repository-wide localization or documentation check when required.

Read `references/pairing-workflow.md` for update and new-pair procedures.

## Non-Negotiable Rules

- Never silently choose one side as authoritative when both changed.
- Never retranslate a complete document to apply a small update unless alignment is impossible and the user approves the broader rewrite.
- Do not invent terminology when the repository has a glossary or established precedent.
- Keep code blocks byte-identical when repository policy requires it.
- Do not bulk re-record pair metadata for files not semantically reviewed.

## Output

Report pairs updated, authored side for each change, whether the edit was minimal or whole-document, terminology decisions needing review, metadata regenerated, and checks run.
