$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== R3B5A DAG FUNCTIONAL PREPARE ==="

& $Php -l .\scripts\prepare-r3b5-dag-functional.php
if($LASTEXITCODE-ne 0){throw "Functional DAG PHP lint failed"}

if($args.Count -gt 0){
    & $Php .\scripts\prepare-r3b5-dag-functional.php --song-id=$($args[0])
}else{
    & $Php .\scripts\prepare-r3b5-dag-functional.php
}
if($LASTEXITCODE-ne 0){throw "Functional DAG prepare failed"}

Write-Host ""
Write-Host "Two chords_scientific jobs are now queued."
Write-Host "Let EZS_orchestrator LAB execute them."
