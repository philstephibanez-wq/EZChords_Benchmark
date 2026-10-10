$ErrorActionPreference = 'Stop'
$python = 'H:\Python\pythoncore-3.14-64\python.exe'
if (-not (Test-Path $python)) {
    throw "Python introuvable: $python"
}
& $python (Join-Path $PSScriptRoot 'apply_terminology_preset_r1.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
