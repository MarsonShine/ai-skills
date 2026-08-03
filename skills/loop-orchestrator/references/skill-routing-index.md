# Skill Routing Index

This index maps sibling skills in this repository to the kinds of requests that should reuse them. When a task matches an entry, read that skill's `SKILL.md` before acting and treat it as supplementary guidance.

Paths are relative to `skills/loop-orchestrator/` so they continue to work when the repository is installed as a Codex plugin.

Do not copy, edit, or migrate skills during routing unless the user explicitly asks. This index is only a routing aid.

| Skill | Relative path | Use for |
| --- | --- | --- |
| `business-solution-architect` | `../business-solution-architect/SKILL.md` | Turning rough business requirements, PRDs, architecture ideas, data models, state flows, and API needs into implementation-ready Chinese solution blueprints. |
| `csharp-dotnet-code-checklist` | `../csharp-dotnet-code-checklist/SKILL.md` | C#, ASP.NET Core, .NET, EF Core, DI, async, security, performance, observability, tests, PR review, diff review, and checklist-based architecture review. |
| `fact-check-debunker` | `../fact-check-debunker/SKILL.md` | Fact-checking claims, debunking misleading content, validating sources, and separating evidence from speculation. |
| `id-photo-maker` | `../id-photo-maker/SKILL.md` | ID photos, passport-style headshots, local photo processing, print sheets, background handling, and related image workflows. |
| `markdown-pdf-export` | `../markdown-pdf-export/SKILL.md` | Exporting Markdown to polished PDFs, one-click PDF export automation, styling presets, margins, fonts, images, page layout, resumes, reports, manuals, proposals, and summaries. |
| `photo-selector` | `../photo-selector/SKILL.md` | Selecting the best photos from a batch, contact sheets, visual comparison, ranking, and image curation workflows. |
| `qwen-image-generator` | `../qwen-image-generator/SKILL.md` | Generating images with DashScope Qwen-Image, including illustrations, posters, flashcards, covers, mascots, product concepts, and vague image requests. |
| `resume-builder` | `../resume-builder/SKILL.md` | Creating, improving, quantifying, tailoring, condensing, localizing, or polishing resumes and CVs from rough notes, PDFs, job histories, evidence files, or job postings. |
| `translate-tech-en-zh` | `../translate-tech-en-zh/SKILL.md` | Technical English-Chinese translation, localization, terminology consistency, and developer-facing article translation. |
| `windows-reclaim-disk-space` | `../windows-reclaim-disk-space/SKILL.md` | Auditing Windows system-drive usage, ranking reclaimable space, producing safe/conditional/do-not-delete reports, and executing explicitly approved cache cleanup with strict safety checks. |

## Routing Rules

- Prefer the most specific matching skill.
- If multiple skills match, use `loop-orchestrator` to define the loop and use the domain skill for task-specific quality rules.
- If no skill matches, proceed with the loop contract and normal repository/context exploration.
- If a matching skill requires tools, credentials, or network access that are unavailable, state the limitation and continue with the closest feasible workflow.
