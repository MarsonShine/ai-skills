# Example Windows Disk Cleanup Report

This example is based on a real system-drive cleanup but uses environment-relative paths instead of machine-specific user names.

## Disk status

- Before: 5.09 GiB free (2.35%)
- After: 66.57 GiB free (30.78%)
- Net observed increase: 61.48 GiB
- Validation: `.NET DriveInfo` and `fsutil volume diskfree` agreed
- Attribution note: the observed increase exceeded the measured targets; concurrent DISM++ or Windows background maintenance may have completed during the run, so the excess was not assigned to a specific target.

## Completed

| Action | Result | Impact |
| --- | --- | --- |
| Disable hibernation through `powercfg` | `hiberfil.sys` absent after verification | Hibernation and Fast Startup disabled; about 25.56 GiB target size |
| Clear NuGet locals | Official command exited successfully | About 12.5 GiB of packages and caches removed; packages redownload on build |
| Clear Go caches | Official command exited successfully | Module and build caches removed; `%USERPROFILE%\go\bin` preserved |

## Confirmed cleanable after closing the owning application

| Candidate | Observed size | Prerequisite |
| --- | ---: | --- |
| `%USERPROFILE%\.cache\codex-runtimes` | 1.68 GiB | Fully exit Codex; allow runtime redownload |
| Logitech Options+ cache | 0.81 GiB | Exit Logitech services/application |
| Copilot SDK obsolete CLI versions | 0.77 GiB | Keep the newest active version; close Copilot clients |
| VS Code obsolete extensions | 0.62 GiB | Close VS Code and confirm newer active versions |
| WeChat and WXWork logs | 0.62 GiB | Fully exit both clients; do not touch message databases |
| Hugging Face and Torch caches | 0.51 GiB | Accept model redownload |
| VS Code cached VSIX files | 0.48 GiB | Close VS Code |
| Postman caches and logs | 0.40 GiB | Ensure workspace is synchronized and close Postman |
| Bun install cache | 0.35 GiB | No package installation running |

## Conditional cleanup

- Old Windows Store application versions: use Store or app maintenance; never delete WindowsApps manually.
- Restore points: retain until the system is known stable, then remove only if rollback loss is acceptable.
- Old PowerToys, MongoDB Compass, Visual Studio, .NET, SQL Server, Docker, Python, or WSL components: use supported uninstallers after dependency/data review.
- Copilot `data.db`, editor workspace storage, browser profiles, and chat data: preserve unless the user separately accepts history loss.

## Do not delete manually

- `Windows\Installer`
- `Windows\WinSxS`
- `Program Files\WindowsApps`
- `System32`, `SysWOW64`, page files, and swap files
- security software and randomly named anti-ransomware bait files

## Stopped safely

The run stopped after exceeding the 50–55 GiB free-space target. Active Codex, VS Code, PowerToys, KuGou, and WXWork data was skipped, and no application was force-closed.
