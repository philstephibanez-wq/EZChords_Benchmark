$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab STEMS -> CHORDS DNA R3B4A HOTFIX APPLY ==="

& $Python .\scripts\migrate-stems-chords-dna-r3b4.py
if($LASTEXITCODE-ne 0){throw "Navigation migration failed"}

foreach($File in @(
 ".\src\Service\DnaRegistry.php",
 ".\src\Service\StemsDnaSync.php",
 ".\src\Service\ChordsExperimentService.php",
 ".\src\Service\LabJobStore.php",
 ".\src\Controller\DnaController.php",
 ".\src\Controller\StemsLabController.php",
 ".\src\Controller\ChordsExperimentController.php",
 ".\tests\stems_chords_dna_r3b4_contract.php",
 ".\tests\stems_chords_dna_r3b4_schema.php"
)){
  & $Php -l $File
  if($LASTEXITCODE-ne 0){throw "PHP lint failed: $File"}
}

& $Php .\tests\stems_chords_dna_r3b4_contract.php
if($LASTEXITCODE-ne 0){throw "R3B4 contract failed"}

& $Php .\tests\stems_chords_dna_r3b4_schema.php
if($LASTEXITCODE-ne 0){throw "R3B4 schema failed"}

& $Php bin\console lint:twig .\templates\lab .\templates\dna .\templates\base.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Cache clear failed"}

Write-Host "EZSTUDIO_STEMS_CHORDS_DNA_R3B4A_APPLY_OK"
