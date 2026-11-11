# Install State

Checked: 2026-11-11
Source: `afb1f6c` with the working-tree WeChat draft assistant
Plugin version: `0.2.0+codex.20261111103201`

This file records where installed copies came from and how far they have drifted. It is not an install log for every tool.

## Codex

Reinstalled `ai-skills@ai-skills` on 2026-11-11 with the local marketplace installer. A command-scoped source override selected a clean snapshot of the repository plus the WeChat assistant, excluding a separate in-progress WorkBuddy directory. The configured marketplace continues to point to this repository.

- Installed cache: `%USERPROFILE%\.codex\plugins\cache\ai-skills\ai-skills\0.2.0+codex.20261111103201`.
- Includes 26 skills. SHA-256 checks matched all 125 skill files and the plugin manifest against the installation snapshot.
- The WeChat assistant passed local preview and draft recovery checks. Account and phone acceptance remain pending. See the [draft assistant acceptance record](../workspaces/wechat-mp-publisher/README.md) and [earlier session-closeout evidence](../workspaces/session-closeout/README.md).
- Open a new Codex chat to load the updated skill catalog.
- The source adds a first-time setup guide and optional centered QR footer support to `wechat-mp-publisher`. These changes are not in the installed cache above; reinstall the plugin to load them in a future session.
- This source repository has not adopted the managed block; no adoption was performed.

## DeepSeek Harness Installed Target

DeepSeek Harness loads user skills from `%USERPROFILE%\.dsh\skills`. Other hosts may use the plugin entry, junctions, or their own skill directory.

## Harness Kit

Installed 2026-10-21 from the `bootstrap-harness` templates and script at `main` `01e10ac`:

- Engine: `%USERPROFILE%\.agents\harness\` (`harness.py` plus `templates/`).
- Skill: a junction at `%USERPROFILE%\.dsh\skills\bootstrap-harness` pointing to this repository.
- Global triggers: `~/.dsh/AGENTS.md`, `~/.codex/AGENTS.md`, and `~/.claude/CLAUDE.md`. They only detect a missing block and propose `init` or `adopt`; they do not contain the rule body.
- First adopter: `MS.Microservice`, baseline v1.

Update the engine by copying the current skill files again; the templates are the source of truth.

The closeout update adds `closeout.py` next to the standalone `harness.py` and refreshes the status/active templates. The managed-block baseline remains v1; project-owned non-empty documents are migrated explicitly, not overwritten by sync.

## DeepSeek Harness Drift (Historical Check)

Last checked 2026-10-21, before the current closeout and packaging changes. At that check, 18 of 25 `SKILL.md` files matched the repository byte for byte and the remaining 7 were older copies. This table is not a fresh comparison against the current source:

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
