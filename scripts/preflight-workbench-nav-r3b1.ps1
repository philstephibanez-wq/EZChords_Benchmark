$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== EZStudio_lab WORKBENCH NAV R3B1 PREFLIGHT ==="

& $Php .\tests\workbench_nav_r3b1_contract.php
if($LASTEXITCODE-ne 0){throw "Workbench navigation contract failed"}

$routes=(& $Php bin\console debug:router | Out-String)
foreach($route in @(
 "workbench_home","workbench_import","workbench_stems",
 "workbench_chords","workbench_lyrics","workbench_runs",
 "bench_view","lab_run"
)){
  if(-not $routes.Contains($route)){throw "Required route missing: $route"}
}

& $Php bin\console lint:twig .\templates\base.html.twig .\templates\workbench
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

Write-Host "EZSTUDIO_WORKBENCH_NAV_R3B1_ROUTES_OK"
Write-Host "EZSTUDIO_WORKBENCH_NAV_R3B1_PREFLIGHT_OK"
