---
name: markdown-pdf-export
description: "Export Markdown to a polished, print-ready PDF or configure a reusable local Markdown-to-PDF workflow. Use for Markdown 转 PDF, export styling, margins, fonts, images, or page layout. Do not use for editing existing PDFs, converting non-Markdown source files, or general document writing."
---

# Markdown PDF Export

Use this skill to turn markdown deliverables into repeatable PDF outputs. Default to leaving behind a reusable script + config setup instead of a one-off command.

## Compatibility

Works best on Windows with PowerShell, Node.js 22+, Pandoc, and Microsoft Edge or Chrome. The PowerShell wrapper stays thin; `scripts/export_markdown_pdf.ts` validates config, runs Pandoc, and prints stable PDFs through a headless browser.

## Runtime layout

| File | Role |
| --- | --- |
| `scripts/export_markdown_pdf.ps1` | Windows entrypoint |
| `scripts/export_markdown_pdf.cmd` | double-clickable wrapper |
| `scripts/export_markdown_pdf.ts` | config validation, Pandoc HTML build, browser PDF print |
| `assets/*.css` | built-in print presets |
| `assets/export-config.example.json` | starter config |
| `references/preset-selection.md` | preset selection rules |

## Default workflow

1. Identify the markdown source files and target PDF names.
2. Choose a preset:
   - `resume` for resumes and profile sheets
   - `compact` for one-page handouts or summaries
   - `default` for general reports and notes
3. If the user wants repeatability, copy the script, wrapper, CSS preset, and example config into the workspace.
4. Fill the config and run `scripts/export_markdown_pdf.ps1`.
5. Verify the PDF exists and is non-empty.

## Config shape

Use `assets/export-config.example.json` as the template.

Supported document fields:

- `input`
- `output`
- `title`
- `preset`
- `css`
- `resourcePath`
- `virtualTimeBudget`

Use `preset` for built-in styles. Use `css` only when the user explicitly wants a custom stylesheet.

## Output rules

- Prefer PDFs next to the source files unless the user asked for another location.
- Keep styles print-safe and boring.
- Surface Pandoc, browser, or missing-file errors directly.
