# Install State

Checked: 2026-10-19
Source: `main` at `a9e08e4`
Plugin version: `0.2.0+codex.20261013120707`

This file records where installed copies came from and how far they have drifted. It is not an install log for every tool.

## Installed Target

DeepSeek Harness loads user skills from `%USERPROFILE%\.dsh\skills`. Other hosts may use the plugin entry, junctions, or their own skill directory.

## Drift

17 of 24 `SKILL.md` files match this repository byte for byte. The remaining 7 are older installed copies:

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

## Update

From an unrestricted shell, with a fresh agent session afterward:

```powershell
$repo = "E:\repositories\ai-skills"
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
