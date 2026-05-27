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

function Get-ApiKey {
    if (-not [string]::IsNullOrWhiteSpace($env:QWEN_IMAGE_API_KEY)) {
        return $env:QWEN_IMAGE_API_KEY
    }

    if (-not [string]::IsNullOrWhiteSpace($env:DASHSCOPE_API_KEY)) {
        return $env:DASHSCOPE_API_KEY
    }

    throw "Set QWEN_IMAGE_API_KEY or DASHSCOPE_API_KEY before running this script."
}

function Get-BaseUrl {
    if (-not [string]::IsNullOrWhiteSpace($env:DASHSCOPE_BASE_URL)) {
        return $env:DASHSCOPE_BASE_URL.TrimEnd("/")
    }

    return "https://dashscope.aliyuncs.com/api/v1"
}

function New-Slug {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $slug = $Value.ToLowerInvariant()
    $slug = [regex]::Replace($slug, "[^a-z0-9]+", "-").Trim("-")
    if ([string]::IsNullOrWhiteSpace($slug)) {
        return "image"
    }

    if ($slug.Length -gt 48) {
        return $slug.Substring(0, 48).Trim("-")
    }

    return $slug
}

function Get-ImageUrls {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Response
    )

    $urls = New-Object System.Collections.Generic.List[string]

    $outputProperty = $Response.PSObject.Properties["output"]
    $output = if ($null -ne $outputProperty) { $outputProperty.Value } else { $null }

    $resultsProperty = if ($null -ne $output) { $output.PSObject.Properties["results"] } else { $null }
    if ($null -ne $resultsProperty) {
        foreach ($item in $resultsProperty.Value) {
            $urlProperty = $item.PSObject.Properties["url"]
            if ($null -ne $urlProperty -and -not [string]::IsNullOrWhiteSpace([string]$urlProperty.Value)) {
                $urls.Add([string]$urlProperty.Value)
                continue
            }

            $imageUrlProperty = $item.PSObject.Properties["image_url"]
            if ($null -ne $imageUrlProperty -and -not [string]::IsNullOrWhiteSpace([string]$imageUrlProperty.Value)) {
                $urls.Add([string]$imageUrlProperty.Value)
            }
        }
    }

    $choicesProperty = if ($null -ne $output) { $output.PSObject.Properties["choices"] } else { $null }
    if ($urls.Count -eq 0 -and $null -ne $choicesProperty) {
        foreach ($choice in $choicesProperty.Value) {
            $messageProperty = $choice.PSObject.Properties["message"]
            if ($null -eq $messageProperty) {
                continue
            }

            $contentProperty = $messageProperty.Value.PSObject.Properties["content"]
            if ($null -eq $contentProperty) {
                continue
            }

            foreach ($contentItem in $contentProperty.Value) {
                $imageProperty = $contentItem.PSObject.Properties["image"]
                if ($null -ne $imageProperty -and -not [string]::IsNullOrWhiteSpace([string]$imageProperty.Value)) {
                    $urls.Add([string]$imageProperty.Value)
                }
            }
        }
    }

    return $urls
}

function Resolve-OutputTargets {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BaseOutputPath,

        [Parameter(Mandatory = $true)]
        [int]$ImageCount,

        [Parameter(Mandatory = $true)]
        [string]$PromptText
    )

    $targets = New-Object System.Collections.Generic.List[string]
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $slug = New-Slug -Value $PromptText

    if ([string]::IsNullOrWhiteSpace($BaseOutputPath)) {
        $dir = Join-Path -Path (Get-Location) -ChildPath "generated-images"
        New-Item -ItemType Directory -Path $dir -Force | Out-Null

        if ($ImageCount -eq 1) {
            $targets.Add((Join-Path -Path $dir -ChildPath "$slug-$timestamp.png"))
            return $targets
        }

        for ($index = 1; $index -le $ImageCount; $index++) {
            $targets.Add((Join-Path -Path $dir -ChildPath ("{0}-{1}-{2:d2}.png" -f $slug, $timestamp, $index)))
        }

        return $targets
    }

    $resolvedPath = [System.IO.Path]::GetFullPath($BaseOutputPath)
    $hasExtension = -not [string]::IsNullOrWhiteSpace([System.IO.Path]::GetExtension($resolvedPath))

    if ($ImageCount -eq 1 -and $hasExtension) {
        $directory = [System.IO.Path]::GetDirectoryName($resolvedPath)
        if (-not [string]::IsNullOrWhiteSpace($directory)) {
            New-Item -ItemType Directory -Path $directory -Force | Out-Null
        }

        $targets.Add($resolvedPath)
        return $targets
    }

    $baseDirectory = if ($hasExtension) {
        [System.IO.Path]::GetDirectoryName($resolvedPath)
    }
    else {
        $resolvedPath
    }

    if ([string]::IsNullOrWhiteSpace($baseDirectory)) {
        $baseDirectory = Get-Location
    }

    New-Item -ItemType Directory -Path $baseDirectory -Force | Out-Null

    $baseName = if ($hasExtension) {
        [System.IO.Path]::GetFileNameWithoutExtension($resolvedPath)
    }
    else {
        "{0}-{1}" -f $slug, $timestamp
    }

    for ($index = 1; $index -le $ImageCount; $index++) {
        $suffix = if ($ImageCount -eq 1) { "" } else { "-{0:d2}" -f $index }
        $targets.Add((Join-Path -Path $baseDirectory -ChildPath "$baseName$suffix.png"))
    }

    return $targets
}

$apiKey = Get-ApiKey
$baseUrl = Get-BaseUrl
$headers = @{
    Authorization  = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

$normalizedSize = if ($Size -match "^\d+x\d+$") {
    $Size -replace "x", "*"
}
else {
    $Size
}

$requestBody = @{
    model      = $Model
    input      = @{
        messages = @(
            @{
                role    = "user"
                content = @(
                    @{
                        text = $Prompt
                    }
                )
            }
        )
    }
    parameters = @{
        size          = $normalizedSize
        prompt_extend = $PromptExtend
        watermark     = $Watermark
        n             = $Count
    }
} | ConvertTo-Json -Depth 10

$createResponse = Invoke-RestMethod -Method Post -Uri "$baseUrl/services/aigc/multimodal-generation/generation" -Headers $headers -Body $requestBody
$taskId = $null
$finalResponse = $createResponse
$imageUrls = @(Get-ImageUrls -Response $finalResponse)

if ($imageUrls.Count -eq 0) {
    $payload = $finalResponse | ConvertTo-Json -Depth 10 -Compress
    throw "DashScope did not return an image URL. Payload=$payload"
}

$targets = @(Resolve-OutputTargets -BaseOutputPath $OutputPath -ImageCount $imageUrls.Count -PromptText $Prompt)
$savedFiles = New-Object System.Collections.Generic.List[string]

for ($index = 0; $index -lt $imageUrls.Count; $index++) {
    Invoke-WebRequest -Uri $imageUrls[$index] -OutFile $targets[$index]
    $savedFiles.Add($targets[$index])
}

[pscustomobject]@{
    model      = $Model
    size       = $normalizedSize
    taskId     = $taskId
    imageUrls  = $imageUrls
    savedFiles = $savedFiles
} | ConvertTo-Json -Depth 10
