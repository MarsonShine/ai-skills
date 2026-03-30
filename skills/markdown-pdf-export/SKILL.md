---
name: markdown-pdf-export
description: "Export Markdown files to polished, print-ready PDFs and set up reusable local export scripts. Use this skill whenever the user wants Markdown converted to PDF, asks for one-click export automation, needs reusable styling presets, or wants to tune margins, fonts, images, or page layout for resumes, reports, manuals, proposals, or summaries. Default to a script-based workflow instead of a one-off manual conversion."
compatibility: "Works best on Windows with PowerShell, Pandoc, and Microsoft Edge or Chrome. The bundled script uses Pandoc to build embedded HTML and a headless browser to print stable PDFs."
---

# Markdown PDF Export

Use this skill to turn markdown deliverables into repeatable PDF outputs. The default recommendation is not a one-time command; it is a reusable local export setup that the user can run again after editing the markdown.

## Default operating mode

- Prefer a reusable script and config file over ad-hoc shell commands.
- On Windows, use the stable stack:
  1. Pandoc converts markdown to standalone HTML with embedded resources
  2. Edge or Chrome headless prints that HTML to PDF
- Write PDFs next to the source files unless the user specifies a different output location.
- Verify that the generated PDFs exist after export.

## Preset selection

Choose the preset automatically unless the user clearly wants something else:

- `resume` - recommended for resumes, CVs, bios, profile sheets, and portfolio summaries
- `compact` - recommended for one-page handouts, summaries, cheat sheets, and condensed versions
- `default` - recommended for general reports, instructions, proposals, and notes

Read `references/preset-selection.md` if you need to justify or refine the preset choice.

## Preferred workflow

1. Identify the markdown source files and expected PDF filenames.
2. If the user wants repeatability, copy the bundled script and wrapper into the target workspace:
   - `scripts/export_markdown_pdf.ps1`
   - `scripts/export_markdown_pdf.cmd`
   - one or more CSS presets from `assets/`
   - `assets/export-config.example.json` adapted into a project-local config file
3. Populate the config with document entries, titles, and presets.
4. Run the script from the target workspace.
5. Verify the PDF outputs and keep the setup in place for future reruns.

If the user only wants a one-time export, you may run the script directly without copying it, but the default recommendation is still to leave a reusable setup behind.

## Config model

The bundled script expects a JSON config file with this shape:

```json
{
  "defaults": {
    "workDir": ".",
    "resourcePath": ".",
    "preset": "default",
    "virtualTimeBudget": 5000
  },
  "documents": [
    {
      "input": "document.md",
      "output": "document.pdf",
      "title": "Document Title",
      "preset": "default"
    }
  ]
}
```

Use:

- `preset` for the built-in CSS options
- `css` only when the user explicitly wants a custom stylesheet
- `resourcePath` when images or local assets are referenced outside the markdown's own directory

## Styling rules

- Keep styles simple, print-safe, and easy to maintain.
- Favor readable fonts, restrained color, predictable spacing, and page-break-safe images.
- For resumes, emphasize headings, contact blocks, and compact bullet spacing.
- For compact documents, reduce margins and vertical spacing without making the output feel cramped.

## Verification rules

After export:

- Confirm the PDF file paths exist.
- Confirm the file sizes are non-zero.
- When feasible, extract a small text sample from the PDF to confirm the content is not an error page.

## Resources in this skill

- `scripts/export_markdown_pdf.ps1` - generic reusable export script
- `scripts/export_markdown_pdf.cmd` - Windows wrapper for the PowerShell script
- `assets/default.css` - balanced general-purpose print style
- `assets/compact.css` - tighter layout for short documents
- `assets/resume.css` - polished resume-oriented style
- `assets/export-config.example.json` - starter config file
- `references/preset-selection.md` - when to use each preset and what to tweak
