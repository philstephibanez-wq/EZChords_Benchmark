$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== EZChords Benchmark V4g preflight ==="

$controller = Join-Path $root "src\Controller\BenchmarkController.php"
$view = Join-Path $root "templates\benchmark\view.html.twig"
$js = Join-Path $root "public\js\benchmark-player.js"

foreach ($f in @($controller,$view,$js)) {
    if (-not (Test-Path $f)) {
        throw "V4G_MISSING_FILE: $f"
    }
}

$c = Get-Content $controller -Raw
$v = Get-Content $view -Raw
$j = Get-Content $js -Raw

if ($v -notmatch "Player V4g") {
    throw "V4G_TEMPLATE_MARKER_MISSING"
}
if ($v -notmatch 'id="difficulty-level"') {
    throw "V4G_DIFFICULTY_SELECTOR_MISSING"
}
if ($c -notmatch "StreamedResponse") {
    throw "V4G_STREAMED_RESPONSE_MISSING"
}
if ($c -match "BinaryFileResponse") {
    throw "V4G_OLD_BINARY_FILE_RESPONSE_PRESENT"
}
if ($c -notmatch "Content-Range") {
    throw "V4G_RANGE_SUPPORT_MISSING"
}
if ($j -notmatch "fallback WebAudio actif") {
    throw "V4G_PLAYER_JS_MARKER_MISSING"
}

Write-Host "V4G_CRITICAL_FILES_OK"

$php = "H:\PHP\php-8.5-x64\php.exe"
if (-not (Test-Path $php)) { throw "PHP absent: $php" }

& $php -l $controller
if ($LASTEXITCODE -ne 0) { throw "V4G_CONTROLLER_LINT_KO" }

if (Test-Path (Join-Path $root "var\cache\dev")) {
    Remove-Item -Recurse -Force (Join-Path $root "var\cache\dev")
}
if (Test-Path (Join-Path $root "var\cache\prod")) {
    Remove-Item -Recurse -Force (Join-Path $root "var\cache\prod")
}

$env:APP_ENV = "dev"
$env:APP_DEBUG = "1"

& $php bin\console cache:clear --env=dev
if ($LASTEXITCODE -ne 0) { throw "V4G_DEV_CACHE_CLEAR_KO" }

Write-Host "V4G_CACHE_OK"
Write-Host "V4G_PREFLIGHT_OK"
