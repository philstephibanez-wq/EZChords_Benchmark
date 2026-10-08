$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab CHORDS ORCHESTRATED DNA R3B5 PREFLIGHT ==="

& $Php .\tests\chords_orchestrated_dna_r3b5_contract.php
if($LASTEXITCODE-ne 0){throw "PHP contract failed"}

& $Python .\scripts\test-chords-orchestrated-dna-r3b5.py
if($LASTEXITCODE-ne 0){throw "Python contract failed"}

$routes=(& $Php bin\console debug:router | Out-String)
foreach($route in @(
 "lab_chords_experiment","lab_chords_experiment_create",
 "lab_internal_analysis_queue","lab_internal_analysis_claim",
 "lab_internal_analysis_progress","lab_internal_analysis_complete",
 "lab_internal_analysis_fail","bench_view","dna_run"
)){
 if(-not $routes.Contains($route)){throw "Required route missing: $route"}
}

& $Php bin\console lint:twig .\templates\lab\chords_experiment.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

Write-Host "EZSTUDIO_CHORDS_ORCHESTRATED_DNA_R3B5_ROUTES_OK"
Write-Host "EZSTUDIO_CHORDS_ORCHESTRATED_DNA_R3B5_PREFLIGHT_OK"
