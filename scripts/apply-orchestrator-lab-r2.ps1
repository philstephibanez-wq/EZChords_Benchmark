$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php = "H:\PHP\php-8.5-x64\php.exe"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab ORCHESTRATOR LAB R2 APPLY ==="

& $Python .\scripts\migrate-orchestrator-lab-r2.py
if ($LASTEXITCODE -ne 0) { throw "R2 migration failed" }

powershell -ExecutionPolicy Bypass -File .\scripts\install-lab-analysis-token.ps1
if ($LASTEXITCODE -ne 0) { throw "LAB token installation failed" }

foreach ($File in @(
    ".\src\Controller\AnalysisDesktopController.php",
    ".\src\Service\LabAnalysisTokenGuard.php",
    ".\src\Service\Database.php",
    ".\src\Service\BenchmarkLauncher.php",
    ".\tests\orchestrator_lab_r2_contract.php"
)) {
    & $Php -l $File
    if ($LASTEXITCODE -ne 0) { throw "PHP lint failed: $File" }
}

& $Python -m py_compile `
    .\analysis\worker_entrypoint.py `
    .\python\worker.py `
    .\tests\test_orchestrator_lab_r2.py
if ($LASTEXITCODE -ne 0) { throw "Python compile failed" }

& $Php .\tests\orchestrator_lab_r2_contract.php
if ($LASTEXITCODE -ne 0) { throw "PHP R2 contract failed" }

& $Python .\tests\test_orchestrator_lab_r2.py
if ($LASTEXITCODE -ne 0) { throw "Python R2 contract failed" }

& $Php bin\console cache:clear --env=dev
if ($LASTEXITCODE -ne 0) { throw "Symfony cache clear failed" }

Write-Host "EZSTUDIO_ORCHESTRATOR_LAB_R2_APPLY_OK"
