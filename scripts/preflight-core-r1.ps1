$ErrorActionPreference = "Stop"
$Project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = "H:\Python\pythoncore-3.14-64\python.exe"
Write-Host "=== EZStudio_lab CORE R1 preflight ==="
if (-not (Test-Path $Python)) { throw "Python introuvable: $Python" }
$Required = @("python\ezstudio\__init__.py","python\ezstudio\core\contracts.py","python\ezstudio\core\hashing.py","python\ezstudio\core\paths.py","python\ezstudio\core\storage.py","python\ezstudio\core\registry.py","scripts\test-core-r1.py")
foreach ($Rel in $Required) { if (-not (Test-Path (Join-Path $Project $Rel))) { throw "Fichier CORE R1 absent: $Rel" } }
& $Python (Join-Path $Project "scripts\test-core-r1.py")
if ($LASTEXITCODE -ne 0) { throw "Echec test CORE R1" }
$CoreText = (Get-ChildItem (Join-Path $Project "python\ezstudio") -Recurse -Filter *.py | ForEach-Object { Get-Content $_.FullName -Raw }) -join "`n"
if ($CoreText -match [regex]::Escape("H:\EZScore")) { throw "Violation autonomie: reference H:\EZScore detectee dans le nouveau Core" }
Write-Host "EZSTUDIO_CORE_R1_PREFLIGHT_OK"
