[CmdletBinding()]
param(
    [ValidatePattern('^[A-Za-z]$')]
    [string]$DriveLetter = 'C',

    [ValidateSet('Quick', 'Full')]
    [string]$Mode = 'Quick',

    [ValidateRange(1, 100)]
    [int]$Top = 25,

    [string]$ProfilePath = $env:USERPROFILE
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$scanWarnings = [System.Collections.Generic.List[string]]::new()
$driveName = $DriveLetter.ToUpperInvariant()
$driveRoot = "$driveName`:\"
$profileRoot = [System.IO.Path]::GetFullPath($ProfilePath)

function Get-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-NativeText {
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string[]]$Arguments = @()
    )

    try {
        $output = & $Command @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        return [pscustomobject]@{
            command = $Command
            arguments = $Arguments
            exitCode = $exitCode
            output = @($output | ForEach-Object { $_.ToString() })
        }
    }
    catch {
        $scanWarnings.Add("Failed to run ${Command}: $($_.Exception.Message)")
        return [pscustomobject]@{
            command = $Command
            arguments = $Arguments
            exitCode = -1
            output = @($_.Exception.Message)
        }
    }
}

function Measure-PathUsage {
    param(
        [Parameter(Mandatory)]
        [string]$Id,

        [Parameter(Mandatory)]
        [string]$Path
    )

    $expanded = [Environment]::ExpandEnvironmentVariables($Path)
    $fullPath = [System.IO.Path]::GetFullPath($expanded)

    try {
        if (-not (Test-Path -LiteralPath $fullPath)) {
            return [pscustomobject]@{
                id = $Id
                path = $fullPath
                exists = $false
                kind = 'missing'
                bytes = [int64]0
                files = [int64]0
                directories = [int64]0
                status = 'missing'
                exitCode = 0
            }
        }

        $item = Get-Item -LiteralPath $fullPath -Force
        if (-not $item.PSIsContainer) {
            return [pscustomobject]@{
                id = $Id
                path = $fullPath
                exists = $true
                kind = 'file'
                bytes = [int64]$item.Length
                files = [int64]1
                directories = [int64]0
                status = 'complete'
                exitCode = 0
            }
        }

        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            return [pscustomobject]@{
                id = $Id
                path = $fullPath
                exists = $true
                kind = 'reparse-point'
                bytes = [int64]0
                files = [int64]0
                directories = [int64]0
                status = 'skipped-reparse-point'
                exitCode = 0
            }
        }

        $auditTarget = Join-Path ([System.IO.Path]::GetPathRoot($fullPath)) '__windows_disk_audit_target__'
        $raw = & robocopy.exe $fullPath $auditTarget /L /S /BYTES /XJ /R:0 /W:0 /NFL /NDL /NJH /NP 2>&1
        $exitCode = $LASTEXITCODE
        $text = $raw -join "`n"
        $bytesMatch = [regex]::Match($text, '(?m)^\s*Bytes\s*:\s*(\d+)')
        $filesMatch = [regex]::Match($text, '(?m)^\s*Files\s*:\s*(\d+)')
        $dirsMatch = [regex]::Match($text, '(?m)^\s*Dirs\s*:\s*(\d+)')

        $status = if (-not $bytesMatch.Success) {
            'inaccessible'
        }
        elseif ($exitCode -ge 8) {
            'partial'
        }
        else {
            'complete'
        }

        return [pscustomobject]@{
            id = $Id
            path = $fullPath
            exists = $true
            kind = 'directory'
            bytes = if ($bytesMatch.Success) { [int64]$bytesMatch.Groups[1].Value } else { [int64]0 }
            files = if ($filesMatch.Success) { [int64]$filesMatch.Groups[1].Value } else { [int64]0 }
            directories = if ($dirsMatch.Success) { [int64]$dirsMatch.Groups[1].Value } else { [int64]0 }
            status = $status
            exitCode = $exitCode
        }
    }
    catch {
        $scanWarnings.Add("Failed to inspect ${fullPath}: $($_.Exception.Message)")
        return [pscustomobject]@{
            id = $Id
            path = $fullPath
            exists = $null
            kind = 'unknown'
            bytes = [int64]0
            files = [int64]0
            directories = [int64]0
            status = 'error'
            exitCode = -1
        }
    }
}

function Get-TopChildDirectoryUsage {
    param(
        [Parameter(Mandatory)]
        [string]$ParentPath,

        [Parameter(Mandatory)]
        [int]$Limit
    )

    try {
        if (-not (Test-Path -LiteralPath $ParentPath)) {
            return @()
        }

        $rows = foreach ($child in Get-ChildItem -LiteralPath $ParentPath -Directory -Force -ErrorAction SilentlyContinue) {
            if ($child.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                continue
            }

            Measure-PathUsage -Id "child:$($child.Name)" -Path $child.FullName
        }

        return @($rows | Sort-Object bytes -Descending | Select-Object -First $Limit)
    }
    catch {
        $scanWarnings.Add("Failed to enumerate ${ParentPath}: $($_.Exception.Message)")
        return @()
    }
}

function Get-VscodeObsoleteExtensions {
    $extensionRoot = Join-Path $profileRoot '.vscode-insiders\extensions'
    $obsoleteFile = Join-Path $extensionRoot '.obsolete'
    if (-not (Test-Path -LiteralPath $obsoleteFile)) {
        return [pscustomobject]@{ totalBytes = [int64]0; folders = @(); status = 'missing' }
    }

    try {
        $obsolete = Get-Content -LiteralPath $obsoleteFile -Raw | ConvertFrom-Json
        $folders = foreach ($property in $obsolete.PSObject.Properties) {
            $candidate = Join-Path $extensionRoot $property.Name
            if (Test-Path -LiteralPath $candidate) {
                Measure-PathUsage -Id "vscode-obsolete:$($property.Name)" -Path $candidate
            }
        }

        $total = [int64](($folders | Measure-Object bytes -Sum).Sum)
        return [pscustomobject]@{ totalBytes = $total; folders = @($folders); status = 'complete' }
    }
    catch {
        $scanWarnings.Add("Failed to read VS Code obsolete extensions: $($_.Exception.Message)")
        return [pscustomobject]@{ totalBytes = [int64]0; folders = @(); status = 'error' }
    }
}

function Get-InstalledApplications {
    param([int]$Limit)

    $keys = @(
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )

    try {
        return @(Get-ItemProperty $keys -ErrorAction SilentlyContinue |
            Where-Object { $_.PSObject.Properties['DisplayName'] -and $_.PSObject.Properties['DisplayName'].Value } |
            ForEach-Object {
                $displayNameProperty = $_.PSObject.Properties['DisplayName']
                $displayVersionProperty = $_.PSObject.Properties['DisplayVersion']
                $publisherProperty = $_.PSObject.Properties['Publisher']
                $estimatedSizeProperty = $_.PSObject.Properties['EstimatedSize']
                $installLocationProperty = $_.PSObject.Properties['InstallLocation']
                [pscustomobject]@{
                    displayName = $displayNameProperty.Value
                    displayVersion = if ($displayVersionProperty) { $displayVersionProperty.Value } else { $null }
                    publisher = if ($publisherProperty) { $publisherProperty.Value } else { $null }
                    estimatedBytes = if ($estimatedSizeProperty) { [int64]$estimatedSizeProperty.Value * 1024 } else { [int64]0 }
                    installLocation = if ($installLocationProperty) { $installLocationProperty.Value } else { $null }
                }
            } |
            Sort-Object estimatedBytes -Descending |
            Select-Object -First $Limit)
    }
    catch {
        $scanWarnings.Add("Failed to read installed applications: $($_.Exception.Message)")
        return @()
    }
}

function Get-RelevantProcesses {
    $pattern = '^(codex|codex-code-mode-host|code|code - insiders|devenv|postman|wechat|wechatappex|wechatocr|wxwork|wxworkweb|wemeet|kugou|logi.*|coze|mongodb.*|powertoys.*|copilot.*|docker.*|com\.docker.*|sqlservr)$'
    $rows = foreach ($process in Get-Process -ErrorAction SilentlyContinue | Where-Object ProcessName -Match $pattern) {
        $path = $null
        try { $path = $process.Path } catch { $path = $null }
        [pscustomobject]@{
            name = $process.ProcessName
            id = $process.Id
            path = $path
        }
    }

    return @($rows | Sort-Object name, id)
}

if (-not (Test-Path -LiteralPath $driveRoot)) {
    throw "Drive $driveRoot does not exist."
}

if (-not (Test-Path -LiteralPath $profileRoot)) {
    throw "Profile path $profileRoot does not exist. Pass -ProfilePath explicitly."
}

$drive = [System.IO.DriveInfo]::new($driveName)
$knownTargetDefinitions = @(
    @{ id = 'hibernation-file'; path = (Join-Path $driveRoot 'hiberfil.sys') },
    @{ id = 'nuget-global-packages'; path = (Join-Path $profileRoot '.nuget\packages') },
    @{ id = 'nuget-local-cache'; path = (Join-Path $profileRoot 'AppData\Local\NuGet') },
    @{ id = 'codex-runtime-cache'; path = (Join-Path $profileRoot '.cache\codex-runtimes') },
    @{ id = 'go-module-cache'; path = (Join-Path $profileRoot 'go\pkg\mod') },
    @{ id = 'go-build-cache'; path = (Join-Path $profileRoot 'AppData\Local\go-build') },
    @{ id = 'pip-cache'; path = (Join-Path $profileRoot 'AppData\Local\pip\Cache') },
    @{ id = 'npm-cache'; path = (Join-Path $profileRoot 'AppData\Local\npm-cache') },
    @{ id = 'bun-install-cache'; path = (Join-Path $profileRoot '.bun\install\cache') },
    @{ id = 'huggingface-cache'; path = (Join-Path $profileRoot '.cache\huggingface') },
    @{ id = 'torch-cache'; path = (Join-Path $profileRoot '.cache\torch') },
    @{ id = 'logi-options-cache'; path = (Join-Path $driveRoot 'ProgramData\LogiOptionsPlus\cache') },
    @{ id = 'copilot-cli-cache'; path = (Join-Path $profileRoot 'AppData\Local\github-copilot-sdk\cli') },
    @{ id = 'vscode-vsix-cache'; path = (Join-Path $profileRoot 'AppData\Roaming\Code - Insiders\CachedExtensionVSIXs') },
    @{ id = 'wechat-logs'; path = (Join-Path $profileRoot 'AppData\Roaming\Tencent\xwechat\log') },
    @{ id = 'wxwork-logs'; path = (Join-Path $profileRoot 'AppData\Roaming\Tencent\WXWork\Log') },
    @{ id = 'postman-cache'; path = (Join-Path $profileRoot 'AppData\Roaming\Postman\Cache') },
    @{ id = 'postman-code-cache'; path = (Join-Path $profileRoot 'AppData\Roaming\Postman\Code Cache') },
    @{ id = 'postman-logs'; path = (Join-Path $profileRoot 'AppData\Roaming\Postman\logs') },
    @{ id = 'coze-updater-pending'; path = (Join-Path $profileRoot 'AppData\Local\coze-updater\pending') },
    @{ id = 'user-temp'; path = (Join-Path $profileRoot 'AppData\Local\Temp') },
    @{ id = 'codex-temp'; path = (Join-Path $profileRoot '.codex\.tmp') },
    @{ id = 'copilot-data-db'; path = (Join-Path $profileRoot '.copilot\data.db') },
    @{ id = 'docker-user-data'; path = (Join-Path $profileRoot 'AppData\Local\Docker') },
    @{ id = 'windows-temp'; path = (Join-Path $driveRoot 'Windows\Temp') },
    @{ id = 'windows-update-downloads'; path = (Join-Path $driveRoot 'Windows\SoftwareDistribution\Download') },
    @{ id = 'windows-installer'; path = (Join-Path $driveRoot 'Windows\Installer') },
    @{ id = 'winsxs'; path = (Join-Path $driveRoot 'Windows\WinSxS') },
    @{ id = 'windowsapps'; path = (Join-Path $driveRoot 'Program Files\WindowsApps') }
)

$knownTargets = foreach ($definition in $knownTargetDefinitions) {
    Measure-PathUsage -Id $definition.id -Path $definition.path
}

$rootFiles = @(Get-ChildItem -LiteralPath $driveRoot -File -Force -ErrorAction SilentlyContinue |
    Sort-Object Length -Descending |
    Select-Object -First $Top |
    ForEach-Object {
        [pscustomobject]@{
            path = $_.FullName
            bytes = [int64]$_.Length
            lastWriteTime = $_.LastWriteTimeUtc.ToString('o')
        }
    })

$fullDirectoryGroups = @()
if ($Mode -eq 'Full') {
    $parents = @(
        $driveRoot,
        (Join-Path $driveRoot 'Windows'),
        (Join-Path $driveRoot 'Program Files'),
        (Join-Path $driveRoot 'Program Files (x86)'),
        (Join-Path $driveRoot 'ProgramData'),
        $profileRoot
    )

    $fullDirectoryGroups = foreach ($parent in $parents) {
        [pscustomobject]@{
            parent = $parent
            children = @(Get-TopChildDirectoryUsage -ParentPath $parent -Limit $Top)
        }
    }
}

$nativeEvidence = [pscustomobject]@{
    shadowStorage = Invoke-NativeText -Command 'vssadmin.exe' -Arguments @('list', 'shadowstorage')
    compactOs = Invoke-NativeText -Command 'compact.exe' -Arguments @('/CompactOS:query')
    dotnetSdks = if (Get-Command dotnet.exe -ErrorAction SilentlyContinue) {
        Invoke-NativeText -Command 'dotnet.exe' -Arguments @('--list-sdks')
    } else { $null }
    dotnetRuntimes = if (Get-Command dotnet.exe -ErrorAction SilentlyContinue) {
        Invoke-NativeText -Command 'dotnet.exe' -Arguments @('--list-runtimes')
    } else { $null }
    wslDistributions = if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
        Invoke-NativeText -Command 'wsl.exe' -Arguments @('--list', '--verbose')
    } else { $null }
}

$result = [pscustomobject]@{
    schemaVersion = 1
    generatedAtUtc = [DateTime]::UtcNow.ToString('o')
    computerName = $env:COMPUTERNAME
    mode = $Mode
    isAdministrator = Get-IsAdministrator
    drive = [pscustomobject]@{
        name = $drive.Name
        totalBytes = [int64]$drive.TotalSize
        freeBytes = [int64]$drive.AvailableFreeSpace
        usedBytes = [int64]($drive.TotalSize - $drive.AvailableFreeSpace)
        freePercent = [math]::Round(100 * $drive.AvailableFreeSpace / $drive.TotalSize, 2)
    }
    profilePath = $profileRoot
    rootFiles = $rootFiles
    knownTargets = @($knownTargets | Sort-Object bytes -Descending)
    vscodeObsoleteExtensions = Get-VscodeObsoleteExtensions
    runningProcesses = Get-RelevantProcesses
    installedApplications = Get-InstalledApplications -Limit $Top
    fullDirectoryGroups = @($fullDirectoryGroups)
    nativeEvidence = $nativeEvidence
    warnings = @($scanWarnings)
}

$result | ConvertTo-Json -Depth 9
exit 0
