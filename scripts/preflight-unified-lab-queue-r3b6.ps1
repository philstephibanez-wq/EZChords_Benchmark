$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab UNIFIED LAB QUEUE R3B6 PREFLIGHT ==="

& $Php .\tests\unified_lab_queue_r3b6_contract.php
if($LASTEXITCODE-ne 0){throw "R3B6 PHP contract failed"}

& $Php .\tests\unified_lab_queue_r3b6_schema.php
if($LASTEXITCODE-ne 0){throw "R3B6 schema contract failed"}

& $Python .\scripts\test-unified-lab-queue-r3b6.py
if($LASTEXITCODE-ne 0){throw "R3B6 Python contract failed"}

$routes=(& $Php bin\console debug:router | Out-String)
foreach($route in @(
 "lab_stems",
 "lab_stems_analyze",
 "lab_stems_job",
 "lab_internal_analysis_queue",
 "lab_internal_analysis_claim",
 "lab_internal_analysis_progress",
 "lab_internal_analysis_complete",
 "lab_internal_analysis_fail"
)){
 if(-not $routes.Contains($route)){throw "Required route missing: $route"}
}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Symfony cache clear failed"}

Write-Host "EZSTUDIO_UNIFIED_LAB_QUEUE_R3B6_ROUTES_OK"
Write-Host "EZSTUDIO_UNIFIED_LAB_QUEUE_R3B6_PREFLIGHT_OK"
