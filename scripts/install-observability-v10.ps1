param(
    [switch]$SkipMongoInstall
)

$ErrorActionPreference = "Stop"

$Project = "H:\EZChords_Benchmark"
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

Write-Host "=== EZChords Benchmark V10 Observability setup ==="

if (-not (Test-Path $Python)) {
    throw "Python introuvable: $Python"
}

if (-not $SkipMongoInstall) {
    $mongod = Get-Command mongod.exe -ErrorAction SilentlyContinue

    if (-not $mongod) {
        Write-Host "MongoDB Server absent -> installation winget MongoDB.Server"
        winget install -e --id MongoDB.Server --accept-package-agreements --accept-source-agreements

        if ($LASTEXITCODE -ne 0) {
            throw "Echec installation MongoDB.Server via winget."
        }
    } else {
        Write-Host "MongoDB Server deja installe: $($mongod.Source)"
    }
}

$service = Get-Service -Name MongoDB -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -ne "Running") {
        Write-Host "Demarrage du service MongoDB..."
        Start-Service MongoDB
    }
    Write-Host "MongoDB service: $((Get-Service MongoDB).Status)"
} else {
    $mongod = Get-Command mongod.exe -ErrorAction SilentlyContinue
    if (-not $mongod) {
        $candidates = Get-ChildItem "C:\Program Files\MongoDB\Server" -Filter mongod.exe -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending
        if ($candidates) {
            $mongod = $candidates[0]
        }
    }

    if (-not $mongod) {
        throw "mongod.exe introuvable apres installation."
    }

    $dbPath = "H:\temp\EZChords_Benchmark\mongodb\data"
    $logPath = "H:\temp\EZChords_Benchmark\mongodb\mongod.log"
    New-Item -ItemType Directory -Force -Path $dbPath | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path $logPath) | Out-Null

    Write-Host "Pas de service MongoDB detecte. Demarrage local benchmark uniquement."
    Start-Process -FilePath $mongod.Source `
        -ArgumentList @(
            "--dbpath", $dbPath,
            "--logpath", $logPath,
            "--bind_ip", "127.0.0.1",
            "--port", "27017"
        ) `
        -WindowStyle Hidden

    Start-Sleep -Seconds 2
}

Write-Host "Installation dependances Python observability..."
& $Python -m pip install --upgrade pymongo matplotlib soundfile

if ($LASTEXITCODE -ne 0) {
    throw "Echec installation dependances Python."
}

Set-Location $Project

& $Python .\python\observability.py --self-test
if ($LASTEXITCODE -ne 0) {
    throw "Self-test observability en echec."
}

& $Python -c "from pymongo import MongoClient; c=MongoClient('mongodb://127.0.0.1:27017',serverSelectionTimeoutMS=3000); print(c.admin.command('ping')); c.close()"
if ($LASTEXITCODE -ne 0) {
    throw "MongoDB ne repond pas sur 127.0.0.1:27017."
}

Write-Host "V10_OBSERVABILITY_SETUP_OK"
