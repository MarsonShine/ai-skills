# Install State

Checked: 2026-10-21
Source: `main` at `27e44f9` with the local plugin cachebuster update
Plugin version: `0.2.0+codex.20261021175202`

This file records where installed copies came from and how far they have drifted. It is not an install log for every tool.

## Codex

Reinstalled `ai-skills@ai-skills` on 2026-10-21 from this repository's local marketplace using `codex plugin add ai-skills@ai-skills --json`.

- Installed cache: `%USERPROFILE%\.codex\plugins\cache\ai-skills\ai-skills\0.2.0+codex.20261021175202`.
- Includes 25 skills, including the new `bootstrap-harness` skill.
- Updated entrypoints since the previous Codex cache: `implement-minimal-code`, `markdown-pdf-export`, `review-technical-prose`, and `write-natural-prose`.
- All 25 skill entrypoints passed quick validation, and the repository skill catalog check passed.
- SHA-256 comparison confirmed all 3,057 installed skill files match the repository, with no missing or extra files; the plugin manifest also matches byte for byte.
- Restart Codex and open a new chat to load the updated plugin into the model context.
- Repository harness adoption was declined for this update; `AGENTS.md` was not changed.

## DeepSeek Harness Installed Target

DeepSeek Harness loads user skills from `%USERPROFILE%\.dsh\skills`. Other hosts may use the plugin entry, junctions, or their own skill directory.

## Harness Kit

Installed 2026-10-21 from the `bootstrap-harness` templates and script at `main` `01e10ac`:

- Engine: `%USERPROFILE%\.agents\harness\` (`harness.py` plus `templates/`).
- Skill: a junction at `%USERPROFILE%\.dsh\skills\bootstrap-harness` pointing to this repository.
- Global triggers: `~/.dsh/AGENTS.md`, `~/.codex/AGENTS.md`, and `~/.claude/CLAUDE.md`. They only detect a missing block and propose `init` or `adopt`; they do not contain the rule body.
- First adopter: `MS.Microservice`, baseline v1.

Update the engine by copying the current skill files again; the templates are the source of truth.

## DeepSeek Harness Drift

18 of 25 `SKILL.md` files match this repository byte for byte. The remaining 7 are older installed copies:

| Skill | Repository (chars) | Installed (chars) |
| --- | ---: | ---: |
| `business-solution-architect` | 1061 | 983 |
| `implement-minimal-code` | 5005 | 3556 |
| `review-code-change` | 2344 | 2190 |
| `review-technical-prose` | 2526 | 1978 |
| `reviewable-change-slices` | 4483 | 4411 |
| `run-pre-push-checks` | 1994 | 1781 |
| `write-natural-prose` | 5800 | 4165 |

The installed copies match the state recorded after the 2026-09-03 reinstall. The 2026-10-13 skill changes were committed but never installed, so the runtime executes older instructions.

## DeepSeek Harness Update

From an unrestricted shell, with a fresh agent session afterward:

```powershell
# Run from the repository root.
$repo = (Get-Location).Path
$dest = Join-Path $env:USERPROFILE ".dsh\skills"

Get-ChildItem (Join-Path $repo "skills") -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
  ForEach-Object {
    $link = Join-Path $dest $_.Name
    if (Test-Path $link) { Remove-Item -Recurse -Force $link }
    New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
  }
```

Do not edit installed copies directly. Re-run this check after changing skills, and update the table above when the drift changes.
