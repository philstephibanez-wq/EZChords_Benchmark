Remove-Item -Path (Join-Path $PSScriptRoot "..\var\tmp\*") -Recurse -Force -ErrorAction SilentlyContinue
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
$env:EZSTUDIO_PYTHON = $python
$env:AI_MODELS_ROOT = "H:\AIModels"
$env:BS_ROFORMER_MODELS_PATH = "H:\AIModels\audio\separation\bs-roformer"
$env:MELBAND_ROFORMER_MODELS_PATH = "H:\AIModels\audio\separation\melband-roformer"
$env:EZSTUDIO_PROFILE_MODELS = "H:\AIModels\audio\profile"
$env:EZSTUDIO_BEAT_THIS_CHECKPOINT = "H:\AIModels\audio\rhythm\beat-this\beat_this-final0.ckpt"
$storageRoot = Join-Path $root "var\storage"
$runtimeRoot = Join-Path $root "var\runtime"
$tmpRoot = Join-Path $root "var\tmp"
$logsRoot = Join-Path $root "var\logs"

New-Item -ItemType Directory -Force -Path `
  $storageRoot, `
  $runtimeRoot, `
  $tmpRoot, `
  $logsRoot | Out-Null

$env:EZSTUDIO_STORAGE_ROOT = $storageRoot
$env:EZSTUDIO_TMP_ROOT = $tmpRoot
$env:EZSTUDIO_LOG_ROOT = $logsRoot

# Legacy compatibility only: durable outputs now resolve under STORAGE_ROOT.
$env:EZSTUDIO_RUNTIME_ROOT = $storageRoot

$env:EZSTUDIO_DEP_ROOT = Join-Path $runtimeRoot "deps"
$env:EZSTUDIO_PROFILE_DEP_ROOT = Join-Path $runtimeRoot "deps\profile-r3b12"
$env:EZSTUDIO_PROFILE_R3B13_DEP_ROOT = Join-Path $runtimeRoot "deps\profile-r3b13"
$env:EZSTUDIO_PROFILE_R3B10_DEP_ROOT = Join-Path $runtimeRoot "deps\profile-r3b10"
$env:EZSTUDIO_PASST_PYTHON = Join-Path $runtimeRoot "venvs\passt-r3b12\Scripts\python.exe"
$env:EZSTUDIO_PASST_TORCH_HOME = Join-Path $runtimeRoot "cache\passt-torch-home"
$env:PANNS_LABELS_CSV = Join-Path $runtimeRoot "deps\panns-data\class_labels_indices.csv"
$env:EZSTUDIO_TORCH_HOME = Join-Path $runtimeRoot "cache\torch-home"
$env:EZSTUDIO_STEMS_CACHE_ROOT = Join-Path $storageRoot "stems"
$env:EZSTUDIO_OBSERVABILITY_ROOT = Join-Path $tmpRoot "observability"
$env:EZSTUDIO_EXPORT_ROOT = Join-Path $storageRoot "exports"
$env:EZSTUDIO_JOB_ROOT = Join-Path $tmpRoot "jobs"
$env:KEEP_UPLOADS = "1"

Write-Host "EZStudio_lab"
Write-Host "MODELS=$env:AI_MODELS_ROOT"
Write-Host "PROFILE_DEPS=$env:EZSTUDIO_PROFILE_DEP_ROOT"
Write-Host "STORAGE=$env:EZSTUDIO_STORAGE_ROOT"
Write-Host "TMP=$env:EZSTUDIO_TMP_ROOT"
Write-Host "LOGS=$env:EZSTUDIO_LOG_ROOT"
Write-Host "RUNTIME_DEPS=$env:EZSTUDIO_DEP_ROOT"
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
