$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== R3B5 DAG FUNCTIONAL CHECK ==="
& $Php .\scripts\check-r3b5-dag-functional.php
$rc=$LASTEXITCODE

if($rc -eq 10){
    Write-Host ""
    Write-Host "Jobs are not both finished yet. This is not a contract failure."
    exit 10
}
if($rc-ne 0){throw "Functional DAG check failed"}

Write-Host "EZSTUDIO_R3B5_DAG_FUNCTIONAL_PREFLIGHT_OK"
