---
name: resume-builder
description: "Create, rewrite, tailor, translate, or condense a professional resume/CV from work history and job requirements. Not for biographies, portfolio sites, or unrelated document editing."
---

# Resume Builder

Produce an application-ready resume from the user's materials. Improve emphasis and wording while keeping every claim supported.

## Workflow

1. Inspect the supplied resume, notes, job description, and relevant source files. Search nearby files only when needed to locate the requested materials. Use `scripts/extract_pdf_text.py` for PDF source text.
2. Establish the target role, language, length, and deliverable from the request and evidence. Continue with a reasonable draft when routine choices are unspecified; ask only for facts or choices that materially change it.
3. Select `assets/resume-detailed-template.md` or `assets/resume-compact-template.md` when a starting structure helps. Adapt sections to the target role and available evidence. Produce additional variants only when requested.
4. Write experience bullets around supported scope, action, and result. Read `references/industry-playbook.md` for unfamiliar industry vocabulary, and `references/quantification-guide.md` when using or calculating metrics.
5. Check the draft against sources, remove unsupported claims, and write the requested file. Default to Markdown when no format is specified; for a requested PDF, use `../markdown-pdf-export/SKILL.md` when available or an available document exporter.

## Evidence Boundaries

- Do not invent employers, dates, qualifications, responsibilities, achievements, or figures. A plausible range or qualitative improvement is still a factual claim and needs evidence. Job titles and industry norms do not establish personal performance.
- Use supplied figures or calculations from supplied data; preserve units, time periods, and whether values are estimates. With no metric evidence, describe supported responsibilities and deliverables without a number. Missing metrics need not block a useful draft.
- Filenames, timestamps, and work photos can help locate or understand material but do not prove the person's role, team size, leadership, certification, or performance. Do not infer sensitive personal data or regulated qualifications from appearance.
- Include supplied work photos only when requested or when the chosen portfolio format calls for evidence images. Keep ID cards, customer data, and unrelated personal images out of the deliverable.
- Preserve an existing file when the user requests a sibling version; use a clear output name when none is provided.

## Output

Deliver the resume file, briefly identify material missing facts, and report any export limitation. Keep the resume itself free of drafting commentary; place unresolved questions outside the finished artifact.
