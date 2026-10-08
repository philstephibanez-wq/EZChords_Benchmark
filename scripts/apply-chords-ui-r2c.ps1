$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab CHORDS UI R2C APPLY ==="

& $Python .\scripts\migrate-chords-ui-r2c.py
if($LASTEXITCODE-ne 0){throw "R2C migration failed"}

& $Python -m py_compile .\scripts\migrate-chords-ui-r2c.py
if($LASTEXITCODE-ne 0){throw "Python compile failed"}

& $Php -l .\tests\chords_ui_r2c_contract.php
if($LASTEXITCODE-ne 0){throw "PHP test lint failed"}

& $Php .\tests\chords_ui_r2c_contract.php
if($LASTEXITCODE-ne 0){throw "CHORDS UI contract failed"}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Symfony cache clear failed"}

Write-Host "EZSTUDIO_CHORDS_UI_R2C_APPLY_OK"
