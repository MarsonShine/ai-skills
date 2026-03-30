# Preset Selection Guide

Use this guide when choosing a PDF export preset.

## `resume`

Best for:

- resumes and CVs
- one-person professional profiles
- consultant bios
- capability statements

Characteristics:

- stronger visual hierarchy
- refined heading spacing
- compact bullets
- quote/contact blocks styled to read cleanly in print

Typical tweaks:

- keep images modest in size
- avoid long tables
- prioritize section scanning over dense prose

## `compact`

Best for:

- one-page summaries
- handouts
- cheat sheets
- condensed versions of longer documents

Characteristics:

- tighter margins
- smaller base font
- reduced spacing
- more content per page

Typical tweaks:

- shorten headings
- trim repeated explanatory text
- keep bullet lists short and decisive

## `default`

Best for:

- reports
- proposals
- meeting notes
- instructions
- lightweight documentation

Characteristics:

- balanced whitespace
- comfortable reading rhythm
- conservative print styling

Typical tweaks:

- increase image width only when diagrams need detail
- consider custom CSS only for strongly branded documents

## Selection heuristic

If unsure:

1. Resume or profile document -> `resume`
2. User explicitly wants a condensed or one-page PDF -> `compact`
3. Everything else -> `default`
