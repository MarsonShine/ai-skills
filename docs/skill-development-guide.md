# Skill Development And Maintenance Guide

This repository is both the source of truth for skills and a local Codex plugin. Keep skills here, validate them here, and install the repository through the marketplace configuration instead of copying skills into user profile folders by hand.

## Repository Layout

```text
ai-skills/
  .codex-plugin/plugin.json
  .agents/plugins/marketplace.json
  skills/
    skill-name/
      SKILL.md
      references/
      scripts/
      assets/
  docs/
```

- `.codex-plugin/plugin.json` makes the repository a Codex plugin and exposes `./skills/`.
- `.agents/plugins/marketplace.json` makes the repository installable as a local marketplace entry.
- `skills/` is the only source-of-truth location for maintained skills.

## Creating Or Updating A Skill

1. Create or edit a folder under `skills/<skill-name>/`.
2. Keep discovery descriptions concise and discriminating. Keep `SKILL.md` focused on the trigger, useful first action, conditional resource routing, output contract, and essential constraints.
3. Move long examples, policies, matrices, and checklists to `references/`.
4. Move deterministic repeated work to `scripts/`.
5. Put reusable templates, images, fonts, or static examples in `assets/`.
6. Avoid absolute paths. Prefer paths relative to the current skill folder or repository root.
7. Run validation before committing.

Skill names should be lowercase hyphen-case and match the folder name.

## Path Rules

- Inside a skill, refer to local resources as `references/file.md`, `scripts/tool.py`, or `assets/file.ext`.
- When one skill routes to another sibling skill, use relative paths such as `../resume-builder/SKILL.md`.
- Do not commit machine-specific absolute paths inside reusable skill instructions.
- If a tool needs user-specific configuration, document the expected environment variable or config file instead of hard-coding the path.

## Validation Checklist

Run these checks from the repository root:

```powershell
$repo = (Get-Location).Path
$codexHome = Join-Path $env:USERPROFILE ".codex"
python -X utf8 (Join-Path $codexHome "skills\.system\plugin-creator\scripts\validate_plugin.py") $repo
python -X utf8 (Join-Path $codexHome "skills\.system\skill-creator\scripts\quick_validate.py") (Join-Path $repo "skills\<skill-name>")
$absolutePathPattern = @('C:' + '\\Users', '[A-Z]:' + '\\', '/' + 'Users/', '/' + 'home/') -join '|'
rg -n $absolutePathPattern skills docs .codex-plugin .agents AGENTS.md .github
```

For changed scripts or invocation contracts, run a representative safe command with a small local fixture. Instruction-only edits need structural and relevant behavioral checks, not every media/API workflow. After description changes, use `workspaces/skill-routing-evals/` to check discovery boundaries; distinguish manual contract review from fresh model runs. Reuse valid passing checks.

## Local Marketplace Workflow

This repository can be installed as a local marketplace:

```powershell
codex plugin marketplace add .
codex plugin add ai-skills@ai-skills
```

After changing skills, update the plugin version cachebuster before reinstalling:

```powershell
$repo = (Get-Location).Path
$codexHome = Join-Path $env:USERPROFILE ".codex"
python (Join-Path $codexHome "skills\.system\plugin-creator\scripts\update_plugin_cachebuster.py") $repo
codex plugin add ai-skills@ai-skills
```

Start a new Codex thread after reinstalling so the updated skills are loaded into the model context.

## Maintenance Notes

- Treat `skills/` as source code. Review diffs before committing.
- Keep generated caches, temporary outputs, and evaluation workspaces out of normal skill folders unless they are intentional fixtures.
- Update `.codex-plugin/plugin.json` when the plugin description, version, prompt examples, or visible capability set changes.
- Update routing indexes when adding, renaming, or removing skills.
- Do not duplicate the same skill in `.codex/skills` and this repository as two independent sources. Install from this plugin instead.
- Prefer small, composable skills over one large all-purpose skill.
