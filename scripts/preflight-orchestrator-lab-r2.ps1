$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php = "H:\PHP\php-8.5-x64\php.exe"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab ORCHESTRATOR LAB R2 PREFLIGHT ==="

& $Php .\tests\orchestrator_lab_r2_contract.php
if ($LASTEXITCODE -ne 0) { throw "PHP R2 contract failed" }

& $Python .\tests\test_orchestrator_lab_r2.py
if ($LASTEXITCODE -ne 0) { throw "Python R2 contract failed" }

$routes = (& $Php bin\console debug:router | Out-String)
foreach ($route in @(
    "lab_internal_analysis_queue",
    "lab_internal_analysis_claim",
    "lab_internal_analysis_progress",
    "lab_internal_analysis_complete",
    "lab_internal_analysis_fail"
)) {
    if (-not $routes.Contains($route)) {
        throw "LAB internal route missing: $route"
    }
}

$envFile = Join-Path $Root ".env.local"
if (-not (Test-Path -LiteralPath $envFile)) {
    throw ".env.local missing"
}
$envText = [System.IO.File]::ReadAllText($envFile)
if ($envText -notmatch "(?m)^EZSTUDIO_ANALYSIS_WORKER_TOKEN=.{32,}$") {
    throw "EZSTUDIO_ANALYSIS_WORKER_TOKEN missing/too short"
}

Write-Host "EZSTUDIO_ORCHESTRATOR_LAB_R2_TOKEN_OK"
Write-Host "EZSTUDIO_ORCHESTRATOR_LAB_R2_ROUTES_OK"
Write-Host "EZSTUDIO_ORCHESTRATOR_LAB_R2_PREFLIGHT_OK"
