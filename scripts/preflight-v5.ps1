$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== EZChords Benchmark V5 preflight ==="

$files = @{
  controller = Join-Path $root "src\Controller\BenchmarkController.php"
  database   = Join-Path $root "src\Service\Database.php"
  base       = Join-Path $root "templates\base.html.twig"
  index      = Join-Path $root "templates\benchmark\index.html.twig"
  view       = Join-Path $root "templates\benchmark\view.html.twig"
  js         = Join-Path $root "public\js\benchmark-player.js"
}

foreach ($f in $files.Values) {
  if (-not (Test-Path $f)) { throw "V5_MISSING_FILE: $f" }
}

$c = Get-Content $files.controller -Raw
$d = Get-Content $files.database -Raw
$b = Get-Content $files.base -Raw
$i = Get-Content $files.index -Raw
$v = Get-Content $files.view -Raw
$j = Get-Content $files.js -Raw

if ($v -notmatch "Player V5") { throw "V5_TEMPLATE_MARKER_MISSING" }
if ($v -notmatch 'id="chord-display-level"') { throw "V5_DISPLAY_SELECTOR_MISSING" }
if ($v -notmatch 'name="approved\[\]"') { throw "V5_APPROVAL_CHECKBOX_MISSING" }
if ($i -notmatch "bench_delete") { throw "V5_TRASH_FORM_MISSING" }
if ($i -notmatch "🗑") { throw "V5_TRASH_ICON_MISSING" }
if ($d -notmatch "deleteSongByRunId") { throw "V5_DB_DELETE_MISSING" }
if ($d -notmatch "saveAlgorithmApprovals") { throw "V5_CHECKBOX_SAVE_MISSING" }
if ($b -notmatch "main-nav") { throw "V5_NAV_MISSING" }
if ($j -notmatch "refreshChordLabels") { throw "V5_REALTIME_DISPLAY_MISSING" }
if ($j -notmatch "primeSynth") { throw "V5_SYNTH_PRIME_MISSING" }
if ($c -match "StreamedResponse") { throw "V5_OLD_AUDIO_STREAM_ROUTE_PRESENT" }

Write-Host "V5_CONTRACT_OK"

$php = "H:\PHP\php-8.5-x64\php.exe"
if (-not (Test-Path $php)) { throw "PHP absent: $php" }

& $php -l $files.controller
if ($LASTEXITCODE -ne 0) { throw "V5_CONTROLLER_LINT_KO" }
& $php -l $files.database
if ($LASTEXITCODE -ne 0) { throw "V5_DATABASE_LINT_KO" }

$devCache = Join-Path $root "var\cache\dev"
if (Test-Path $devCache) { Remove-Item -Recurse -Force $devCache }

$env:APP_ENV = "dev"
$env:APP_DEBUG = "1"
& $php bin\console cache:clear --env=dev
if ($LASTEXITCODE -ne 0) { throw "V5_CACHE_CLEAR_KO" }

Write-Host "V5_CACHE_OK"
Write-Host "V5_PREFLIGHT_OK"
