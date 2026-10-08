$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php = "H:\PHP\php-8.5-x64\php.exe"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab ORCHESTRATOR LAB R2B HOTFIX ==="

& $Php -l .\tests\orchestrator_lab_r2_contract.php
if ($LASTEXITCODE -ne 0) { throw "PHP contract lint failed" }

& $Php .\tests\orchestrator_lab_r2_contract.php
if ($LASTEXITCODE -ne 0) { throw "PHP R2B contract failed" }

& $Python .\tests\test_orchestrator_lab_r2.py
if ($LASTEXITCODE -ne 0) { throw "Python R2 contract failed" }

& $Php bin\console cache:clear --env=dev
if ($LASTEXITCODE -ne 0) { throw "Symfony cache clear failed" }

Write-Host "EZSTUDIO_ORCHESTRATOR_LAB_R2B_HOTFIX_OK"
