$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== EZStudio_lab DAG ADN R3B3A PREFLIGHT ==="

& $Php .\tests\dag_adn_r3b3_contract.php
if($LASTEXITCODE-ne 0){throw "DAG ADN contract failed"}

& $Php .\tests\dag_adn_r3b3_schema.php
if($LASTEXITCODE-ne 0){throw "DAG ADN schema verification failed"}

$routes=(& $Php bin\console debug:router | Out-String)
foreach($route in @("dna_song","dna_run","dna_run_json","dna_compare")){
  if(-not $routes.Contains($route)){throw "Required route missing: $route"}
}

& $Php bin\console lint:twig .\templates\dna
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

Write-Host "EZSTUDIO_DAG_ADN_R3B3_ROUTES_OK"
Write-Host "EZSTUDIO_DAG_ADN_R3B3_SCHEMA_CONTRACT_OK"
Write-Host "EZSTUDIO_DAG_ADN_R3B3A_PREFLIGHT_OK"
