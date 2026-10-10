$ErrorActionPreference='Stop'
$python='H:\Python\pythoncore-3.14-64\python.exe'
if(-not (Test-Path $python)){ throw "Python introuvable: $python" }
& $python (Join-Path $PSScriptRoot 'grep_legacy_terminology_r2a_scoped.py')
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }
