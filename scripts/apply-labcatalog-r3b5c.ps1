$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Php="H:\PHP\php-8.5-x64\php.exe"

Write-Host "=== EZStudio_lab LABCATALOG R3B5D HOTFIX APPLY ==="

& $Php -l .\src\Service\LabCatalog.php
if($LASTEXITCODE-ne 0){throw "LabCatalog PHP lint failed"}

& $Php .\tests\labcatalog_r3b5c_contract.php
if($LASTEXITCODE-ne 0){throw "LabCatalog contract failed"}

& $Php -r "require 'vendor/autoload.php'; if (!class_exists('App\\Service\\LabCatalog')) { fwrite(STDERR, 'LabCatalog class not autoloadable'.PHP_EOL); exit(1); } echo 'EZSTUDIO_LABCATALOG_R3B5D_CLASS_OK'.PHP_EOL;"
if($LASTEXITCODE-ne 0){throw "LabCatalog class autoload failed"}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Symfony cache clear failed"}

$routes = (& $Php bin\console debug:router | Out-String)
if($LASTEXITCODE-ne 0){throw "debug:router failed"}
foreach($route in @("lab_stems","lab_chords_experiment","lab_chords_experiment_create")){
    if(-not $routes.Contains($route)){throw "Required route missing: $route"}
}

Write-Host "EZSTUDIO_LABCATALOG_R3B5D_ROUTES_OK"
Write-Host "EZSTUDIO_LABCATALOG_R3B5D_APPLY_OK"
