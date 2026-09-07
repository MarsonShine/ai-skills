---
name: markdown-pdf-export
description: "Export Markdown to print-ready PDF, adjust export layout, or configure a reusable local export workflow. Not for editing PDFs or converting other source formats."
---

# Markdown PDF Export

Export the requested Markdown to PDF using the bundled exporter. Copy a reusable script/config setup into the workspace only when the user requests that deliverable.

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
5. Verify the PDF opens, then render or preview the affected pages to check clipping, page breaks, fonts, and images. A non-empty file alone does not prove a usable export; report when visual inspection is unavailable.

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

Use `preset` for built-in styles. Use `css` when a preset cannot express the requested layout; choosing a stylesheet for an authorized formatting change needs no separate confirmation.

## Output rules

- Prefer PDFs next to the source files unless the user asked for another location.
- Keep styles print-safe and boring.
- Surface Pandoc, browser, or missing-file errors directly.
