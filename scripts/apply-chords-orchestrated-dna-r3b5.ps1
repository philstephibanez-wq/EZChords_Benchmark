$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Php="H:\PHP\php-8.5-x64\php.exe"
$Python="H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZStudio_lab CHORDS ORCHESTRATED DNA R3B5 APPLY ==="

foreach($File in @(
 ".\src\Service\Database.php",
 ".\src\Service\ChordsDnaExecutionService.php",
 ".\src\Controller\AnalysisDesktopController.php",
 ".\src\Controller\ChordsExperimentController.php",
 ".\tests\chords_orchestrated_dna_r3b5_contract.php"
)){
  & $Php -l $File
  if($LASTEXITCODE-ne 0){throw "PHP lint failed: $File"}
}

& $Python -m py_compile .\analysis\worker_entrypoint.py .\python\worker.py .\python\engine.py
if($LASTEXITCODE-ne 0){throw "Python compile failed"}

& $Php .\tests\chords_orchestrated_dna_r3b5_contract.php
if($LASTEXITCODE-ne 0){throw "PHP contract failed"}

& $Python .\scripts\test-chords-orchestrated-dna-r3b5.py
if($LASTEXITCODE-ne 0){throw "Python contract failed"}

& $Php bin\console lint:twig .\templates\lab\chords_experiment.html.twig
if($LASTEXITCODE-ne 0){throw "Twig lint failed"}

& $Php bin\console cache:clear --env=dev
if($LASTEXITCODE-ne 0){throw "Cache clear failed"}

Write-Host "EZSTUDIO_CHORDS_ORCHESTRATED_DNA_R3B5_APPLY_OK"
