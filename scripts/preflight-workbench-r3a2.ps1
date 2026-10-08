$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab WORKBENCH R3A2 PREFLIGHT ==="

& $Python .\tests\workbench_r3a2_migration_test.py
if($LASTEXITCODE-ne 0){throw "R3A2 synthetic migration tests failed"}

& $Php .\tests\workbench_r3a_contract.php
if($LASTEXITCODE-ne 0){throw "Workbench R3A contract failed"}

& $Php bin\console lint:twig .\templates\lab\index.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

$routes=(& $Php bin\console debug:router | Out-String)
foreach($route in @("lab_index","lab_run","bench_view","bench_start")){
  if(-not $routes.Contains($route)){throw "Required route missing: $route"}
}

Write-Host "EZSTUDIO_WORKBENCH_R3A2_ROUTES_OK"
Write-Host "EZSTUDIO_WORKBENCH_R3A2_PREFLIGHT_OK"
