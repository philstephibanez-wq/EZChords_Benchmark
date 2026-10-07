$ErrorActionPreference = "Stop"

$Project = "H:\EZChords_Benchmark"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

Set-Location $Project

Write-Host "=== EZChords Benchmark V10 preflight ==="

if (-not (Test-Path ".\python\observability.py")) {
    throw "python\observability.py absent"
}

if (-not (Test-Path ".\python\worker.py")) {
    throw "python\worker.py absent"
}

$engine = Get-Content ".\python\engine.py" -Raw
$worker = Get-Content ".\python\worker.py" -Raw
$obs = Get-Content ".\python\observability.py" -Raw

if ($engine -notmatch 'ENGINE_VERSION = "r9-positive-harmonic-support"') {
    throw "Baseline engine V9 inattendue."
}

$requiredAlgorithms = @(
    "Beat This downbeat",
    "Percussive onset",
    "Bass CQT",
    "Rhythm + Bass",
    "Harmonic novelty",
    "R41-like fusion"
)

foreach ($name in $requiredAlgorithms) {
    if ($engine -notmatch [regex]::Escape($name)) {
        throw "Methode metrique manquante: $name"
    }
}

if ($worker -notmatch "build_observability_bundle") {
    throw "Worker non instrumente V10."
}

if ($obs -notmatch "mongodb://127.0.0.1:27017") {
    throw "MongoDB V10 doit rester localhost."
}

if ($obs -match 'H:\\EZScore') {
    throw "Interdit: observability ne doit contenir aucun chemin d'ecriture EZScore."
}

& $Python .\python\engine.py --self-test
if ($LASTEXITCODE -ne 0) {
    throw "Engine self-test en echec."
}

& $Python .\python\observability.py --self-test
if ($LASTEXITCODE -ne 0) {
    throw "Observability self-test en echec."
}

& $Python -c "from pymongo import MongoClient; c=MongoClient('mongodb://127.0.0.1:27017',serverSelectionTimeoutMS=3000); print(c.admin.command('ping')); c.close()"
if ($LASTEXITCODE -ne 0) {
    throw "MongoDB indisponible."
}

Write-Host "V10_ENGINE_R9_UNTOUCHED_CONTRACT_OK"
Write-Host "V10_SIX_METRIC_METHODS_PRESENT_OK"
Write-Host "V10_MONGO_LOCALHOST_OK"
Write-Host "V10_EZSCORE_READ_ONLY_OK"
Write-Host "V10_AUTOMATIC_SCIENTIFIC_EXPORT_OK"
Write-Host "V10_PREFLIGHT_OK"
