$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== EZChords Benchmark V6b preflight ==="

$engine = Get-Content (Join-Path $root "python\engine.py") -Raw
$view = Get-Content (Join-Path $root "templates\benchmark\view.html.twig") -Raw
$controller = Get-Content (Join-Path $root "src\Controller\BenchmarkController.php") -Raw
$reset = Get-Content (Join-Path $root "scripts\reset-benchmark.ps1") -Raw

if ($engine -notmatch "harmonic_silence_mask") { throw "V6B_NO_CHORD_ENGINE_MISSING" }
if ($engine -notmatch "silent_beats=silent_beats") { throw "V6B_GRID_SILENCE_MISSING" }
if ($view -notmatch "No-chord") { throw "V6B_SILENCE_DIAGNOSTIC_MISSING" }
if ($controller -notmatch "silence_diagnostic") { throw "V6B_CONTROLLER_DIAGNOSTIC_MISSING" }
if ($reset -notmatch "public\\benchmark-audio") { throw "V6B_RESET_AUDIO_MISSING" }
if ($reset -notmatch "H:\\temp\\EZChords_Benchmark\\work") { throw "V6B_RESET_WORK_MISSING" }

Write-Host "V6B_SILENCE_DETECTION_OK"
Write-Host "V6B_SILENCE_DISPLAY_OK"
Write-Host "V6B_RESET_COMPLETE_OK"
Write-Host "V6B_PREFLIGHT_OK"
