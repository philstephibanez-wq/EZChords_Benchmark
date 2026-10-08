$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab WORKBENCH R3A1 HOTFIX APPLY ==="

& $Python .\tests\workbench_r3a1_migration_contract.py
if($LASTEXITCODE-ne 0){throw "R3A1 migration contract failed"}

& $Python .\scripts\migrate-workbench-r3a.py
if($LASTEXITCODE-ne 0){throw "R3A1 migration failed"}

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

Write-Host "EZSTUDIO_WORKBENCH_R3A1_APPLY_OK"
