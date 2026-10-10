$ErrorActionPreference = 'Stop'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = 'H:\Python\pythoncore-3.14-64\python.exe'
if (-not (Test-Path $python)) {
    throw "Python introuvable: $python"
}

Write-Host '1/4 Migration SQLite...' -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot 'migrate_terminology_preset_r2a_db.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '2/4 Alignement code/UI...' -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot 'apply_terminology_preset_r2a.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '3/4 Contrat R2A...' -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot 'test_terminology_preset_r2a.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '4/4 Grep résiduel...' -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot 'grep_legacy_terminology_r2a.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'TERMINOLOGY_PRESET_R2A_APPLIED' -ForegroundColor Green
