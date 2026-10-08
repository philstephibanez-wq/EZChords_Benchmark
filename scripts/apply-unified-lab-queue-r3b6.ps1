$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab UNIFIED LAB QUEUE R3B6 APPLY ==="

& $Python .\scripts\migrate-unified-lab-queue-r3b6.py
if($LASTEXITCODE-ne 0){throw "Database source migration failed"}

& $Php .\scripts\migrate-analysis-jobs-r3b6.php
if($LASTEXITCODE-ne 0){throw "analysis_jobs schema migration failed"}

foreach($File in @(
 ".\src\Service\Database.php",
 ".\src\Service\StemsDnaExecutionService.php",
 ".\src\Controller\StemsLabController.php",
 ".\src\Controller\AnalysisDesktopController.php",
 ".\tests\unified_lab_queue_r3b6_contract.php",
 ".\tests\unified_lab_queue_r3b6_schema.php"
)){
  & $Php -l $File
  if($LASTEXITCODE-ne 0){throw "PHP lint failed: $File"}
}

& $Python -m py_compile .\analysis\worker_entrypoint.py
if($LASTEXITCODE-ne 0){throw "Python compile failed"}

& $Php .\tests\unified_lab_queue_r3b6_contract.php
if($LASTEXITCODE-ne 0){throw "R3B6 PHP contract failed"}

& $Php .\tests\unified_lab_queue_r3b6_schema.php
if($LASTEXITCODE-ne 0){throw "R3B6 schema contract failed"}

& $Python .\scripts\test-unified-lab-queue-r3b6.py
if($LASTEXITCODE-ne 0){throw "R3B6 Python contract failed"}

& $Php bin\console lint:twig .\templates\lab\stems.html.twig .\templates\lab\stems_job.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Symfony cache clear failed"}

Write-Host "EZSTUDIO_UNIFIED_LAB_QUEUE_R3B6_APPLY_OK"
