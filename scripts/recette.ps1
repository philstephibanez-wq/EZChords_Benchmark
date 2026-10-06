$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$php = "H:\PHP\php-8.5-x64\php.exe"
$python = "H:\Python\pythoncore-3.14-64\python.exe"

if (-not (Test-Path $php)) { throw "PHP introuvable: $php" }
if (-not (Test-Path $python)) { throw "Python introuvable: $python" }

Write-Host "=== EZChords Benchmark recette V2c ==="

Write-Host ""
Write-Host "[1/7] Vérification config env"
$services = Get-Content .\config\services.yaml -Raw
if ($services -match '%env\(') {
    throw "CONFIG_ENV_BIND_KO: config/services.yaml contient encore %env(...)%"
}
if ($services -notmatch 'H:\\Python\\pythoncore-3\.14-64\\python\.exe') {
    throw "CONFIG_PYTHON_PATH_KO"
}
Write-Host "CONFIG_ENV_BIND_OK"

Write-Host ""
Write-Host "[2/7] PHP lint applicatif"
$phpFiles = @()
foreach ($file in @(
    (Join-Path $ProjectRoot "router.php"),
    (Join-Path $ProjectRoot "public\index.php"),
    (Join-Path $ProjectRoot "bin\console")
)) {
    if (Test-Path $file) { $phpFiles += Get-Item $file }
}
foreach ($dirName in @("src", "config")) {
    $dir = Join-Path $ProjectRoot $dirName
    if (Test-Path $dir) {
        $phpFiles += Get-ChildItem $dir -Recurse -File -Filter *.php
    }
}
$phpFiles = $phpFiles | Sort-Object FullName -Unique
foreach ($file in $phpFiles) {
    & $php -l $file.FullName
    if ($LASTEXITCODE -ne 0) { throw "PHP lint KO: $($file.FullName)" }
}
Write-Host "PHP_APP_LINT_OK ($($phpFiles.Count) fichiers)"

Write-Host ""
Write-Host "[3/7] Python compile"
$pythonFiles = Get-ChildItem .\python -Recurse -File -Filter *.py
foreach ($file in $pythonFiles) {
    & $python -m py_compile $file.FullName
    if ($LASTEXITCODE -ne 0) { throw "Python compile KO: $($file.FullName)" }
}
Write-Host "PYTHON_COMPILE_OK ($($pythonFiles.Count) fichiers)"

Write-Host ""
Write-Host "[4/7] Engine self-test"
& $python .\python\engine.py --self-test
if ($LASTEXITCODE -ne 0) { throw "ENGINE_SELF_TEST_KO" }

Write-Host ""
Write-Host "[5/7] Conteneur PROD"
& $php bin\console cache:clear --env=prod
if ($LASTEXITCODE -ne 0) { throw "PROD_CACHE_CLEAR_KO" }

& $php bin\console debug:container "App\Service\BenchmarkLauncher" --env=prod
if ($LASTEXITCODE -ne 0) { throw "PROD_BENCHMARK_LAUNCHER_CONTAINER_KO" }

Write-Host ""
Write-Host "[6/7] Conteneur DEV"
$devCache = Join-Path $ProjectRoot "var\cache\dev"
if (Test-Path $devCache) {
    Remove-Item -Recurse -Force $devCache
}

& $php bin\console cache:clear --env=dev
if ($LASTEXITCODE -ne 0) { throw "DEV_CACHE_CLEAR_KO" }

& $php bin\console debug:container "App\Service\BenchmarkLauncher" --env=dev
if ($LASTEXITCODE -ne 0) { throw "DEV_BENCHMARK_LAUNCHER_CONTAINER_KO" }

Write-Host ""
Write-Host "[7/7] Symfony smoke DEV"
& $php bin\console about --env=dev
if ($LASTEXITCODE -ne 0) { throw "SYMFONY_DEV_SMOKE_KO" }

Write-Host ""
Write-Host "RECETTE_OK"
