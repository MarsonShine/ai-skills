# AI Skills

Reusable agent skills for Codex, Claude Code, GitHub Copilot, and other tools that understand the Agent Skills layout.

This repository is the source of truth. Do not maintain separate long-lived copies under `.codex`, `.copilot`, or `.claude`; install from this repository with a plugin entry, symlinks/junctions, or the GitHub skill workflow.

## What's Inside

```text
ai-skills/
  .codex-plugin/plugin.json        # Codex plugin manifest
  .agents/plugins/marketplace.json # Local Codex marketplace entry
  .github/copilot-instructions.md  # Repo-level Copilot guidance
  AGENTS.md                        # Canonical repo maintenance rules
  docs/skill-development-guide.md  # Development and maintenance guide
  skills/                          # Installable skills
  workspaces/                      # Eval/output workspaces, not installable skills
```

Current skills:

- `business-solution-architect`
- `csharp-dotnet-code-checklist`
- `fact-check-debunker`
- `id-photo-maker`
- `loop-orchestrator`
- `markdown-pdf-export`
- `photo-selector`
- `qwen-image-generator`
- `resume-builder`
- `translate-tech-en-zh`

## Install For Codex

This repository is already packaged as a local Codex plugin. From the repository root:

```powershell
codex plugin marketplace add .
codex plugin add ai-skills@ai-skills
```

After editing skills, update the plugin cachebuster and reinstall:

```powershell
$repo = (Get-Location).Path
$codexHome = Join-Path $env:USERPROFILE ".codex"
python (Join-Path $codexHome "skills\.system\plugin-creator\scripts\update_plugin_cachebuster.py") $repo
codex plugin add ai-skills@ai-skills
```

Start a new Codex thread after reinstalling so the updated skill metadata is loaded.

## Install For Claude Code

Claude Code loads custom skills from personal, project, and plugin locations. For a personal install that stays linked to this repository, create directory junctions on Windows:

```powershell
$repo = (Resolve-Path .).Path
$dest = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Get-ChildItem (Join-Path $repo "skills") -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
  ForEach-Object {
    $link = Join-Path $dest $_.Name
    if (Test-Path $link) { Remove-Item -Recurse -Force $link }
    New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
  }
```

On macOS/Linux:

```bash
mkdir -p ~/.claude/skills
for d in skills/*; do
  [ -f "$d/SKILL.md" ] && ln -sfn "$(pwd)/$d" "$HOME/.claude/skills/$(basename "$d")"
done
```

You can also install a single skill into a project by linking it to `.claude/skills/<skill-name>`.

If you publish the repository as GitHub skills, Claude Code can also use GitHub CLI:

```bash
gh skill install MarsonShine/ai-skills loop-orchestrator --agent claude-code --scope user
```

## Install For GitHub Copilot

Copilot can use repository custom instructions and agent skills.

This repo already includes `.github/copilot-instructions.md` for repository-level guidance.

For personal skills that stay linked to this repository on Windows:

```powershell
$repo = (Resolve-Path .).Path
$dest = Join-Path $env:USERPROFILE ".copilot\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Get-ChildItem (Join-Path $repo "skills") -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
  ForEach-Object {
    $link = Join-Path $dest $_.Name
    if (Test-Path $link) { Remove-Item -Recurse -Force $link }
    New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
  }
```

For project-scoped Copilot skills, link or copy selected skills into another repository's `.github/skills/` directory:

```powershell
$source = Resolve-Path ".\skills\loop-orchestrator"
$project = "<path-to-project>"
$dest = Join-Path $project ".github\skills\loop-orchestrator"
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
New-Item -ItemType Junction -Path $dest -Target $source | Out-Null
```

After publishing GitHub skills, users can install with GitHub CLI:

```bash
gh skill install MarsonShine/ai-skills loop-orchestrator
```

## Install For Other Agent-Skills Tools

Many tools support the same basic shape: each skill is a folder containing `SKILL.md` plus optional `references/`, `scripts/`, and `assets/`.

Use one of these patterns:

- Personal install: link selected folders from `skills/` into the tool's personal skills directory.
- Project install: link selected folders into the project's skills directory, such as `.agents/skills/`.
- Direct use: point the tool at this repository and configure it to scan `skills/`.

Generic Windows personal install:

```powershell
$repo = (Resolve-Path .).Path
$dest = Join-Path $env:USERPROFILE ".agents\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Get-ChildItem (Join-Path $repo "skills") -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
  ForEach-Object {
    $link = Join-Path $dest $_.Name
    if (Test-Path $link) { Remove-Item -Recurse -Force $link }
    New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
  }
```

Generic macOS/Linux personal install:

```bash
mkdir -p ~/.agents/skills
for d in skills/*; do
  [ -f "$d/SKILL.md" ] && ln -sfn "$(pwd)/$d" "$HOME/.agents/skills/$(basename "$d")"
done
```

## Publish And Validate

Validate the Codex plugin:

```powershell
$repo = (Get-Location).Path
$codexHome = Join-Path $env:USERPROFILE ".codex"
python (Join-Path $codexHome "skills\.system\plugin-creator\scripts\validate_plugin.py") $repo
```

Validate every skill:

```powershell
$env:PYTHONUTF8 = "1"
$repo = (Get-Location).Path
$codexHome = Join-Path $env:USERPROFILE ".codex"
$validator = Join-Path $codexHome "skills\.system\skill-creator\scripts\quick_validate.py"

Get-ChildItem (Join-Path $repo "skills") -Directory |
  ForEach-Object { python $validator $_.FullName }
```

Check for machine-specific absolute paths:

```powershell
$absolutePathPattern = @('C:' + '\Users', '[A-Z]:' + '\', '/' + 'Users/', '/' + 'home/') -join '|'
rg -n $absolutePathPattern skills docs .codex-plugin .agents AGENTS.md .github README.md
```

For GitHub skills publishing:

```bash
gh skill publish --dry-run
gh skill publish --fix
gh skill publish
```

Use `--dry-run` before publishing. Use `--fix` only after reviewing the resulting diff.

## Maintenance Workflow

1. Add or edit a skill under `skills/<skill-name>/`.
2. Keep `SKILL.md` small and move long guidance into `references/`.
3. Use relative paths inside skills. Do not hard-code user profile or drive paths.
4. Keep eval outputs and experiments under `workspaces/`, not directly under `skills/`.
5. Validate the plugin and skills.
6. Commit the change.
7. Reinstall or republish for the target tool.

See [docs/skill-development-guide.md](docs/skill-development-guide.md) for the detailed development rules.

## References

- [Claude Code skills documentation](https://code.claude.com/docs/en/skills)
- [GitHub Copilot agent skills documentation](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [GitHub Copilot repository custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
