param(
    [string]$ConfigPath = "pdf-export.config.json",
    [string]$WorkDir = ".",
    [string]$StyleRoot = "",
    [string]$PandocPath = "",
    [string]$BrowserPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-Executable {
    param(
        [string]$CommandName,
        [string[]]$CandidatePaths
    )

    foreach ($candidate in $CandidatePaths) {
        if ($candidate -and (Test-Path $candidate)) {
            return (Resolve-Path $candidate).Path
        }
    }

    try {
        return (Get-Command $CommandName -ErrorAction Stop).Source
    }
    catch {
        throw "Could not find executable: $CommandName"
    }
}

function Wait-ForFileReady {
    param(
        [string]$Path,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastSize = -1L
    $stableSeconds = 0

    while ((Get-Date) -lt $deadline) {
        if (Test-Path $Path) {
            $item = Get-Item $Path -ErrorAction Stop
            if ($item.Length -gt 0) {
                if ($item.Length -eq $lastSize) {
                    $stableSeconds += 1
                    if ($stableSeconds -ge 2) {
                        return
                    }
                }
                else {
                    $stableSeconds = 0
                }

                $lastSize = $item.Length
            }
        }

        Start-Sleep -Seconds 1
    }

    throw "Timed out waiting for output file: $Path"
}

function Get-OptionalValue {
    param(
        [object]$InputObject,
        [string]$Name,
        [object]$DefaultValue = $null
    )

    if ($null -eq $InputObject) {
        return $DefaultValue
    }

    $prop = $InputObject.PSObject.Properties[$Name]
    if ($null -eq $prop) {
        return $DefaultValue
    }

    return $prop.Value
}

function Resolve-StylePath {
    param(
        [string]$Preset,
        [string]$Css,
        [string]$StyleRootPath
    )

    if ($Css) {
        $candidate = if ([System.IO.Path]::IsPathRooted($Css)) {
            $Css
        }
        else {
            Join-Path $PWD $Css
        }

        if (-not (Test-Path $candidate)) {
            throw "Custom CSS not found: $candidate"
        }

        return (Resolve-Path $candidate).Path
    }

    $presetName = if ($Preset) { $Preset } else { "default" }
    $allowed = @("default", "compact", "resume")
    if ($presetName -notin $allowed) {
        throw "Unsupported preset '$presetName'. Supported presets: $($allowed -join ', ')"
    }

    $presetPath = Join-Path $StyleRootPath "$presetName.css"
    if (-not (Test-Path $presetPath)) {
        throw "Preset stylesheet not found: $presetPath"
    }

    return (Resolve-Path $presetPath).Path
}

function Convert-Document {
    param(
        [pscustomobject]$Document,
        [pscustomobject]$Defaults,
        [string]$ResolvedWorkDir,
        [string]$ResolvedStyleRoot,
        [string]$ResolvedPandocPath,
        [string]$ResolvedBrowserPath,
        [string]$TempRoot
    )

    if (-not $Document.input) {
        throw "Each document entry must contain an 'input' field."
    }
    if (-not $Document.output) {
        throw "Each document entry must contain an 'output' field."
    }

    $inputPath = if ([System.IO.Path]::IsPathRooted([string]$Document.input)) {
        [string]$Document.input
    }
    else {
        Join-Path $ResolvedWorkDir ([string]$Document.input)
    }

    if (-not (Test-Path $inputPath)) {
        throw "Markdown input not found: $inputPath"
    }

    $outputPath = if ([System.IO.Path]::IsPathRooted([string]$Document.output)) {
        [string]$Document.output
    }
    else {
        Join-Path $ResolvedWorkDir ([string]$Document.output)
    }

    $outputDir = Split-Path -Parent $outputPath
    if ($outputDir -and -not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }

    $title = [string](Get-OptionalValue -InputObject $Document -Name "title" -DefaultValue ([System.IO.Path]::GetFileNameWithoutExtension($inputPath)))
    $preset = [string](Get-OptionalValue -InputObject $Document -Name "preset" -DefaultValue (Get-OptionalValue -InputObject $Defaults -Name "preset" -DefaultValue "default"))
    $cssPath = Resolve-StylePath -Preset $preset -Css ([string](Get-OptionalValue -InputObject $Document -Name "css" -DefaultValue "")) -StyleRootPath $ResolvedStyleRoot
    $resourcePath = [string](Get-OptionalValue -InputObject $Document -Name "resourcePath" -DefaultValue (Get-OptionalValue -InputObject $Defaults -Name "resourcePath" -DefaultValue "."))
    $resourcePathResolved = if ([System.IO.Path]::IsPathRooted($resourcePath)) { $resourcePath } else { Join-Path $ResolvedWorkDir $resourcePath }
    $virtualTimeBudget = [int](Get-OptionalValue -InputObject $Document -Name "virtualTimeBudget" -DefaultValue (Get-OptionalValue -InputObject $Defaults -Name "virtualTimeBudget" -DefaultValue 5000))

    $safeKey = [System.IO.Path]::GetFileNameWithoutExtension([string]$Document.output)
    $htmlPath = Join-Path $TempRoot "$safeKey.html"
    $headPath = Join-Path $TempRoot "$safeKey-head.html"
    $tempPdfPath = Join-Path $TempRoot "$safeKey.pdf"

    $styleMarkup = "<style>`r`n" + (Get-Content -Raw $cssPath) + "`r`n</style>`r`n"
    Set-Content -Path $headPath -Value $styleMarkup -Encoding UTF8

    & $ResolvedPandocPath $inputPath `
        -f gfm `
        -t html5 `
        -s `
        --quiet `
        "--metadata=title:$title" `
        --embed-resources `
        "--resource-path=$resourcePathResolved" `
        -H $headPath `
        -o $htmlPath

    if ($LASTEXITCODE -ne 0) {
        throw "Pandoc conversion failed for $inputPath"
    }

    if (Test-Path $tempPdfPath) {
        Remove-Item $tempPdfPath -Force
    }

    $htmlUri = ([System.Uri]::new((Resolve-Path $htmlPath).Path)).AbsoluteUri

    & $ResolvedBrowserPath `
        --headless `
        --disable-gpu `
        --allow-file-access-from-files `
        --no-first-run `
        --no-default-browser-check `
        "--virtual-time-budget=$virtualTimeBudget" `
        --no-pdf-header-footer `
        "--print-to-pdf=$tempPdfPath" `
        $htmlUri

    Wait-ForFileReady -Path $tempPdfPath
    Copy-Item $tempPdfPath $outputPath -Force
    Write-Host "Generated: $outputPath"
}

$resolvedWorkDir = (Resolve-Path $WorkDir).Path
$resolvedConfigPath = if ([System.IO.Path]::IsPathRooted($ConfigPath)) {
    $ConfigPath
}
else {
    Join-Path $resolvedWorkDir $ConfigPath
}

if (-not (Test-Path $resolvedConfigPath)) {
    throw "Config file not found: $resolvedConfigPath"
}

$resolvedStyleRoot = if ($StyleRoot) {
    if ([System.IO.Path]::IsPathRooted($StyleRoot)) { $StyleRoot } else { Join-Path $resolvedWorkDir $StyleRoot }
}
else {
    Join-Path (Split-Path -Parent $PSScriptRoot) "assets"
}

if (-not (Test-Path $resolvedStyleRoot)) {
    throw "Style root not found: $resolvedStyleRoot"
}

$resolvedPandocPath = if ($PandocPath) {
    if ([System.IO.Path]::IsPathRooted($PandocPath)) { $PandocPath } else { Find-Executable -CommandName $PandocPath -CandidatePaths @() }
}
else {
    Find-Executable -CommandName "pandoc" -CandidatePaths @(
        (Join-Path $env:LOCALAPPDATA "Pandoc\pandoc.exe")
    )
}

$resolvedBrowserPath = if ($BrowserPath) {
    if ([System.IO.Path]::IsPathRooted($BrowserPath)) { $BrowserPath } else { Find-Executable -CommandName $BrowserPath -CandidatePaths @() }
}
else {
    Find-Executable -CommandName "msedge" -CandidatePaths @(
        (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
        (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
        (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe")
    )
}

$config = Get-Content -Raw $resolvedConfigPath | ConvertFrom-Json
if (-not $config.documents -or $config.documents.Count -eq 0) {
    throw "Config must contain at least one document entry."
}

$defaults = if ($config.defaults) { $config.defaults } else { [pscustomobject]@{} }
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("markdown-pdf-export-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

try {
    foreach ($document in $config.documents) {
        Convert-Document `
            -Document $document `
            -Defaults $defaults `
            -ResolvedWorkDir $resolvedWorkDir `
            -ResolvedStyleRoot $resolvedStyleRoot `
            -ResolvedPandocPath $resolvedPandocPath `
            -ResolvedBrowserPath $resolvedBrowserPath `
            -TempRoot $tempRoot
    }
}
finally {
    Remove-Item $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
