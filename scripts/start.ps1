$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$php = "H:\PHP\php-8.5-x64\php.exe"
$python = "H:\Python\pythoncore-3.14-64\python.exe"
$public = Join-Path $root "public"
$router = Join-Path $root "router.php"

if (-not (Test-Path $php)) { throw "PHP absent: $php" }
if (-not (Test-Path $python)) { throw "Python absent: $python" }
if (-not (Test-Path $public)) { throw "PUBLIC_DIR_MISSING: $public" }
if (-not (Test-Path $router)) { throw "ROUTER_MISSING: $router" }

$env:APP_ENV = "dev"
$env:APP_DEBUG = "1"
$env:BENCH_PYTHON = $python
$env:BENCH_DEP_ROOT = "H:\temp\EZChords_Benchmark\deps"
$env:KEEP_UPLOADS = "1"

Write-Host "APP_ENV=$env:APP_ENV"
Write-Host "APP_DEBUG=$env:APP_DEBUG"
Write-Host "BENCH_PYTHON=$env:BENCH_PYTHON"
Write-Host "BENCH_DEP_ROOT=$env:BENCH_DEP_ROOT"
Write-Host "KEEP_UPLOADS=$env:KEEP_UPLOADS"
Write-Host "DOCROOT=$public"

$devCache = Join-Path $root "var\cache\dev"
if (Test-Path $devCache) {
    Remove-Item -Recurse -Force $devCache
}

& $php bin\console cache:clear --env=dev
if ($LASTEXITCODE -ne 0) {
    throw "DEV_CACHE_CLEAR_KO"
}

& $php `
  -d upload_max_filesize=1G `
  -d post_max_size=1100M `
  -d max_execution_time=0 `
  -S 127.0.0.1:8701 `
  -t $public `
  $router
