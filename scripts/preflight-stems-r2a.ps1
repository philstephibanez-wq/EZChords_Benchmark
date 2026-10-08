$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
$Python="H:\Python\pythoncore-3.14-64\python.exe"
$Php="H:\PHP\php-8.5-x64\php.exe"
Set-Location $Root
if(-not(Test-Path "H:\EZS_orchestrator\runtime_guard\singleton.py")){throw "orchestrator guard absent"}
$env:PYTHONPATH="$Root\python"
$env:EZSTUDIO_ORCHESTRATOR_ROOT="H:\EZS_orchestrator"
$env:EZSTUDIO_RUNTIME_ROOT="H:\temp\EZStudio_lab"
$env:EZSTUDIO_PHP=$Php

& $Python -m py_compile .\python\ezstudio\jobs\orchestrator_guard.py .\python\ezstudio\jobs\stems_worker.py .\python\ezstudio\pipeline\stems\diagnostics.py .\scripts\migrate-stems-r2a.py
if($LASTEXITCODE-ne 0){throw "python compile failed"}
& $Python -m ezstudio.jobs.stems_worker --self-test
if($LASTEXITCODE-ne 0){throw "orchestrator guard self-test failed"}

foreach($file in @(".\src\Service\LabJobStore.php",".\src\Controller\StemsLabController.php",".\scripts\lab-job-store.php")){
  & $Php -l $file
  if($LASTEXITCODE-ne 0){throw "PHP lint failed: $file"}
}

$routes=(& $Php bin\console debug:router|Out-String)
foreach($route in @("lab_stems","lab_stems_run","lab_stems_job")){if(-not $routes.Contains($route)){throw "route missing: $route"}}
Write-Host "EZSTUDIO_STEMS_R2A_ROUTES_OK"

if(Test-Path .\src\Controller\InternalAnalysisController.php){throw "rejected R2 controller remains"}
if(Test-Path .\analysis\worker_entrypoint.py){throw "rejected R2 worker entrypoint remains"}
Write-Host "EZSTUDIO_REJECTED_ORCHESTRATOR_PATCH_CLEANED_OK"

powershell -ExecutionPolicy Bypass -File .\scripts\start-stems-worker.ps1
if($LASTEXITCODE-ne 0){throw "worker start failed"}
powershell -ExecutionPolicy Bypass -File .\scripts\status-stems-worker.ps1
if($LASTEXITCODE-ne 0){throw "worker status failed"}

Write-Host "EZSTUDIO_ORCHESTRATOR_REPO_UNTOUCHED_CONTRACT_OK"
Write-Host "EZSTUDIO_STEMS_R2A_PREFLIGHT_OK"
