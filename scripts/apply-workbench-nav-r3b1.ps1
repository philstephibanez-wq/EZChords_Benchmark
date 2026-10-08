$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab WORKBENCH NAV R3B1 APPLY ==="

& $Python .\scripts\migrate-workbench-nav-r3b1.py
if($LASTEXITCODE-ne 0){throw "Base navigation migration failed"}

foreach($File in @(
 ".\src\Service\WorkbenchCatalog.php",
 ".\src\Controller\WorkbenchController.php",
 ".\src\EventSubscriber\WorkbenchHomeSubscriber.php",
 ".\tests\workbench_nav_r3b1_contract.php"
)){
  & $Php -l $File
  if($LASTEXITCODE-ne 0){throw "PHP lint failed: $File"}
}

& $Php .\tests\workbench_nav_r3b1_contract.php
if($LASTEXITCODE-ne 0){throw "Workbench navigation contract failed"}

& $Php bin\console lint:twig .\templates\base.html.twig .\templates\workbench
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Cache clear failed"}

Write-Host "EZSTUDIO_WORKBENCH_NAV_R3B1_APPLY_OK"
