$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== EZChords Benchmark V5a static preflight ==="

$start = Join-Path $root "scripts\start.ps1"
$js = Join-Path $root "public\js\benchmark-player.js"
$public = Join-Path $root "public"
$router = Join-Path $root "router.php"

foreach ($f in @($start,$js,$public,$router)) {
    if (-not (Test-Path $f)) {
        throw "V5A_MISSING: $f"
    }
}

$s = Get-Content $start -Raw

if ($s -notmatch '\-t \$public') {
    throw "V5A_PUBLIC_DOCROOT_NOT_CONFIGURED"
}

if ($s -match 'KEEP_UPLOADS\s*=\s*"0"') {
    throw "V5A_KEEP_UPLOADS_WRONG"
}

Write-Host "V5A_PUBLIC_DOCROOT_OK"
Write-Host "V5A_PLAYER_JS_PRESENT"
Write-Host "V5A_KEEP_UPLOADS_OK"
Write-Host "V5A_PREFLIGHT_OK"
