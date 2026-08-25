---
name: sync-documentation-site
description: Synchronize canonical repository Markdown with a generated or framework-backed documentation site. Use for VitePress, Docusaurus, MkDocs, or custom site projections involving pages, navigation, routes, links, moves, or removals. Do not use for ordinary documentation editing, translation, deployment, or hosting changes.
---

# Synchronize a Documentation Site

Treat canonical repository documents as the editable source and the site as a projection unless the target repository explicitly says otherwise.

## Discover the Pipeline First

1. Read repository and documentation instructions.
2. Locate the site framework, content roots, page manifest or discovery rules, navigation configuration, generated directories, and validation commands.
3. Determine whether pages are copied, transformed, generated, localized, or authored directly in the site tree.
4. Identify directories that are disposable build output and must never be edited or committed.

Read `references/projection-checklist.md` before changing a custom manifest, locale route, or link-rewriting pipeline.

## Classify the Change

- Edit an existing published page at its canonical source.
- Add a page to the owning content tier, then update only the mapping or navigation required by the current framework.
- Move or remove a page atomically with its mappings, navigation entries, aliases, redirects, and inbound links.
- Change a generated page at its generator or source data, then regenerate it.
- Change framework configuration only when the existing content model cannot express the request.

## Validate

Run the repository's focused projection or docs check, link and fragment validation, site build, and diff checks. Preview the affected routes when the change is visible or navigation-sensitive.

Report canonical files changed, public routes affected, generated files intentionally left untouched, and exact checks run.

## Boundary

Content synchronization does not authorize deployment, DNS changes, public hosting, analytics, or CI permission changes. Stop after a verified local build unless the user explicitly asks to publish.
