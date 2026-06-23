param(
    [Parameter(Mandatory = $true)]
    [string]$Prompt,

    [string]$Model = "qwen-image-2.0",

    [string]$Size = "1024x1024",

    [string]$OutputPath = "",

    [bool]$PromptExtend = $true,

    [bool]$Watermark = $false,

    [ValidateRange(1, 4)]
    [int]$Count = 1,

    [ValidateRange(10, 600)]
    [int]$TimeoutSeconds = 180,

    [ValidateRange(1, 10)]
    [int]$PollIntervalSeconds = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "generate_qwen_image.ts"
if (-not (Test-Path $scriptPath)) {
    throw "Missing TypeScript core: $scriptPath"
}

Get-Command node -ErrorAction Stop | Out-Null

$payload = @{
    prompt              = $Prompt
    model               = $Model
    size                = $Size
    outputPath          = $OutputPath
    promptExtend        = $PromptExtend
    watermark           = $Watermark
    count               = $Count
    timeoutSeconds      = $TimeoutSeconds
    pollIntervalSeconds = $PollIntervalSeconds
} | ConvertTo-Json -Depth 10 -Compress

$payloadBase64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payload))

# ponytail: PowerShell is just argument plumbing now; keep the API logic in TS.
& node --no-warnings --experimental-strip-types $scriptPath "--payload-base64=$payloadBase64"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
