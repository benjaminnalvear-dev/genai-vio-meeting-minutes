[CmdletBinding()]
param(
    [string]$Model = 'ministral-3:3b',
    [int]$ContextSize = 8192,
    [int]$OutputLimit = 3000,
    [int]$Seed = 42
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$promptPath = Join-Path $repositoryRoot 'pruebas\01_prompt_directo_ministral.md'
$transcriptPath = Join-Path $repositoryRoot 'pruebas\01_transcripcion_reunion_simulada.md'
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outputPath = Join-Path $repositoryRoot "pruebas\repeticion_ministral_$timestamp.json"

if (-not (Test-Path -LiteralPath $promptPath)) {
    throw "Prompt not found: $promptPath"
}

if (-not (Test-Path -LiteralPath $transcriptPath)) {
    throw "Transcript not found: $transcriptPath"
}

$taskPrompt = Get-Content -Raw -LiteralPath $promptPath
$meetingTranscript = Get-Content -Raw -LiteralPath $transcriptPath
$modelInput = $taskPrompt + "`n`n--- TRANSCRIPCION A ANALIZAR ---`n`n" + $meetingTranscript

$requestBody = @{
    model = $Model
    prompt = $modelInput
    stream = $false
    format = 'json'
    keep_alive = '10m'
    options = @{
        num_ctx = $ContextSize
        temperature = 0
        seed = $Seed
        num_predict = $OutputLimit
    }
} | ConvertTo-Json -Depth 6

$result = Invoke-RestMethod `
    -Method Post `
    -Uri 'http://localhost:11434/api/generate' `
    -ContentType 'application/json' `
    -Body $requestBody

$record = [ordered]@{
    model = $Model
    context_size = $ContextSize
    temperature = 0
    seed = $Seed
    output_limit = $OutputLimit
    created_at = (Get-Date).ToString('o')
    total_duration_ns = $result.total_duration
    prompt_eval_count = $result.prompt_eval_count
    eval_count = $result.eval_count
    done_reason = $result.done_reason
    response = $result.response | ConvertFrom-Json
}

$json = $record | ConvertTo-Json -Depth 20
[System.IO.File]::WriteAllText($outputPath, $json, [System.Text.UTF8Encoding]::new($false))

Write-Host "Saved result to: $outputPath"
