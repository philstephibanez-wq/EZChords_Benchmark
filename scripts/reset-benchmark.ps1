param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== RESET EZChords Benchmark ==="
Write-Host ""
Write-Host "Suppression des donnees locales du benchmark :"
Write-Host " - SQLite (+ WAL/SHM)"
Write-Host " - public\benchmark-audio"
Write-Host " - var\uploads"
Write-Host " - var\worker"
Write-Host " - results"
Write-Host " - H:\temp\EZChords_Benchmark\work"
Write-Host ""
Write-Host "Conservation : code, deps, modeles/cache, configuration."
Write-Host "Aucun fichier EZScore n'est touche."
Write-Host ""

if (-not $Force) {
    $answer = Read-Host "Tape RESET pour confirmer"
    if ($answer -ne "RESET") {
        Write-Host "Annule."
        exit 0
    }
}

$files = @(
    (Join-Path $ProjectRoot "data\benchmark.sqlite"),
    (Join-Path $ProjectRoot "data\benchmark.sqlite-wal"),
    (Join-Path $ProjectRoot "data\benchmark.sqlite-shm")
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Remove-Item -Force $file
        Write-Host "Supprime: $file"
    }
}

$dirsToRemove = @(
    (Join-Path $ProjectRoot "public\benchmark-audio"),
    (Join-Path $ProjectRoot "var\uploads"),
    (Join-Path $ProjectRoot "var\worker"),
    (Join-Path $ProjectRoot "results"),
    "H:\temp\EZChords_Benchmark\work"
)

foreach ($dir in $dirsToRemove) {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
        Write-Host "Supprime: $dir"
    }
}

# Recreate required writable directories only.
foreach ($dir in @(
    (Join-Path $ProjectRoot "data"),
    (Join-Path $ProjectRoot "public\benchmark-audio"),
    (Join-Path $ProjectRoot "var")
)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
}

Write-Host ""
Write-Host "RESET_OK"
Write-Host "La base et les tables de notation seront recreees automatiquement au prochain acces."
