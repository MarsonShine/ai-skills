# Windows Disk Cleanup Policy

Use this policy after collecting current disk facts. A path name alone never proves that deletion is safe.

## Classification gate

Classify a target as **confirmed cleanable** only when all applicable checks pass:

1. The target exists and its scan is complete enough to support the reported size.
2. It is a documented cache, log, temporary download, obsolete extension, or package-manager store that can be regenerated.
3. The owning application is closed, or the official cleanup command is designed to handle active locks.
4. The resolved target is not a drive root, profile root, reparse point, configuration store, credential store, database, chat history, project directory, or installed binary directory.
5. The user accepts any download, rebuild, first-start delay, or feature loss.

If any check fails, downgrade the item to **conditional cleanup** or **do not delete manually**.

## Tier A: confirmed cleanable when prerequisites pass

| Candidate | Required condition | Preferred mechanism | Expected impact |
| --- | --- | --- | --- |
| NuGet global, HTTP, temp, and plugin caches | User accepts package restore | `dotnet nuget locals all --clear` | Next build downloads packages again |
| Go module, build, and test caches | Preserve `GOPATH/bin`; user accepts downloads | `go clean -cache -testcache -modcache` | Next build downloads and recompiles |
| pip, npm, Bun, Hugging Face, and Torch caches | No related install/download is running | Package-manager command when available; otherwise exact cache path | Downloads or models are fetched again |
| Application `Cache`, `Code Cache`, GPU cache, crash dumps, and logs | Application is fully closed; do not include storage databases | Application UI first, exact cache paths second | First launch may be slower |
| VS Code cached VSIX files | VS Code is closed | Delete only `CachedExtensionVSIXs` contents | Extensions remain installed |
| VS Code obsolete extension folders | Folder is listed in `.obsolete` and a newer active version is confirmed | Let VS Code clean on restart or remove the exact obsolete folder | Active extension version remains |
| User and Windows temp contents | Delete contents, not the temp root; skip locked files and reparse points | Windows Storage/Storage Sense first | Active files remain locked and must be skipped |
| Old installer/update payload | Installed version is confirmed healthy and payload is not the repair source | Product updater or exact pending-download path | Re-download may be required for repair |

Never add parent and child target sizes together. For example, do not sum an entire application cache with its already-counted subcaches.

## Tier B: conditional cleanup

| Candidate | Confirmation required | Safe mechanism | Main risk |
| --- | --- | --- | --- |
| `hiberfil.sys` | User accepts disabling hibernation and Fast Startup | `powercfg /hibernate off`; restore with `powercfg /hibernate on` | Feature loss; never delete the file directly |
| Restore points or shadow copies | User accepts losing rollback coverage and the system is stable | System Protection or supported Windows UI/command | Cannot roll back to deleted point |
| Codex runtime/cache folders | Codex and related hosts are closed; network is available | Product repair/restart or exact documented cache | Current task or plugin runtime may break until redownload |
| Old Store application versions | Package is not the active registered version | Microsoft Store, app repair/reset, or supported package maintenance | Manual WindowsApps deletion corrupts package state |
| SDKs, runtimes, Visual Studio workloads, Windows SDKs | Projects and installed applications no longer require them | Visual Studio Installer or product uninstaller | Builds or applications may stop working |
| SQL Server, Docker, database products | Data is backed up and the product/instance is unused | Product uninstaller and product cleanup tools | Database, image, or volume loss |
| WSL distributions and virtual disks | Distribution data is backed up and permanent deletion is accepted | `wsl --export` before supported unregister/uninstall | Entire Linux environment can be destroyed |
| Chat, email, browser profile, editor workspace, or Copilot databases | User explicitly accepts history/state loss or has a backup | In-app storage management/export/reset | Irrecoverable user-data loss |
| Security, VPN, endpoint, and enterprise-management software | Organization/IT explicitly authorizes removal | Supported enterprise uninstaller | Device access, compliance, or networking failure |

Do not automate Tier B deletion from a generic script. Execute only the individually approved supported mechanism and validate immediately.

## Tier C: do not delete manually

Never recursively delete these paths or equivalents:

- `Windows\Installer`
- `Windows\WinSxS`
- `Windows\System32` and `Windows\SysWOW64`
- `Program Files\WindowsApps`
- `System Volume Information`
- `pagefile.sys`, `swapfile.sys`, and crash-control system files
- package-manager databases, application configuration databases, credential stores, browser profiles, and chat histories
- unknown randomly named root files/directories that may be anti-ransomware bait
- enterprise security directories such as endpoint protection, VPN, DLP, or device-management data

Use DISM, Windows Storage, Microsoft Store, an application repair/reset flow, or a supported uninstaller instead.

## Safe execution contract

Before any recursive deletion:

1. Resolve the exact target with `Resolve-Path -LiteralPath`.
2. Normalize it with `[System.IO.Path]::GetFullPath()`.
3. Verify the normalized target begins with the intended normalized parent plus a directory separator.
4. Verify the target is not equal to the allowed parent, profile root, Windows root, or drive root.
5. Reject wildcards, unresolved variables, junctions, symbolic links, and other reparse points.
6. Re-check relevant processes and skip active applications.
7. Use `Remove-Item -LiteralPath` from PowerShell; never pass enumerated paths into another shell.
8. Measure free bytes after the batch and report partial failures instead of retrying broad deletion.

## Report requirements

For each item include:

- observed path or supported mechanism
- confirmed logical bytes and whether the scan is complete, partial, or inaccessible
- risk tier
- prerequisite and consequence
- recommended supported action
- execution status: completed, failed, skipped-active, skipped-unconfirmed, or report-only

Always disclose that logical sizes can differ from reclaimed bytes because of hard links, compression, sparse files, active handles, filesystem metadata, and concurrent Windows maintenance.
