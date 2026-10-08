$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== EZStudio_lab STEMS -> CHORDS DNA R3B4A HOTFIX PREFLIGHT ==="

& $Php .\tests\stems_chords_dna_r3b4_contract.php
if($LASTEXITCODE-ne 0){throw "R3B4 contract failed"}

& $Php .\tests\stems_chords_dna_r3b4_schema.php
if($LASTEXITCODE-ne 0){throw "R3B4 schema failed"}

$routes=(& $Php bin\console debug:router | Out-String)
foreach($route in @(
 "lab_stems","lab_stems_analyze","lab_stems_job",
 "lab_chords_experiment","lab_chords_experiment_create",
 "dna_run","dna_run_json","bench_view"
)){
 if(-not $routes.Contains($route)){throw "Required route missing: $route"}
}

& $Php bin\console lint:twig .\templates\lab .\templates\dna .\templates\base.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

Write-Host "EZSTUDIO_STEMS_CHORDS_DNA_R3B4_ROUTES_OK"
Write-Host "EZSTUDIO_STEMS_CHORDS_DNA_R3B4A_PREFLIGHT_OK"
