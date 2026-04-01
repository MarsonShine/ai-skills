#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$BaseDir,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$OutputDir,

    [Parameter(Mandatory = $true, Position = 2)]
    [int]$Cols,

    [Parameter(Mandatory = $true, Position = 3)]
    [int]$Rows,

    [Parameter(Mandatory = $true, Position = 4)]
    [int]$CellWidth,

    [Parameter(Mandatory = $true, Position = 5)]
    [int]$CellHeight,

    [Parameter(Position = 6)]
    [string]$CandidateList
)

$ErrorActionPreference = "Stop"

function Get-PythonCommand {
    if ($env:PHOTO_SELECTOR_PYTHON) {
        if (-not (Test-Path -LiteralPath $env:PHOTO_SELECTOR_PYTHON -PathType Leaf)) {
            throw "PHOTO_SELECTOR_PYTHON points to a missing file: $($env:PHOTO_SELECTOR_PYTHON)"
        }

        return @{
            Exe = $env:PHOTO_SELECTOR_PYTHON
            Args = @()
        }
    }

    $LocalPythonCandidates = @(
        (Join-Path $ScriptDir "..\.venv\Scripts\python.exe"),
        (Join-Path $ScriptDir "..\.venv\bin\python")
    )

    foreach ($Candidate in $LocalPythonCandidates) {
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            return @{
                Exe = $Candidate
                Args = @()
            }
        }
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{
            Exe = "py"
            Args = @("-3")
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{
            Exe = "python"
            Args = @()
        }
    }

    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        return @{
            Exe = "python3"
            Args = @()
        }
    }

    throw "Python 3 was not found. Install Python 3 and Pillow with: python -m pip install pillow"
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Command,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Command.Exe @($Command.Args + $Arguments)
}

$ScriptDir = Split-Path -Parent $PSCommandPath
$PythonScript = Join-Path $ScriptDir "contact_sheet_pillow.py"

if (-not (Test-Path -LiteralPath $BaseDir -PathType Container)) {
    throw "Base directory not found: $BaseDir"
}

if (-not (Test-Path -LiteralPath $PythonScript -PathType Leaf)) {
    throw "Missing Python backend: $PythonScript"
}

$Python = Get-PythonCommand
Invoke-Python -Command $Python -Arguments @($PythonScript, "--check-deps") | Out-Null

$Files = @()

if ($CandidateList) {
    if (-not (Test-Path -LiteralPath $CandidateList -PathType Leaf)) {
        throw "Candidate list not found: $CandidateList"
    }

    foreach ($Line in Get-Content -LiteralPath $CandidateList) {
        $Trimmed = $Line.Trim()
        if (-not $Trimmed) {
            continue
        }

        if ([System.IO.Path]::IsPathRooted($Trimmed)) {
            $Files += $Trimmed
        }
        else {
            $Files += (Join-Path $BaseDir $Trimmed)
        }
    }
}
else {
    $Files = @(
        Get-ChildItem -LiteralPath $BaseDir -File |
            Where-Object { $_.Extension -imatch "^\.(jpg|jpeg)$" } |
            Sort-Object Name |
            ForEach-Object { $_.FullName }
    )
}

if ($Files.Count -eq 0) {
    throw "No JPG files found."
}

foreach ($File in $Files) {
    if (-not (Test-Path -LiteralPath $File -PathType Leaf)) {
        throw "Image not found: $File"
    }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$IndexFile = Join-Path $OutputDir "index.txt"
Set-Content -LiteralPath $IndexFile -Value @()

$PageSize = $Cols * $Rows
$PageNumber = 1

for ($i = 0; $i -lt $Files.Count; $i += $PageSize) {
    $SliceEnd = [Math]::Min($i + $PageSize - 1, $Files.Count - 1)
    $PageFiles = @($Files[$i..$SliceEnd])
    $OutputFile = Join-Path $OutputDir ("sheet_{0}.jpg" -f $PageNumber.ToString("00"))

    Invoke-Python -Command $Python -Arguments (@($PythonScript, $OutputFile, $Cols, $Rows, $CellWidth, $CellHeight) + $PageFiles) | Out-Null

    $FirstName = [System.IO.Path]::GetFileName($PageFiles[0])
    $LastName = [System.IO.Path]::GetFileName($PageFiles[$PageFiles.Count - 1])
    Add-Content -LiteralPath $IndexFile -Value ("sheet_{0}: {1} - {2}" -f $PageNumber.ToString("00"), $FirstName, $LastName)

    $PageNumber++
}

Write-Output ("Generated {0} sheet(s) for {1} image(s) in {2}" -f ($PageNumber - 1), $Files.Count, $OutputDir)
