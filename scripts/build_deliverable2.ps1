param(
    [string]$Source = "Deliverable_2_BA_XG_ER_DV.md",
    [string]$Output = "Deliverable_2.pdf"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $repoRoot $Source
$tmpDir = Join-Path $repoRoot "tmp\deliverable2-build"

if (-not (Test-Path -LiteralPath $sourcePath)) {
    throw "No se encontró el fuente LaTeX: $sourcePath"
}

New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
& pdflatex -interaction=nonstopmode -halt-on-error -output-directory $tmpDir -jobname Deliverable_2 $sourcePath
if ($LASTEXITCODE -ne 0) {
    throw "pdflatex terminó con código $LASTEXITCODE"
}

$builtPdf = Join-Path $tmpDir "Deliverable_2.pdf"
$outputPath = Join-Path $repoRoot $Output
Copy-Item -LiteralPath $builtPdf -Destination $outputPath -Force

$pageLine = (& pdfinfo $outputPath | Select-String '^Pages:').ToString()
if ($pageLine -notmatch 'Pages:\s+1$') {
    throw "El PDF final no tiene exactamente una página: $pageLine"
}

Write-Output "PDF generado y verificado: $outputPath"
