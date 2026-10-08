$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab WORKBENCH R3A2 FULL APPLY ==="

& $Python .\tests\workbench_r3a2_migration_test.py
if($LASTEXITCODE-ne 0){throw "R3A2 synthetic migration tests failed"}

& $Python .\scripts\migrate-workbench-r3a2.py
if($LASTEXITCODE-ne 0){throw "R3A2 migration failed"}

foreach($File in @(
  ".\src\Service\Database.php",
  ".\src\Controller\LabController.php",
  ".\tests\workbench_r3a_contract.php"
)){
  & $Php -l $File
  if($LASTEXITCODE-ne 0){throw "PHP lint failed: $File"}
}

& $Php .\tests\workbench_r3a_contract.php
if($LASTEXITCODE-ne 0){throw "Workbench R3A contract failed"}

& $Php bin\console lint:twig .\templates\lab\index.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Symfony cache clear failed"}

Write-Host "EZSTUDIO_WORKBENCH_R3A2_APPLY_OK"
