---
name: windows-reclaim-disk-space
description: Audit or clean Windows system-drive storage with ranked, safety-classified candidates. Use for C 盘清理, low disk space, reclaiming Windows storage, deletion checklists, or deciding which system files are safe to remove. Do not use for non-Windows systems, arbitrary file deletion, or general performance troubleshooting.
---

# Windows Reclaim Disk Space

Audit first and default to reporting only. Treat every deletion as a separate, explicit permission boundary.

## Workflow

1. Confirm the target drive and requested mode. Default to drive `C` and `audit`; use `execute` only when the user explicitly asks to clean.
2. Run the read-only collector:

   ```powershell
   & "{baseDir}\scripts\collect_windows_disk.ps1" -DriveLetter C -Mode Quick
   ```

   Use `-Mode Full` when the quick scan cannot explain the used space. Full mode scans top-level and common Windows directories and can take several minutes.
3. Read `references/cleanup-policy.md` before classifying targets or proposing deletion. Convert every candidate into one of its required risk tiers.
4. Sort candidates by confirmed bytes, keep partial or inaccessible scans visibly marked, and produce the report shape below.
5. If execution is authorized, close or skip relevant applications, prefer official cleanup commands or uninstallers, execute one bounded batch, and re-measure free space. Never force-close applications with possible unsaved work.
6. Stop when the agreed free-space target is reached or only conditional/forbidden items remain.

## Collector Modes

- `Quick`: drive totals, known cleanup targets, running applications, root files, installed-app estimates, and protected-area evidence.
- `Full`: Quick plus ranked usage under the drive root, user profile, Windows, Program Files, Program Files (x86), and ProgramData.

The collector emits JSON to stdout and never deletes, moves, compresses, or modifies files. Run it elevated only when the user authorizes inspection of protected paths; report inaccessible paths instead of inventing sizes.

## Execution Rules

- Use official mechanisms first: `powercfg`, `dotnet nuget locals`, `go clean`, Windows Storage settings, application storage managers, Microsoft Store, and product uninstallers.
- Before recursive deletion, resolve the exact absolute path, verify it remains under the intended parent, reject drive roots and profile roots, reject wildcards, and stop on reparse points.
- Use native PowerShell end-to-end for Windows file operations and `-LiteralPath` for exact targets.
- Re-check the relevant process list. Skip active Codex, editor, chat, database, browser, or updater data unless the user explicitly closes the application.
- Preserve user data, configuration, credentials, databases, chat histories, project state, installed tools, and rollback points unless the user separately accepts the stated loss.
- After each batch, measure actual free bytes and verify any official cleanup command's exit status. Do not attribute unrelated background cleanup to a specific target.

## Report Output

Use the user's language and this order:

1. **Disk status**: total, used, free, free percentage, scan completeness, and administrator coverage.
2. **Confirmed cleanable**: exact path or mechanism, confirmed bytes, prerequisite, regeneration impact, and recommended command/UI.
3. **Conditional cleanup**: feature/data dependency, required confirmation, backup or close-app requirement, and safe mechanism.
4. **Do not delete manually**: protected paths and the supported alternative.
5. **Execution result** when applicable: before/after bytes, commands completed, failures, skipped targets, and residual risks.

Use `references/report-example.md` when a concrete formatting example is useful.

## Hard Prohibitions

- Never manually delete `Windows\Installer`, `Windows\WinSxS`, `WindowsApps`, `System32`, `SysWOW64`, page or swap files, security software data, or random anti-ransomware bait files.
- Never unregister WSL, remove restore points, uninstall SDKs/runtimes, delete chat data, or remove application databases without separate confirmation of the consequence.
- Never describe a cache as "safe" solely from its folder name. Require the policy criteria and current process evidence.
- Never hide partial scans, access failures, hard-link double counting, compression, or dynamic disk-space changes.
