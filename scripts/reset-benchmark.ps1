param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== RESET EZChords Benchmark ==="
Write-Host ""
Write-Host "Ce reset supprime uniquement les donnees locales du benchmark :"
Write-Host " - data\benchmark.sqlite (+ WAL/SHM)"
Write-Host " - var\uploads"
Write-Host " - var\worker"
Write-Host " - results\*"
Write-Host ""
Write-Host "Aucun fichier EZScore n'est touche."
Write-Host ""

if (-not $Force) {
    $answer = Read-Host "Tape RESET pour confirmer"
    if ($answer -ne "RESET") {
        Write-Host "Annule."
        exit 0
    }
}

$targets = @(
    (Join-Path $ProjectRoot "data\benchmark.sqlite"),
    (Join-Path $ProjectRoot "data\benchmark.sqlite-wal"),
    (Join-Path $ProjectRoot "data\benchmark.sqlite-shm")
)

foreach ($target in $targets) {
    if (Test-Path $target) {
        Remove-Item -Force $target
        Write-Host "Supprime: $target"
    }
}

foreach ($dir in @(
    (Join-Path $ProjectRoot "var\uploads"),
    (Join-Path $ProjectRoot "var\worker")
)) {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
        Write-Host "Supprime: $dir"
    }
}

$results = Join-Path $ProjectRoot "results"
if (Test-Path $results) {
    Get-ChildItem $results -Force | Remove-Item -Recurse -Force
    Write-Host "Nettoye: $results"
}

Write-Host ""
Write-Host "RESET_OK"
Write-Host "La base sera recreee automatiquement au prochain demarrage."
