$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== EZStudio_lab WORKBENCH R3A PREFLIGHT ==="

& $Php .\tests\workbench_r3a_contract.php
if($LASTEXITCODE-ne 0){throw "Workbench R3A contract failed"}

& $Php bin\console lint:twig .\templates\lab\index.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

$routes=(& $Php bin\console debug:router | Out-String)
foreach($route in @("lab_index","lab_run","bench_view","bench_start")){
  if(-not $routes.Contains($route)){throw "Required route missing: $route"}
}

Write-Host "EZSTUDIO_WORKBENCH_R3A_ROUTES_OK"
Write-Host "EZSTUDIO_WORKBENCH_R3A_PREFLIGHT_OK"
