$ErrorActionPreference = "Stop"
$Project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab independent application + UI R1B ==="

if (-not (Test-Path $Python)) {
    throw "Python introuvable: $Python"
}

& $Python (Join-Path $Project "scripts\migrate-independent-ui-r1.py")
if ($LASTEXITCODE -ne 0) {
    throw "Migration source independante en erreur"
}

Set-Location $Project
composer dump-autoload
if ($LASTEXITCODE -ne 0) {
    throw "composer dump-autoload en erreur"
}

php bin\console cache:clear
if ($LASTEXITCODE -ne 0) {
    throw "cache:clear en erreur"
}

Write-Host "EZSTUDIO_INDEPENDENT_UI_R1B_APPLY_OK"
