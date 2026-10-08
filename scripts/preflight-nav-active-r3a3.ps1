$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab NAV ACTIVE R3A3 PREFLIGHT ==="

& $Python .\tests\nav_active_r3a3_test.py
if($LASTEXITCODE-ne 0){throw "Synthetic nav test failed"}

& $Php .\tests\nav_active_r3a3_contract.php
if($LASTEXITCODE-ne 0){throw "Nav contract failed"}

& $Php bin\console lint:twig .\templates\base.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

Write-Host "EZSTUDIO_NAV_ACTIVE_R3A3_PREFLIGHT_OK"
