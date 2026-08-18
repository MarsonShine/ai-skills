# Skill Routing Index

This index maps sibling skills in this repository to the kinds of requests that should reuse them. When a task matches an entry, read that skill's `SKILL.md` before acting and treat it as supplementary guidance.

Paths are relative to `skills/loop-orchestrator/` so they continue to work when the repository is installed as a Codex plugin.

Do not copy, edit, or migrate skills during routing unless the user explicitly asks. This index is only a routing aid.

| Skill | Relative path | Use for |
| --- | --- | --- |
| `business-solution-architect` | `../business-solution-architect/SKILL.md` | Turning rough business requirements, PRDs, architecture ideas, data models, state flows, and API needs into implementation-ready Chinese solution blueprints. |
| `csharp-dotnet-code-checklist` | `../csharp-dotnet-code-checklist/SKILL.md` | C#, ASP.NET Core, .NET, EF Core, DI, async, security, performance, observability, tests, PR review, diff review, and checklist-based architecture review. |
| `fact-check-debunker` | `../fact-check-debunker/SKILL.md` | Fact-checking claims, debunking misleading content, validating sources, and separating evidence from speculation. |
| `find-code-simplifications` | `../find-code-simplifications/SKILL.md` | Evidence-backed audits for dead, duplicated, speculative, over-built, or replaceable code and API surfaces. |
| `id-photo-maker` | `../id-photo-maker/SKILL.md` | ID photos, passport-style headshots, local photo processing, print sheets, background handling, and related image workflows. |
| `maintain-decision-records` | `../maintain-decision-records/SKILL.md` | Adding, auditing, consolidating, archiving, restoring, or pruning repository ADRs, RFCs, Agent Notes, and other decision records. |
| `markdown-pdf-export` | `../markdown-pdf-export/SKILL.md` | Exporting Markdown to polished PDFs, one-click PDF export automation, styling presets, margins, fonts, images, page layout, resumes, reports, manuals, proposals, and summaries. |
| `merge-stacked-prs` | `../merge-stacked-prs/SKILL.md` | Verifying and landing same-repository dependent GitHub pull requests through official stack support. |
| `photo-selector` | `../photo-selector/SKILL.md` | Selecting the best photos from a batch, contact sheets, visual comparison, ranking, and image curation workflows. |
| `qwen-image-generator` | `../qwen-image-generator/SKILL.md` | Generating images with DashScope Qwen-Image, including illustrations, posters, flashcards, covers, mascots, product concepts, and vague image requests. |
| `record-browser-gif` | `../record-browser-gif/SKILL.md` | Recording concise, verified browser workflow GIFs and, only when explicitly requested, publishing them as pull-request evidence. |
| `resume-builder` | `../resume-builder/SKILL.md` | Creating, improving, quantifying, tailoring, condensing, localizing, or polishing resumes and CVs from rough notes, PDFs, job histories, evidence files, or job postings. |
| `review-code-change` | `../review-code-change/SKILL.md` | General pull-request and diff review across languages, with evidence-focused correctness, security, lifecycle, compatibility, and test analysis. |
| `review-technical-prose` | `../review-technical-prose/SKILL.md` | Writing, reviewing, restructuring, or auditing Markdown, JSDoc, comments, prompts, diagnostics, and other technical prose. |
| `run-pre-push-checks` | `../run-pre-push-checks/SKILL.md` | Selecting and running the smallest credible local evidence set before an outgoing Git push or after rewritten branch publication. |
| `sync-bilingual-docs` | `../sync-bilingual-docs/SKILL.md` | Only explicit synchronization of both sides of an existing repository-managed bilingual document pair; never ordinary or standalone translation. |
| `sync-documentation-site` | `../sync-documentation-site/SKILL.md` | Synchronizing canonical repository docs with VitePress, Docusaurus, MkDocs, or a custom generated documentation site. |
| `translate-tech-en-zh` | `../translate-tech-en-zh/SKILL.md` | Ordinary or standalone technical English-to-Chinese text, file, article, and URL translation; not repository pair synchronization. |
| `trim-reasoning-leakage` | `../trim-reasoning-leakage/SKILL.md` | Removing private authoring-session, plan, PR, review, control-flow, and hedging residue from durable technical prose. |
| `windows-reclaim-disk-space` | `../windows-reclaim-disk-space/SKILL.md` | Auditing Windows system-drive usage, ranking reclaimable space, producing safe/conditional/do-not-delete reports, and executing explicitly approved cache cleanup with strict safety checks. |

## Routing Rules

- Prefer the most specific matching skill.
- If multiple skills match, use `loop-orchestrator` to define the loop and use the domain skill for task-specific quality rules.
- Route to `sync-bilingual-docs` only after an explicit request to synchronize an existing repository pair or an explicit `$sync-bilingual-docs` invocation. All ordinary translation stays with `translate-tech-en-zh`.
- If no skill matches, proceed with the loop contract and normal repository/context exploration.
- If a matching skill requires tools, credentials, or network access that are unavailable, state the limitation and continue with the closest feasible workflow.
