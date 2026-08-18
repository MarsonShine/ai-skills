# Documentation Projection Checklist

## Source Ownership

- Confirm which file is canonical and which files are generated or copied.
- Check whether generated catalogs must be changed through source metadata or a generator.
- Preserve repository-relative links in canonical Markdown when the projector owns route rewriting.

## Page Mapping

Read the current type or schema instead of remembering fields. Common concerns include:

- canonical source path;
- public route and aliases;
- navigation label, section, and stable order;
- locale and fallback behavior;
- source aliases used only for link resolution;
- draft, private, or internal pages that must remain unpublished.

Do not add internal documents merely because they exist under a documentation directory.

## Links and Assets

- Distinguish mapped site pages, repository-source links, external URLs, fragments, and images.
- Verify cross-page heading fragments in the built site; renderer slug rules may differ from repository hosts.
- Keep images inside allowed roots and confirm whether the pipeline copies or serves them directly.
- Use redirects or aliases for intentional moves; do not leave silent broken routes.

## Locales

- Discover whether locales use sibling files, locale directories, generated translations, or a manifest.
- Keep source layout separate from public route layout when the pipeline does so.
- Use `../sync-bilingual-docs/SKILL.md` only when the user explicitly requests synchronization of an existing bilingual pair.

## Validation Evidence

Prefer a focused projector check, broken-link and fragment scan, framework production build, and visual route preview. Restart the dev server when configuration changes are not hot-reloaded.
