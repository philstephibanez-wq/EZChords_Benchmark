$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== EZStudio_lab DAG ADN R3B3A APPLY ==="

foreach($File in @(
 ".\src\Service\DnaRegistry.php",
 ".\src\Controller\DnaController.php",
 ".\scripts\migrate-dag-adn-r3b3.php",
 ".\tests\dag_adn_r3b3_contract.php",
 ".\tests\dag_adn_r3b3_schema.php"
)){
  & $Php -l $File
  if($LASTEXITCODE-ne 0){throw "PHP lint failed: $File"}
}

& $Php .\tests\dag_adn_r3b3_contract.php
if($LASTEXITCODE-ne 0){throw "DAG ADN contract failed"}

& $Php .\scripts\migrate-dag-adn-r3b3.php
if($LASTEXITCODE-ne 0){throw "DAG ADN schema migration failed"}

& $Php .\tests\dag_adn_r3b3_schema.php
if($LASTEXITCODE-ne 0){throw "DAG ADN schema verification failed"}

& $Php bin\console lint:twig .\templates\dna
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Cache clear failed"}

Write-Host "EZSTUDIO_DAG_ADN_R3B3A_APPLY_OK"
