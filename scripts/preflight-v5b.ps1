$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "=== EZChords Benchmark V5b preflight ==="

$required = @(
  "src\Controller\BenchmarkController.php",
  "src\Service\Database.php",
  "templates\base.html.twig",
  "templates\benchmark\view.html.twig",
  "templates\benchmark\report.html.twig",
  "public\js\benchmark-player.js",
  "python\engine.py",
  "scripts\start.ps1"
)
foreach ($rel in $required) {
  if (-not (Test-Path (Join-Path $root $rel))) { throw "V5B_MISSING: $rel" }
}

$c = Get-Content (Join-Path $root "src\Controller\BenchmarkController.php") -Raw
$d = Get-Content (Join-Path $root "src\Service\Database.php") -Raw
$b = Get-Content (Join-Path $root "templates\base.html.twig") -Raw
$v = Get-Content (Join-Path $root "templates\benchmark\view.html.twig") -Raw
$j = Get-Content (Join-Path $root "public\js\benchmark-player.js") -Raw
$e = Get-Content (Join-Path $root "python\engine.py") -Raw
$s = Get-Content (Join-Path $root "scripts\start.ps1") -Raw

if ($c -notmatch "bench_report") { throw "V5B_REPORT_ROUTE_MISSING" }
if ($d -notmatch "reportRows") { throw "V5B_REPORT_QUERY_MISSING" }
if ($b -notmatch "Bilan") { throw "V5B_NAV_BILAN_MISSING" }
if ($v -notmatch 'id="mp3-volume"') { throw "V5B_MP3_VOLUME_MISSING" }
if ($v -notmatch 'id="midi-volume"') { throw "V5B_MIDI_VOLUME_MISSING" }
if ($j -notmatch "timelines remises à zéro") { throw "V5B_STOP_RESET_MISSING" }
if ($e -notmatch "zero-overlap") { throw "V5B_SILENCE_FIX_MISSING" }
if ($s -notmatch '\-t \$public') { throw "V5B_PUBLIC_DOCROOT_MISSING" }

Write-Host "V5B_CONTRACT_OK"
Write-Host "V5B_PREFLIGHT_OK"
