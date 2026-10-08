$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== EZStudio_lab CHORDS UI R2C PREFLIGHT ==="

& $Php .\tests\chords_ui_r2c_contract.php
if($LASTEXITCODE-ne 0){throw "CHORDS UI contract failed"}

& $Php bin\console lint:twig .\templates\benchmark\view.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

Write-Host "EZSTUDIO_CHORDS_UI_R2C_TWIG_OK"
Write-Host "EZSTUDIO_CHORDS_UI_R2C_PREFLIGHT_OK"
