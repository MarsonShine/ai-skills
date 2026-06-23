param(
    [string]$ConfigPath = "pdf-export.config.json",
    [string]$WorkDir = ".",
    [string]$StyleRoot = "",
    [string]$PandocPath = "",
    [string]$BrowserPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "export_markdown_pdf.ts"
if (-not (Test-Path $scriptPath)) {
    throw "Missing TypeScript core: $scriptPath"
}

Get-Command node -ErrorAction Stop | Out-Null

$payload = @{
    configPath  = $ConfigPath
    workDir     = $WorkDir
    styleRoot   = $StyleRoot
    pandocPath  = $PandocPath
    browserPath = $BrowserPath
} | ConvertTo-Json -Depth 5 -Compress

$payloadBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payload))

# ponytail: keep system-friendly PowerShell at the edge and move the workflow to TS.
& node --no-warnings --experimental-strip-types $scriptPath "--payload-base64=$payloadBase64"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
