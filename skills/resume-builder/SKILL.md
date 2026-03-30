---
name: resume-builder
description: "Build or rewrite professional resumes and CVs from scattered materials, existing resumes, PDFs, job histories, work photos, certificates, or target job postings. Use this skill whenever the user asks to create, improve, quantify, tailor, condense, localize, or polish any resume or CV, even if they only provide rough notes or evidence files. Default to producing truthful, well-structured markdown resumes and a concise version when that would help the user apply faster."
compatibility: "Works best with file viewing/search tools and PowerShell so you can inspect source files, extract PDF text, and create final markdown deliverables in the working directory."
---

# Resume Builder

Turn incomplete source material into a strong, believable, application-ready resume. Default to doing the work end-to-end: inspect files, infer the user's target role, enrich details carefully, quantify achievements conservatively, and write polished markdown output instead of stopping at advice.

## Default operating mode

- Prefer execution over consultation. If the user gives materials and a target file, produce the file.
- Preserve truth. Upgrade wording and structure, but do not invent employers, dates, degrees, certificates, or exact figures that have no basis.
- Use evidence aggressively. Mine existing resumes, PDFs, photos, job descriptions, filenames, and surrounding project files for clues.
- If the user does not want the current resume overwritten, keep the current file untouched and create sibling outputs such as `_compact`, `_tailored`, `_english`, or `_final`.
- Match the user's language. If the materials are mostly Chinese-language materials, write in Chinese unless explicitly asked otherwise.

## Workflow decision tree

1. Classify the request:
   - **Create from scratch** from notes, files, or evidence
   - **Rewrite or enrich** an existing resume
   - **Tailor** a resume to a target role or company
   - **Compress** into a concise or one-page version

2. Gather evidence before writing:
   - Search the current working directory for obvious resume materials: `.md`, `.txt`, `.pdf`, image files, job descriptions, certificates, or project notes.
   - If a PDF contains the source resume, extract text with `scripts/extract_pdf_text.py`.
   - Inspect work photos when they help establish job scope, equipment familiarity, team leadership, project environment, or service context.

3. Infer the professional context:
   - Identify the likely industry, target title, seniority, and proof points.
   - Read `references/industry-playbook.md` when the role is outside generic office work or when you need better domain vocabulary.

4. Draft the strongest truthful version:
   - Use the detailed template for the primary resume unless the user explicitly wants only a concise version.
   - Create a concise version as well when the user asks for one, when the source is too long, or when a frontline/service role would benefit from a fast-scanning version.

5. Quantify impact carefully:
   - Read `references/quantification-guide.md`.
   - Prefer conservative ranges, stable performance bands, or cycle-time improvements over fake precision.

6. Finalize:
   - Ensure the final markdown is clean, structured, and ready for export.
   - If the user also wants a PDF, keep the markdown export-ready and then use the `markdown-pdf-export` skill.

## Evidence collection rules

- Read enough context before editing so the final resume does not contradict the source materials.
- Treat filenames, timestamps, and visual cues as supporting evidence, not as permission to invent unsupported facts.
- For work photos, infer only what is visibly defensible:
  - team coordination or morning briefings
  - equipment operation
  - field environment
  - layout, dispatch, inspection, or onsite management
- Do not infer sensitive personal data, licenses, or regulated qualifications from appearance alone.

## Resume writing rules

### Default structure for a detailed resume

Use this structure unless the user's target format clearly requires a different one:

1. Name and contact block
2. Target role / objective
3. Professional summary
4. Core strengths
5. Work experience
6. Selected achievements or representative highlights
7. Professional skills
8. Education / certificates / training if available
9. Optional evidence section such as work photos or project snapshots

### Default structure for a concise resume

Use this structure for fast-scanning delivery:

1. Name and contact block
2. One short positioning summary
3. Four to six core strengths
4. Condensed work history
5. Key quantified wins

### Bullet-writing standard

For each bullet, aim for:

- **Scope**: what area, team, project, customer group, or asset base was involved
- **Action**: what the user actually organized, improved, delivered, or operated
- **Result**: what became faster, better, cleaner, safer, cheaper, more stable, or more compliant

Prefer strong, specific verbs:

- Led, coordinated, scheduled, maintained, trained, inspected, optimized, standardized, reduced, improved, delivered, supported, handled

## Quantification rules

- Only quantify what can be reasonably inferred from the role, files, or visible evidence.
- Prefer ranges and soft qualifiers such as `about`, `nearly`, `stable at`, `20-30 people`, `97%-98%`, or `within 24 hours`.
- Good categories to quantify:
  - team size
  - service coverage
  - pass rate or quality score
  - complaint response and closure
  - cost or material savings
  - onboarding speed
  - on-time rate
  - output volume
  - defect or error reduction
- Avoid false precision such as `97.43%` unless the exact figure exists in the source.

## Photos and supporting evidence

Default recommendation:

- **Frontline, operations, service, property, logistics, construction, hospitality, or manufacturing roles**: include one to four strong work photos when they increase credibility.
- **Corporate, finance, legal, HR, or knowledge-worker resumes**: omit photos unless they function as portfolio or project evidence.

When including images:

- Add a small section such as `Work Scenes`, `Project Site`, or `Representative Work Scenes`.
- Use concise captions that support the resume story.
- Never expose ID cards, private customer data, or irrelevant personal images.

## Output expectations

- Write the actual resume file(s), not just suggestions, when a target path or filename is available.
- Keep markdown readable and export-friendly:
  - clean headings
  - short paragraphs
  - compact bullet lists
  - consistent punctuation
- If the user gave no filename, create one that matches the content and keep sibling variants clearly named.

## Resources in this skill

- `references/industry-playbook.md` - how to emphasize the right strengths by industry
- `references/quantification-guide.md` - how to add credible metrics without crossing into fabrication
- `assets/resume-detailed-template.md` - reusable detailed structure
- `assets/resume-compact-template.md` - reusable concise structure
- `scripts/extract_pdf_text.py` - helper for extracting source text from PDF resumes
