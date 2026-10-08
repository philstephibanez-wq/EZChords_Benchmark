$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
$Python="H:\Python\pythoncore-3.14-64\python.exe"
$Php="H:\PHP\php-8.5-x64\php.exe"
Set-Location $Root
& $Python .\scripts\migrate-stems-r2a.py
if($LASTEXITCODE-ne 0){throw "migration failed"}
composer dump-autoload
if($LASTEXITCODE-ne 0){throw "composer failed"}
& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "cache clear failed"}
Write-Host "EZSTUDIO_STEMS_R2A_APPLY_OK"
