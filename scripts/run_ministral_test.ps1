[CmdletBinding()]
param(
    [string]$Model = 'ministral-3:3b',
    [int]$ContextSize = 8192,
    [int]$OutputLimit = 3000,
    [int]$Seed = 42,
    [switch]$Think
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$promptPath = Join-Path $repositoryRoot 'pruebas\01_prompt_directo_ministral.md'
$transcriptPath = Join-Path $repositoryRoot 'pruebas\01_transcripcion_reunion_simulada.md'
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

if (-not (Test-Path -LiteralPath $promptPath)) {
    throw "Prompt not found: $promptPath"
}

if (-not (Test-Path -LiteralPath $transcriptPath)) {
    throw "Transcript not found: $transcriptPath"
}

$taskPrompt = Get-Content -Raw -Encoding UTF8 -LiteralPath $promptPath
$meetingTranscript = Get-Content -Raw -Encoding UTF8 -LiteralPath $transcriptPath
$modelInput = $taskPrompt + "`n`n--- TRANSCRIPCION A ANALIZAR ---`n`n" + $meetingTranscript
$safeModelName = $Model -replace '[^A-Za-z0-9._-]', '_'
$outputPath = Join-Path $repositoryRoot "pruebas\repeticion_${safeModelName}_$timestamp.json"

$requestBody = @{
    model = $Model
    prompt = $modelInput
    stream = $false
    format = 'json'
    think = [bool]$Think
    keep_alive = '10m'
    options = @{
        num_ctx = $ContextSize
        temperature = 0
        seed = $Seed
        num_predict = $OutputLimit
    }
} | ConvertTo-Json -Depth 6
$requestBytes = [System.Text.Encoding]::UTF8.GetBytes($requestBody)

$result = Invoke-RestMethod `
    -Method Post `
    -Uri 'http://localhost:11434/api/generate' `
    -ContentType 'application/json' `
    -Body $requestBytes

$responseJsonValid = $true
try {
    $parsedResponse = $result.response | ConvertFrom-Json
} catch {
    $responseJsonValid = $false
    $parsedResponse = $null
}

$ollamaVersion = (ollama --version 2>&1 | Out-String).Trim()

$record = [ordered]@{
    model = $Model
    ollama_version = $ollamaVersion
    context_size = $ContextSize
    temperature = 0
    seed = $Seed
    output_limit = $OutputLimit
    thinking_enabled = [bool]$Think
    created_at = (Get-Date).ToString('o')
    load_duration_ns = $result.load_duration
    total_duration_ns = $result.total_duration
    prompt_eval_duration_ns = $result.prompt_eval_duration
    prompt_eval_count = $result.prompt_eval_count
    eval_duration_ns = $result.eval_duration
    eval_count = $result.eval_count
    done_reason = $result.done_reason
    response_json_valid = $responseJsonValid
    response_raw = $result.response
    response = $parsedResponse
    thinking = $result.thinking
}

$json = $record | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText($outputPath, $json, [System.Text.UTF8Encoding]::new($false))

Write-Host "Saved result to: $outputPath"
